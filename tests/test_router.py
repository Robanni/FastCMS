import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms.resource import Action


@pytest.fixture
def client(app):
    return TestClient(app)


def test_get_list_empty(client: TestClient):
    response = client.get("/articles/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item(client: TestClient):
    response = client.post("/articles/", json={"title": "Test"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert "id" in data


def test_get_item(client: TestClient):
    created = client.post("/articles/", json={"title": "Test"}).json()
    response = client.get(f"/articles/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test"


def test_get_item_not_found(client: TestClient):
    response = client.get("/articles/9999")
    assert response.status_code == 404


def test_update_item(client: TestClient):
    created = client.post("/articles/", json={"title": "Old"}).json()
    response = client.patch(f"/articles/{created['id']}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"


def test_update_item_not_found(client: TestClient):
    response = client.patch("/articles/9999", json={"title": "X"})
    assert response.status_code == 404


def test_delete_item(client: TestClient):
    created = client.post("/articles/", json={"title": "Delete me"}).json()
    response = client.delete(f"/articles/{created['id']}")
    assert response.status_code == 204


def test_delete_item_not_found(client: TestClient):
    response = client.delete("/articles/9999")
    assert response.status_code == 404


def test_read_only_field_ignored_on_create(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class ArticleResource(Resource):
        model = Article
        read_only = {"published"}

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ArticleResource], get_session=get_session)
    client = TestClient(app)

    response = client.post("/articles/", json={"title": "Test", "published": True})
    assert response.status_code == 201
    assert response.json()["published"] is False


def test_read_only_field_ignored_on_update(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class ArticleResource(Resource):
        model = Article
        read_only = {"published"}

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ArticleResource], get_session=get_session)
    client = TestClient(app)

    created = client.post("/articles/", json={"title": "Test"}).json()
    response = client.patch(f"/articles/{created['id']}", json={"published": True})
    assert response.status_code == 200
    assert response.json()["published"] is False


def test_write_only_field_hidden_from_read(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class ArticleResource(Resource):
        model = Article
        write_only = {"author_id"}

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ArticleResource], get_session=get_session)
    client = TestClient(app)

    created = client.post("/articles/", json={"title": "Test", "author_id": 7}).json()
    assert "author_id" not in created

    fetched = client.get(f"/articles/{created['id']}").json()
    assert "author_id" not in fetched


def test_actions_restricted_to_read_only(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class ReadOnlyResource(Resource):
        model = Article
        actions = frozenset({Action.LIST, Action.RETRIEVE})

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ReadOnlyResource], get_session=get_session)
    client = TestClient(app)

    assert client.get("/articles/").status_code == 200
    assert client.get("/articles/9999").status_code == 404

    assert client.post("/articles/", json={"title": "nope"}).status_code == 405
    assert client.patch("/articles/1", json={"title": "nope"}).status_code == 405
    assert client.delete("/articles/1").status_code == 405


def test_excluded_action_not_in_openapi_schema(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class ReadOnlyResource(Resource):
        model = Article
        actions = frozenset({Action.LIST, Action.RETRIEVE})

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ReadOnlyResource], get_session=get_session)
    client = TestClient(app)

    openapi = client.get("/openapi.json").json()
    methods = openapi["paths"]["/articles/"]
    assert "post" not in methods
    assert "get" in methods


def test_actions_create_only(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup
    from tests.conftest import Article

    class CreateOnlyResource(Resource):
        model = Article
        actions = frozenset({Action.CREATE})

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[CreateOnlyResource], get_session=get_session)
    client = TestClient(app)

    assert client.post("/articles/", json={"title": "ok"}).status_code == 201
    assert client.get("/articles/").status_code == 405
    assert client.get("/articles/1").status_code == 404
