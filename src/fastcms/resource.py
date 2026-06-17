from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import DeclarativeBase

from fastcms.permission import BasePermission

if TYPE_CHECKING:
    from fastcms.filter import Filter


class Resource:
    model: type[DeclarativeBase]

    permissions: dict[str, BasePermission] = {}

    # Optional filter class — subclass of Filter
    filter_class: type[Filter] | None = None

    search_fields: list[str] = []
    sort_fields: list[str] = []

    prefix: str | None = None
    tags: list[str] | None = None

    read_only: set[str] = set()
    write_only: set[str] = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "model"):
            raise TypeError(f"{cls.__name__} must define 'model'")

    def before_create(self, data: dict, session, request) -> dict:
        return data

    def after_create(self, obj, session, request) -> None:
        pass

    def before_update(self, obj, data: dict, session, request) -> dict:
        return data

    def after_update(self, obj, session, request) -> None:
        pass

    def before_delete(self, obj, session, request) -> None:
        pass

    def after_delete(self, data: dict, session, request) -> None:
        pass
