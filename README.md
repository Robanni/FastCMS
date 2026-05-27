# FastCMS

Lightweight CRUD framework for FastAPI. Declare a resource — get a full API.

```python
class ArticleResource(Resource):
    model = Article
```

```
GET    /articles
GET    /articles/{id}
POST   /articles
PATCH  /articles/{id}
DELETE /articles/{id}
```

## Installation

```bash
pip install fastcms
```

## Quick Start

### 1. Define your SQLAlchemy model

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    body: Mapped[str]
```

### 2. Create a resource

```python
from fastcms import Resource

class ArticleResource(Resource):
    model = Article
```

### 3. Register with FastAPI

```python
from fastapi import FastAPI
from fastcms import setup

app = FastAPI()
setup(app, resources=[ArticleResource], get_session=get_db)
```

That's it. Full CRUD with pagination and OpenAPI docs at `/docs`.

---

## Session Setup

FastCMS detects sync vs async mode from the return annotation of `get_session`.

### Sync (SQLAlchemy `Session`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///db.sqlite3")

def get_db() -> Session:
    with Session(engine) as session:
        yield session
```

### Async (SQLAlchemy `AsyncSession`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

---

## Pagination

All list endpoints support `offset` and `limit` query parameters.

```
GET /articles?offset=0&limit=20
```

Response:

```json
[
  { "id": 1, "title": "Hello" },
  { "id": 2, "title": "World" }
]
```

---

## Permissions

Protect endpoints by adding `permissions` to your resource.

Implement `BasePermission` with your own auth logic:

```python
from fastapi import HTTPException, Request
from fastcms.permission import BasePermission

class IsAuthenticated(BasePermission):
    async def __call__(self, request: Request) -> None:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

class IsAdmin(BasePermission):
    async def __call__(self, request: Request) -> None:
        user = await get_current_user(request)  # your auth logic
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Forbidden")
```

Assign permissions per action:

```python
class ArticleResource(Resource):
    model = Article
    permissions = {
        "list":     IsAuthenticated(),
        "retrieve": IsAuthenticated(),
        "create":   IsAdmin(),
        "update":   IsAdmin(),
        "delete":   IsAdmin(),
    }
```

Available actions: `list`, `retrieve`, `create`, `update`, `delete`.

Missing key = open endpoint (no check performed).

Both sync and async `__call__` are supported.

---

## Resource Options

```python
class ArticleResource(Resource):
    model = Article

    prefix = "/posts"           # default: "/{model_name_lowercase}s"
    tags = ["Posts"]            # default: [model.__name__]

    permissions = {
        "create": IsAuthenticated(),
    }
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including filters, hooks, search, sorting, and relation expansion.
