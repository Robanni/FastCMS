import datetime
import decimal
import uuid

import pytest
from sqlalchemy import (
    BigInteger, Boolean, create_engine, Date, DateTime, Enum,
    Float, Integer, Numeric, String, Text, Time, UUID,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FullTypesModel(Base):
    __tablename__ = "full_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    big_num: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2))
    uid: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)
    status: Mapped[str] = mapped_column(Enum("active", "inactive", name="status_enum"))
    born: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    alarm: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)


@pytest.fixture(scope="function")
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def get_session_factory(engine):
    def get_session() -> Session:
        return Session(engine)

    return get_session


@pytest.fixture
def app(engine):
    from fastapi import FastAPI
    from fastcms import Resource, setup

    class ArticleResource(Resource):
        model = Article

    def get_session() -> Session:
        return Session(engine)

    application = FastAPI()
    setup(application, resources=[ArticleResource], get_session=get_session)
    return application


@pytest.fixture
def app_with_filter(engine):
    from fastapi import FastAPI
    from fastcms import Filter, Resource, setup

    class ArticleFilter(Filter):
        published: bool | None = None
        author_id: int | None = None

    class ArticleResource(Resource):
        model = Article
        filter_class = ArticleFilter

    def get_session() -> Session:
        return Session(engine)

    application = FastAPI()
    setup(application, resources=[ArticleResource], get_session=get_session)
    return application
