import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastcms import Resource, setup
from tests.conftest import Article


def make_app(engine, resource_cls):
    def get_session() -> Session:
        return Session(engine)

    app = FastAPI()
    setup(app, resources=[resource_cls], get_session=get_session)
    return app


# --- sync hooks ---


def test_before_create_can_mutate_data(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def before_create(self, data: dict, session, request) -> dict:
            calls.append(("before_create", data.copy()))
            data["title"] = data["title"].upper()
            return data

    client = TestClient(make_app(engine, ArticleResource))
    resp = client.post("/articles/", json={"title": "hello"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "HELLO"
    assert calls[0][0] == "before_create"


def test_after_create_called_with_obj(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def after_create(self, obj, session, request) -> None:
            calls.append(obj.title)

    client = TestClient(make_app(engine, ArticleResource))
    client.post("/articles/", json={"title": "after"})
    assert calls == ["after"]


def test_before_update_can_mutate_data(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def before_update(self, obj, data: dict, session, request) -> dict:
            calls.append(("before_update", obj.id))
            data["title"] = data["title"] + "_patched"
            return data

    client = TestClient(make_app(engine, ArticleResource))
    created = client.post("/articles/", json={"title": "orig"}).json()
    resp = client.patch(f"/articles/{created['id']}", json={"title": "new"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "new_patched"
    assert calls[0][0] == "before_update"


def test_after_update_called(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def after_update(self, obj, session, request) -> None:
            calls.append(obj.title)

    client = TestClient(make_app(engine, ArticleResource))
    created = client.post("/articles/", json={"title": "orig"}).json()
    client.patch(f"/articles/{created['id']}", json={"title": "upd"})
    assert calls == ["upd"]


def test_before_delete_called_with_obj(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def before_delete(self, obj, session, request) -> None:
            calls.append(obj.id)

    client = TestClient(make_app(engine, ArticleResource))
    created = client.post("/articles/", json={"title": "del"}).json()
    client.delete(f"/articles/{created['id']}")
    assert calls == [created["id"]]


def test_after_delete_called(engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        def after_delete(self, obj, session, request) -> None:
            calls.append(obj.title)

    client = TestClient(make_app(engine, ArticleResource))
    created = client.post("/articles/", json={"title": "gone"}).json()
    client.delete(f"/articles/{created['id']}")
    assert calls == ["gone"]


def test_no_hooks_defined_no_error(engine):
    class ArticleResource(Resource):
        model = Article

    client = TestClient(make_app(engine, ArticleResource))
    resp = client.post("/articles/", json={"title": "plain"})
    assert resp.status_code == 201


# --- async hooks ---

aiosqlite = pytest.importorskip("aiosqlite", reason="aiosqlite not installed")


@pytest.fixture
def async_engine():
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from tests.conftest import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init())
    yield engine
    asyncio.get_event_loop().run_until_complete(engine.dispose())


def make_async_app(async_engine, resource_cls):
    from collections.abc import AsyncGenerator
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(async_engine, expire_on_commit=False)

    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app = FastAPI()
    setup(app, resources=[resource_cls], get_session=get_session)
    return app


def test_async_before_create_can_mutate_data(async_engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        async def before_create(self, data: dict, session, request) -> dict:
            calls.append("before_create")
            data["title"] = data["title"].upper()
            return data

    client = TestClient(make_async_app(async_engine, ArticleResource))
    resp = client.post("/articles/", json={"title": "async"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "ASYNC"
    assert "before_create" in calls


def test_async_after_create_called(async_engine):
    calls = []

    class ArticleResource(Resource):
        model = Article

        async def after_create(self, obj, session, request) -> None:
            calls.append(obj.title)

    client = TestClient(make_async_app(async_engine, ArticleResource))
    client.post("/articles/", json={"title": "after"})
    assert calls == ["aafter"]
