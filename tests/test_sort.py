import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms import Resource, setup
from fastcms.service import CrudService
from tests.conftest import Article


@pytest.fixture
def service(get_session_factory) -> CrudService[Article]:
    return CrudService(Article, get_session_factory)


@pytest.fixture
def app_with_sort(engine):
    class ArticleResource(Resource):
        model = Article
        sort_fields = ["title", "author_id"]

    def get_session() -> Session:
        return Session(engine)

    application = FastAPI()
    setup(application, resources=[ArticleResource], get_session=get_session)
    return application


# --- service-level unit tests ---


def test_sort_asc(service: CrudService[Article], session):
    service.create(session, {"title": "C", "published": True, "author_id": 1})
    service.create(session, {"title": "A", "published": True, "author_id": 2})
    service.create(session, {"title": "B", "published": True, "author_id": 3})

    items = service.get_list(session, sort=[("title", False)])
    assert [i.title for i in items] == ["A", "B", "C"]


def test_sort_desc(service: CrudService[Article], session):
    service.create(session, {"title": "C", "published": True, "author_id": 1})
    service.create(session, {"title": "A", "published": True, "author_id": 2})
    service.create(session, {"title": "B", "published": True, "author_id": 3})

    items = service.get_list(session, sort=[("title", True)])
    assert [i.title for i in items] == ["C", "B", "A"]


def test_sort_multi(service: CrudService[Article], session):
    service.create(session, {"title": "B", "published": True, "author_id": 2})
    service.create(session, {"title": "A", "published": True, "author_id": 2})
    service.create(session, {"title": "A", "published": True, "author_id": 1})

    items = service.get_list(session, sort=[("title", False), ("author_id", False)])
    assert [(i.title, i.author_id) for i in items] == [("A", 1), ("A", 2), ("B", 2)]


def test_sort_none(service: CrudService[Article], session):
    service.create(session, {"title": "B", "published": True, "author_id": 1})
    service.create(session, {"title": "A", "published": True, "author_id": 2})

    items = service.get_list(session, sort=None)
    assert len(items) == 2


# --- HTTP-level tests ---


def test_sort_query_asc(app_with_sort, engine):
    with Session(engine) as s:
        s.add_all([
            Article(title="C", published=True, author_id=1),
            Article(title="A", published=True, author_id=2),
            Article(title="B", published=True, author_id=3),
        ])
        s.commit()

    client = TestClient(app_with_sort)
    resp = client.get("/articles/?sort=title")
    assert resp.status_code == 200
    assert [i["title"] for i in resp.json()] == ["A", "B", "C"]


def test_sort_query_desc(app_with_sort, engine):
    with Session(engine) as s:
        s.add_all([
            Article(title="C", published=True, author_id=1),
            Article(title="A", published=True, author_id=2),
            Article(title="B", published=True, author_id=3),
        ])
        s.commit()

    client = TestClient(app_with_sort)
    resp = client.get("/articles/?sort=-title")
    assert resp.status_code == 200
    assert [i["title"] for i in resp.json()] == ["C", "B", "A"]


def test_sort_disallowed_field(app_with_sort, engine):
    client = TestClient(app_with_sort)
    resp = client.get("/articles/?sort=published")
    assert resp.status_code == 400
    assert "published" in resp.json()["detail"]


def test_sort_absent_no_error(app_with_sort, engine):
    client = TestClient(app_with_sort)
    resp = client.get("/articles/")
    assert resp.status_code == 200


def test_no_sort_fields_ignores_param(engine):
    class ArticleResource(Resource):
        model = Article

    def get_session() -> Session:
        return Session(engine)

    application = FastAPI()
    setup(application, resources=[ArticleResource], get_session=get_session)

    client = TestClient(application)
    resp = client.get("/articles/?sort=title")
    assert resp.status_code == 200
