from sqlalchemy.orm import DeclarativeBase


class Resource:
    model: type[DeclarativeBase]

    search_fields: list[str] = []
    sort_fields: list[str] = []

    prefix: str | None = None
    tags: list[str] | None = None
