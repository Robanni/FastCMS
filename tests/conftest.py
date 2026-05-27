import pytest
from sqlalchemy import create_engine, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)


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
