import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms import Resource, setup
from fastcms.permission import BasePermission
from tests.conftest import Article


class DenyAll(BasePermission):
    async def __call__(self, request: Request) -> None:
        raise HTTPException(status_code=403, detail="Forbidden")


class AllowAll(BasePermission):
    async def __call__(self, request: Request) -> None:
        pass


class CheckToken(BasePermission):
    async def __call__(self, request: Request) -> None:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")


@pytest.fixture
def protected_client(engine):
    class ProtectedResource(Resource):
        model = Article
        permissions = {
            "list": CheckToken(),
            "retrieve": CheckToken(),
            "create": CheckToken(),
            "update": CheckToken(),
            "delete": CheckToken(),
        }

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[ProtectedResource], get_session=get_session)
    return TestClient(app)


@pytest.fixture
def denied_client(engine):
    class DeniedResource(Resource):
        model = Article
        permissions = {
            "list": DenyAll(),
            "create": DenyAll(),
        }

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[DeniedResource], get_session=get_session)
    return TestClient(app)


# --- CheckToken tests ---

def test_list_without_token_returns_401(protected_client: TestClient):
    response = protected_client.get("/articles/")
    assert response.status_code == 401


def test_list_with_token_returns_200(protected_client: TestClient):
    response = protected_client.get("/articles/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200


def test_create_without_token_returns_401(protected_client: TestClient):
    response = protected_client.post("/articles/", json={"title": "Test"})
    assert response.status_code == 401


def test_create_with_token_returns_201(protected_client: TestClient):
    response = protected_client.post(
        "/articles/",
        json={"title": "Test"},
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 201


def test_update_without_token_returns_401(protected_client: TestClient):
    response = protected_client.patch("/articles/1", json={"title": "X"})
    assert response.status_code == 401


def test_delete_without_token_returns_401(protected_client: TestClient):
    response = protected_client.delete("/articles/1")
    assert response.status_code == 401


# --- DenyAll tests ---

def test_deny_all_list_returns_403(denied_client: TestClient):
    response = denied_client.get("/articles/")
    assert response.status_code == 403


def test_deny_all_create_returns_403(denied_client: TestClient):
    response = denied_client.post("/articles/", json={"title": "Test"})
    assert response.status_code == 403


def test_deny_all_retrieve_not_protected(denied_client: TestClient):
    # retrieve не в permissions — должен пропускать
    response = denied_client.get("/articles/9999")
    assert response.status_code == 404  # не 403
