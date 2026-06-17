from pydantic import BaseModel, create_model
from sqlalchemy import (
    String,
    Text,
    Integer,
    BigInteger,
    SmallInteger,
    Boolean,
    DateTime,
    Date,
    Time,
    Float,
    Numeric,
    UUID,
    Enum,
    JSON,
    LargeBinary,
    inspect,
)
import datetime
import decimal
import uuid

from sqlalchemy.orm import DeclarativeBase


TYPE_MAP: dict[type, type] = {
    String: str,
    Text: str,
    Integer: int,
    BigInteger: int,
    SmallInteger: int,
    Boolean: bool,
    DateTime: datetime.datetime,
    Date: datetime.date,
    Time: datetime.time,
    Float: float,
    Numeric: decimal.Decimal,
    UUID: uuid.UUID,
    Enum: str,
    JSON: dict,
    LargeBinary: bytes,
}


class SchemaFactory:
    @staticmethod
    def create_schema(
        model: type[DeclarativeBase],
        read_only: set[str] | None = None,
        write_only: set[str] | None = None,
    ) -> tuple[type[BaseModel], type[BaseModel], type[BaseModel]]:
        fields = _extract_fields(model)
        read_only = read_only or set()
        write_only = write_only or set()

        return (
            _build_read(fields, model.__name__, write_only),
            _build_create(fields, model.__name__, read_only),
            _build_update(fields, model.__name__, read_only),
        )


def _extract_fields(model: type[DeclarativeBase]) -> dict[str, dict[str, object]]:
    fields: dict[str, dict[str, object]] = {}
    mapper = inspect(model)

    for column in mapper.columns:
        column_type = type(column.type)

        if (python_type := TYPE_MAP.get(column_type)) is None:
            try:
                python_type = column.type.python_type
            except NotImplementedError:
                raise ValueError(f"Unsupported column type: {column_type.__name__}")

        has_server_default = (
            column.default is not None or column.server_default is not None
        )

        fields[column.key] = {
            "type": python_type,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "has_default": has_server_default,
        }

    return fields


def _build_read(
    fields: dict[str, dict[str, object]],
    model_name: str,
    write_only: set[str] = frozenset(),
) -> type[BaseModel]:
    pydantic_fields = {}
    for key, info in fields.items():
        if key in write_only:
            continue
        if info["nullable"]:
            pydantic_fields[key] = (info["type"] | None, None)
        else:
            pydantic_fields[key] = (info["type"], ...)
    return create_model(f"{model_name}Read", **pydantic_fields)


def _build_create(
    fields: dict[str, dict[str, object]],
    model_name: str,
    read_only: set[str] = frozenset(),
) -> type[BaseModel]:
    pydantic_fields = {}
    for key, info in fields.items():
        if info["primary_key"] or key in read_only:
            continue
        if info["nullable"] or info["has_default"]:
            pydantic_fields[key] = (info["type"] | None, None)
        else:
            pydantic_fields[key] = (info["type"], ...)
    return create_model(f"{model_name}Create", **pydantic_fields)


def _build_update(
    fields: dict[str, dict[str, object]],
    model_name: str,
    read_only: set[str] = frozenset(),
) -> type[BaseModel]:
    pydantic_fields = {}

    for key, info in fields.items():
        if info["primary_key"] or key in read_only:
            continue
        pydantic_fields[key] = (info["type"] | None, None)

    return create_model(f"{model_name}Update", **pydantic_fields)
