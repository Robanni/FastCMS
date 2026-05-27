import pytest

from fastcms.service import CrudService
from tests.conftest import Article


@pytest.fixture
def service(get_session_factory):
    return CrudService(Article, get_session_factory)


def test_service_sync_mode(service: CrudService[Article]):
    assert service.async_mode is False


def test_create(service: CrudService[Article], session):
    obj = service.create(session, {"title": "Hello"})
    assert obj.id is not None
    assert obj.title == "Hello"


def test_get_one(service: CrudService[Article], session):
    obj = service.create(session, {"title": "Hello"})
    found = service.get_one(session, obj.id)
    assert found is not None
    assert found.title == "Hello"


def test_get_one_not_found(service: CrudService[Article], session):
    assert service.get_one(session, 9999) is None


def test_get_list(service: CrudService[Article], session):
    service.create(session, {"title": "A"})
    service.create(session, {"title": "B"})
    items = service.get_list(session)
    assert len(items) == 2


def test_get_list_pagination(service: CrudService[Article], session):
    for i in range(5):
        service.create(session, {"title": f"Article {i}"})
    items = service.get_list(session, offset=0, limit=2)
    assert len(items) == 2


def test_update(service: CrudService[Article], session):
    obj = service.create(session, {"title": "Old"})
    updated = service.update(session, obj.id, {"title": "New"})
    assert updated.title == "New"


def test_update_not_found(service: CrudService[Article], session):
    assert service.update(session, 9999, {"title": "X"}) is None


def test_delete(service: CrudService[Article], session):
    obj = service.create(session, {"title": "Delete me"})
    deleted = service.delete(session, obj.id)
    assert deleted is not None
    assert deleted.title == "Delete me"
    assert service.get_one(session, obj.id) is None


def test_delete_not_found(service: CrudService[Article], session):
    assert service.delete(session, 9999) is None
