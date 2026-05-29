from __future__ import annotations


from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase


_LOOKUPS = {
    "eq":         lambda col, v: col == v,
    "ne":         lambda col, v: col != v,
    "gt":         lambda col, v: col > v,
    "gte":        lambda col, v: col >= v,
    "lt":         lambda col, v: col < v,
    "lte":        lambda col, v: col <= v,
    "contains":   lambda col, v: col.contains(v),
    "startswith": lambda col, v: col.startswith(v),
    "endswith":   lambda col, v: col.endswith(v),
    "in":         lambda col, v: col.in_(v),
    "isnull":     lambda col, v: col.is_(None) if v else col.is_not(None),
}


class Filter(BaseModel):
    """
    Base class for query filters.

    Subclass and declare fields matching model column names.
    Supports lookup suffixes separated by ``__``:

    Example::

        class ArticleFilter(Filter):
            published: bool | None = None        # exact match (==)
            author_id__gte: int | None = None    # >=
            author_id__lt: int | None = None     # <
            title__contains: str | None = None   # LIKE %v%
            status__in: list[str] | None = None  # IN (...)
            bio__isnull: bool | None = None      # IS NULL / IS NOT NULL

        class ArticleResource(Resource):
            model = Article
            filter_class = ArticleFilter

    Supported lookups: eq, ne, gt, gte, lt, lte,
    contains, startswith, endswith, in, isnull.
    """

    model_config = {"extra": "ignore"}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: object) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        for field_name in cls.model_fields:
            if "__" in field_name:
                lookup = field_name.rsplit("__", 1)[1]
                if lookup not in _LOOKUPS:
                    raise TypeError(
                        f"{cls.__name__}: unknown filter lookup '{lookup}' in field '{field_name}'. "
                        f"Valid lookups: {', '.join(_LOOKUPS)}"
                    )

    def apply(self, query: Select, model: type[DeclarativeBase]) -> Select:
        """Apply non-None fields as WHERE clauses to *query*."""
        for field_name, value in self.model_dump(exclude_none=True).items():
            if "__" in field_name:
                col_name, lookup = field_name.rsplit("__", 1)
            else:
                col_name, lookup = field_name, "eq"

            column = getattr(model, col_name, None)
            if column is None:
                continue

            query = query.where(_LOOKUPS[lookup](column, value))
        return query
