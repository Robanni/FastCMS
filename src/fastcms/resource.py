from sqlalchemy.orm import DeclarativeBase


class Resource:
    model: type[DeclarativeBase]

    search_fields: list[str] = []
    sort_fields: list[str] = []

    prefix: str | None = None
    tags: list[str] | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "model"):
            raise TypeError(f"{cls.__name__} must define 'model'")
