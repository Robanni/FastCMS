import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms.filter import Filter
from fastcms.service import CrudService
from tests.conftest import Article


# --- Filter subclasses for tests ---


class ArticleFilterLookups(Filter):
    author_id__gte: int | None = None
    author_id__lte: int | None = None
    author_id__gt: int | None = None
    author_id__lt: int | None = None
    author_id__ne: int | None = None
    author_id__in: list[int] | None = None
    title__contains: str | None = None
    title__startswith: str | None = None
    title__endswith: str | None = None
    author_id__isnull: bool | None = None


@pytest.fixture
def service(get_session_factory) -> CrudService[Article]:
    return CrudService(Article, get_session_factory)


@pytest.fixture
def articles(service, session):
    service.create(session, {"title": "Alpha", "published": True, "author_id": 1})
    service.create(session, {"title": "Beta",  "published": True, "author_id": 2})
    service.create(session, {"title": "Gamma", "published": False, "author_id": 3})
    service.create(session, {"title": "Delta", "published": False, "author_id": None})


# --- Numeric comparisons ---


def test_gte(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__gte=2))
    assert {i.author_id for i in items} == {2, 3}


def test_lte(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__lte=2))
    assert {i.author_id for i in items} == {1, 2}


def test_gt(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__gt=2))
    assert {i.author_id for i in items} == {3}


def test_lt(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__lt=2))
    assert {i.author_id for i in items} == {1}


def test_ne(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__ne=1))
    ids = {i.author_id for i in items}
    assert 1 not in ids
    assert 2 in ids and 3 in ids


def test_in(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__in=[1, 3]))
    assert {i.author_id for i in items} == {1, 3}


# --- String lookups ---


def test_contains(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(title__contains="pha"))
    assert len(items) == 1
    assert items[0].title == "Alpha"


def test_startswith(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(title__startswith="B"))
    assert len(items) == 1
    assert items[0].title == "Beta"


def test_endswith(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(title__endswith="ta"))
    assert {i.title for i in items} == {"Beta", "Delta"}


# --- NULL checks ---


def test_isnull_true(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__isnull=True))
    assert len(items) == 1
    assert items[0].author_id is None


def test_isnull_false(service, session, articles):
    items = service.get_list(session, filters=ArticleFilterLookups(author_id__isnull=False))
    assert all(i.author_id is not None for i in items)
    assert len(items) == 3


# --- Unknown lookup raises ---


def test_unknown_lookup_raises():
    with pytest.raises(TypeError, match="unknown filter lookup"):

        class BadFilter(Filter):
            author_id__bogus: int | None = None


# --- Combination ---


def test_combined_gte_and_contains(service, session, articles):
    # author_id >= 2 → Beta(2), Gamma(3); title contains "mm" → only Gamma
    items = service.get_list(
        session,
        filters=ArticleFilterLookups(author_id__gte=2, title__contains="mm"),
    )
    assert {i.title for i in items} == {"Gamma"}


# --- HTTP integration ---


@pytest.fixture
def app_lookups(engine):
    from fastapi import FastAPI
    from fastcms import Filter, Resource, setup

    class ArticleFilter(Filter):
        author_id__gte: int | None = None
        author_id__lte: int | None = None
        title__contains: str | None = None
        author_id__in: list[int] | None = None

    class ArticleResource(Resource):
        model = Article
        filter_class = ArticleFilter

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ArticleResource], get_session=get_session)
    return app


@pytest.fixture
def client_lookups(app_lookups):
    return TestClient(app_lookups)


def _seed(client):
    client.post("/articles/", json={"title": "Alpha", "published": True,  "author_id": 1})
    client.post("/articles/", json={"title": "Beta",  "published": True,  "author_id": 2})
    client.post("/articles/", json={"title": "Gamma", "published": False, "author_id": 3})


def test_http_gte(client_lookups):
    _seed(client_lookups)
    r = client_lookups.get("/articles/?author_id__gte=2")
    assert r.status_code == 200
    assert {i["author_id"] for i in r.json()} == {2, 3}


def test_http_lte(client_lookups):
    _seed(client_lookups)
    r = client_lookups.get("/articles/?author_id__lte=2")
    assert r.status_code == 200
    assert {i["author_id"] for i in r.json()} == {1, 2}


def test_http_contains(client_lookups):
    _seed(client_lookups)
    r = client_lookups.get("/articles/?title__contains=pha")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Alpha"


def test_http_in(client_lookups):
    _seed(client_lookups)
    r = client_lookups.get("/articles/?author_id__in=1&author_id__in=3")
    assert r.status_code == 200
    assert {i["author_id"] for i in r.json()} == {1, 3}


def test_http_combined(client_lookups):
    _seed(client_lookups)
    # author_id >= 2 → Beta(2), Gamma(3); title contains "mm" → only Gamma
    r = client_lookups.get("/articles/?author_id__gte=2&title__contains=mm")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Gamma"
