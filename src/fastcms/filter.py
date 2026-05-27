from __future__ import annotations


from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase


class Filter(BaseModel):
    """
    Base class for query filters.

    Subclass and declare fields matching model column names.
    Each non-None field is applied as an equality WHERE clause.

    Example::

        class ArticleFilter(Filter):
            published: bool | None = None
            author_id: int | None = None

        class ArticleResource(Resource):
            model = Article
            filter_class = ArticleFilter
    """

    model_config = {"extra": "ignore"}

    def apply(self, query: Select, model: type[DeclarativeBase]):
        """Apply non-None fields as WHERE clauses to *query*."""
        for field_name, value in self.model_dump(exclude_none=True).items():
            column = getattr(model, field_name, None)
            if column is not None:
                query = query.where(column == value)
        return query
