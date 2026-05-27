import inspect
from sqlalchemy import select
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

    # --- sync ---
    def get_list(self, session: Session, offset: int = 0, limit: int = 20) -> list[T]:
        result = session.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    def get_one(self, session: Session, id: int) -> T | None:
        return session.get(self.model, id)

    def create(self, session: Session, data: dict) -> T:
        obj = self.model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def update(
        self,
        session: Session,
        id: int,
        data: dict,
    ) -> T | None:
        obj = session.get(self.model, id)
        if obj is None:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return obj

    def delete(
        self,
        session: Session,
        id: int,
    ) -> bool:
        obj = session.get(self.model, id)
        if obj is None:
            return False
        session.delete(obj)
        session.commit()
        return True

    # --- async ---
    async def async_get_list(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> list[T]:
        result = await session.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    async def async_get_one(self, session: AsyncSession, id: int) -> T | None:
        return await session.get(self.model, id)

    async def async_create(self, session: AsyncSession, data: dict) -> T:
        obj = self.model(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def async_update(
        self, session: AsyncSession, id: int, data: dict
    ) -> T | None:
        obj = await session.get(self.model, id)
        if obj is None:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(obj, key, value)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def async_delete(self, session: AsyncSession, id: int) -> bool:
        obj = await session.get(self.model, id)
        if obj is None:
            return False
        await session.delete(obj)
        await session.commit()
        return True
