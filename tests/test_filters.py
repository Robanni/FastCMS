import pytest
from fastapi.testclient import TestClient

from fastcms.filter import Filter
from fastcms.service import CrudService
from tests.conftest import Article


# --- Filter unit tests ---


class ArticleFilter(Filter):
    published: bool | None = None
    author_id: int | None = None


@pytest.fixture
def service(get_session_factory) -> CrudService[Article]:
    return CrudService(Article, get_session_factory)


def test_filter_no_fields(service: CrudService[Article], session):
    """Empty filter = no WHERE clauses = all rows returned."""
    service.create(session, {"title": "A", "published": True, "author_id": 1})
    service.create(session, {"title": "B", "published": False, "author_id": 2})

    f = ArticleFilter()
    items = service.get_list(session, filters=f)
    assert len(items) == 2


def test_filter_by_published(service: CrudService[Article], session):
    service.create(session, {"title": "A", "published": True, "author_id": 1})
    service.create(session, {"title": "B", "published": False, "author_id": 2})
    service.create(session, {"title": "C", "published": True, "author_id": 3})

    f = ArticleFilter(published=True)
    items = service.get_list(session, filters=f)
    assert len(items) == 2
    assert all(i.published is True for i in items)


def test_filter_by_author_id(service: CrudService[Article], session):
    service.create(session, {"title": "A", "published": True, "author_id": 1})
    service.create(session, {"title": "B", "published": True, "author_id": 2})
    service.create(session, {"title": "C", "published": False, "author_id": 1})

    f = ArticleFilter(author_id=1)
    items = service.get_list(session, filters=f)
    assert len(items) == 2
    assert all(i.author_id == 1 for i in items)


def test_filter_combined(service: CrudService[Article], session):
    service.create(session, {"title": "A", "published": True, "author_id": 1})
    service.create(session, {"title": "B", "published": False, "author_id": 1})
    service.create(session, {"title": "C", "published": True, "author_id": 2})

    f = ArticleFilter(published=True, author_id=1)
    items = service.get_list(session, filters=f)
    assert len(items) == 1
    assert items[0].title == "A"


def test_filter_no_matches(service: CrudService[Article], session):
    service.create(session, {"title": "A", "published": True, "author_id": 1})

    f = ArticleFilter(author_id=99)
    items = service.get_list(session, filters=f)
    assert items == []


def test_filter_unknown_field_ignored():
    """Extra fields with extra='ignore' don't raise."""
    f = ArticleFilter.model_validate({"published": True, "nonexistent": "x"})
    assert f.published is True


# --- Router integration tests ---


@pytest.fixture
def client(app_with_filter):
    return TestClient(app_with_filter)


def test_list_no_filter(client: TestClient):
    client.post("/articles/", json={"title": "A", "published": True, "author_id": 1})
    client.post("/articles/", json={"title": "B", "published": False, "author_id": 2})
    response = client.get("/articles/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_filter_published(client: TestClient):
    client.post("/articles/", json={"title": "A", "published": True, "author_id": 1})
    client.post("/articles/", json={"title": "B", "published": False, "author_id": 2})
    client.post("/articles/", json={"title": "C", "published": True, "author_id": 3})

    response = client.get("/articles/?published=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["published"] is True for item in data)


def test_list_filter_author_id(client: TestClient):
    client.post("/articles/", json={"title": "A", "published": True, "author_id": 1})
    client.post("/articles/", json={"title": "B", "published": True, "author_id": 2})
    client.post("/articles/", json={"title": "C", "published": False, "author_id": 1})

    response = client.get("/articles/?author_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["author_id"] == 1 for item in data)


def test_list_filter_combined(client: TestClient):
    client.post("/articles/", json={"title": "A", "published": True, "author_id": 1})
    client.post("/articles/", json={"title": "B", "published": False, "author_id": 1})
    client.post("/articles/", json={"title": "C", "published": True, "author_id": 2})

    response = client.get("/articles/?published=true&author_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "A"


def test_list_filter_no_matches(client: TestClient):
    client.post("/articles/", json={"title": "A", "published": True, "author_id": 1})

    response = client.get("/articles/?author_id=99")
    assert response.status_code == 200
    assert response.json() == []
