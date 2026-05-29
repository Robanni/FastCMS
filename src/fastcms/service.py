import inspect

from sqlalchemy import Select, select, asc, desc
from typing import Callable, Generic, TypeVar


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session

T = TypeVar("T", bound=DeclarativeBase)

type AnySession = AsyncSession | Session
type SessionFactory = Callable[..., AnySession]


def _is_async(get_session: SessionFactory) -> bool:
    hints = inspect.get_annotations(get_session)
    return hints.get("return") is AsyncSession


class CrudService(Generic[T]):
    def __init__(self, model: type[T], get_session: SessionFactory) -> None:
        self.model: type[T] = model
        self.get_session = get_session
        self.async_mode = _is_async(get_session)

    def _apply_sort(self, query: Select, sort_params):
        if not sort_params:
            return query
        for field, descending in sort_params:
            col = getattr(self.model, field, None)
            if col is not None:
                query = query.order_by(desc(col) if descending else asc(col))
        return query

    # --- sync ---
    def get_list(
        self,
        session: Session,
        offset: int = 0,
        limit: int = 20,
        filters=None,
        sort=None,
    ) -> list[T]:
        query = select(self.model)
        if filters is not None:
            query = filters.apply(query, self.model)
        query = self._apply_sort(query, sort)
        result = session.execute(query.offset(offset).limit(limit))
        return result.scalars().all()

    def get_one(self, session: Session, id: int) -> T | None:
        return session.get(self.model, id)

    def create(self, session: Session, data: dict) -> T:
        obj = self.model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def update(self, session: Session, obj: T, data: dict) -> T:
        for key, value in data.items():
            setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return obj

    def delete(self, session: Session, obj: T) -> dict:
        from sqlalchemy import inspect as sa_inspect

        data = {c.key: getattr(obj, c.key) for c in sa_inspect(obj).mapper.column_attrs}
        session.delete(obj)
        session.commit()
        return data

    # --- async ---
    async def async_get_list(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        filters=None,
        sort=None,
    ) -> list[T]:
        query = select(self.model)
        if filters is not None:
            query = filters.apply(query, self.model)
        query = self._apply_sort(query, sort)
        result = await session.execute(query.offset(offset).limit(limit))
        return result.scalars().all()

    async def async_get_one(self, session: AsyncSession, id: int) -> T | None:
        return await session.get(self.model, id)

    async def async_create(self, session: AsyncSession, data: dict) -> T:
        obj = self.model(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def async_update(self, session: AsyncSession, obj: T, data: dict) -> T:
        for key, value in data.items():
            setattr(obj, key, value)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def async_delete(self, session: AsyncSession, obj: T) -> dict:
        from sqlalchemy import inspect as sa_inspect

        data = {c.key: getattr(obj, c.key) for c in sa_inspect(obj).mapper.column_attrs}
        await session.delete(obj)
        await session.commit()
        return data
