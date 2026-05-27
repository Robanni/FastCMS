from pydantic import BaseModel

from fastcms.schema import SchemaFactory
from tests.conftest import Article


def test_schema_factory_returns_three_schemas():
    read, create, update = SchemaFactory.create_schema(Article)
    assert issubclass(read, BaseModel)
    assert issubclass(create, BaseModel)
    assert issubclass(update, BaseModel)


def test_schema_names():
    read, create, update = SchemaFactory.create_schema(Article)
    assert read.__name__ == "ArticleRead"
    assert create.__name__ == "ArticleCreate"
    assert update.__name__ == "ArticleUpdate"


def test_read_schema_has_id():
    read, _, _ = SchemaFactory.create_schema(Article)
    assert "id" in read.model_fields


def test_create_schema_no_id():
    _, create, _ = SchemaFactory.create_schema(Article)
    assert "id" not in create.model_fields
    assert "title" in create.model_fields


def test_update_schema_all_optional():
    _, _, update = SchemaFactory.create_schema(Article)
    for field in update.model_fields.values():
        assert not field.is_required()
