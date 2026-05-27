import datetime
import decimal
import uuid

from pydantic import BaseModel

from fastcms.schema import SchemaFactory
from tests.conftest import Article, FullTypesModel


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


def test_full_types_schema_created():
    read, create, update = SchemaFactory.create_schema(FullTypesModel)
    assert issubclass(read, BaseModel)
    assert issubclass(create, BaseModel)
    assert issubclass(update, BaseModel)


def test_full_types_field_types():
    read, _, _ = SchemaFactory.create_schema(FullTypesModel)
    fields = read.model_fields

    assert fields["big_num"].annotation == int
    assert fields["name"].annotation == str
    assert fields["score"].annotation == float
    assert fields["price"].annotation == decimal.Decimal
    assert fields["born"].annotation == datetime.date | None
    assert fields["alarm"].annotation == datetime.time | None
    assert fields["created_at"].annotation == datetime.datetime
    assert fields["uid"].annotation == uuid.UUID | None
    assert fields["status"].annotation == str
    assert fields["bio"].annotation == str | None
