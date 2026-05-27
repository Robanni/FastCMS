from pydantic import BaseModel, create_model
from sqlalchemy import String, Integer, Boolean, DateTime, inspect
import datetime

from sqlalchemy.orm import DeclarativeBase


TYPE_MAP: dict[type, type] = {
    String: str,
    Integer: int,
    Boolean: bool,
    DateTime: datetime.datetime,
}


class SchemaFactory:
    @staticmethod
    def create_schema(
        model: type[DeclarativeBase],
    ) -> tuple[type[BaseModel], type[BaseModel], type[BaseModel]]:
        fields = _extract_fields(model)
        return (
            _build_read(fields, model.__name__),
            _build_create(fields, model.__name__),
            _build_update(fields, model.__name__),
        )


def _extract_fields(model: type[DeclarativeBase]) -> dict[str, dict[str, object]]:
    fields: dict[str, dict[str, object]] = {}
    mapper = inspect(model)

    for column in mapper.columns:
        column_type = type(column.type)

        if (python_type := TYPE_MAP.get(column_type)) is None:
            raise ValueError(f"{column_type} is not supported!")

        fields[column.key] = {
            "type": python_type,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
        }

    return fields


def _build_read(
    fields: dict[str, dict[str, object]], model_name: str
) -> type[BaseModel]:
    pydantic_fields = {key: (info["type"], ...) for key, info in fields.items()}
    return create_model(f"{model_name}Read", **pydantic_fields)


def _build_create(
    fields: dict[str, dict[str, object]], model_name: str
) -> type[BaseModel]:
    pydantic_fields = {
        key: (info["type"], ...)
        for key, info in fields.items()
        if not info["primary_key"]
    }
    return create_model(f"{model_name}Create", **pydantic_fields)


def _build_update(fields: dict[str, dict[str, object]], model_name: str) -> type[BaseModel]:
    pydantic_fields = {
        key: (info["type"] | None, None)
        for key, info in fields.items()
        if not info["primary_key"]
    }
    return create_model(f"{model_name}Update", **pydantic_fields)
