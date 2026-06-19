import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms import Resource, setup
from fastcms.guard import BaseGuard
from fastcms.permission import BasePermission
from fastcms.resource import Action
from tests.conftest import Article


def deny_func(request: Request) -> None:
    raise HTTPException(status_code=403, detail="Blocked by guard")


def allow_func(request: Request) -> None:
    pass


class DenyGuard(BaseGuard):
    async def __call__(self, request: Request) -> None:
        raise HTTPException(status_code=429, detail="Rate limited")


class AllowGuard(BaseGuard):
    async def __call__(self, request: Request) -> None:
        pass


class AllowAllPermission(BasePermission):
    async def __call__(self, request: Request) -> None:
        pass


@pytest.fixture
def guarded_client(engine):
    class GuardedResource(Resource):
        model = Article
        guards = {
            Action.LIST: [deny_func],
            Action.CREATE: [DenyGuard()],
        }

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[GuardedResource], get_session=get_session)
    return TestClient(app)


@pytest.fixture
def multi_guard_client(engine):
    class MultiGuardResource(Resource):
        model = Article
        guards = {
            Action.LIST: [allow_func, AllowGuard(), deny_func],
        }

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[MultiGuardResource], get_session=get_session)
    return TestClient(app)


@pytest.fixture
def guard_and_permission_client(engine):
    class CombinedResource(Resource):
        model = Article
        permissions = {"list": AllowAllPermission()}
        guards = {Action.LIST: [deny_func]}

    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[CombinedResource], get_session=get_session)
    return TestClient(app)


def test_function_guard_blocks_list(guarded_client: TestClient):
    response = guarded_client.get("/articles/")
    assert response.status_code == 403


def test_class_guard_blocks_create(guarded_client: TestClient):
    response = guarded_client.post("/articles/", json={"title": "Test"})
    assert response.status_code == 429


def test_action_without_guard_not_blocked(guarded_client: TestClient):
    response = guarded_client.get("/articles/9999")
    assert response.status_code == 404  # not blocked by guard, just missing


def test_multiple_guards_first_failure_blocks(multi_guard_client: TestClient):
    response = multi_guard_client.get("/articles/")
    assert response.status_code == 403


def test_guards_and_permissions_combined(guard_and_permission_client: TestClient):
    response = guard_and_permission_client.get("/articles/")
    assert response.status_code == 403
