# FastCMS

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Lightweight CRUD framework for FastAPI. Declare a resource — get a full REST API.

```python
class ArticleResource(Resource):
    model = Article
```

```
GET    /articles/
GET    /articles/{id}
POST   /articles/
PATCH  /articles/{id}
DELETE /articles/{id}
```

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Session Setup](#session-setup)
- [Pagination](#pagination)
- [Sorting](#sorting)
- [Filters](#filters)
- [Permissions](#permissions)
- [Hooks](#hooks)
- [Field & Route Control](#field--route-control)
- [Resource Options](#resource-options)
- [Roadmap](#roadmap)

---

## Installation

```bash
pip install git+https://github.com/Robanni/fastcms.git
```

---

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
    published: Mapped[bool] = mapped_column(default=False)
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

Full CRUD with pagination, sorting, and OpenAPI docs at `/docs`. No extra code.

---

## Session Setup

FastCMS auto-detects sync vs async mode from the return annotation of `get_session`.

### Sync (`Session`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///db.sqlite3")

def get_db() -> Session:
    with Session(engine) as session:
        yield session
```

### Async (`AsyncSession`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

---

## Pagination

All list endpoints support `offset` and `limit` query params.

```
GET /articles/?offset=20&limit=10
```

```json
[
  { "id": 21, "title": "Hello" },
  { "id": 22, "title": "World" }
]
```

---

## Sorting

Whitelist sortable fields via `sort_fields`, then use `?sort=` in requests.

```python
class ArticleResource(Resource):
    model = Article
    sort_fields = ["title", "created_at", "author_id"]
```

```
GET /articles/?sort=-created_at          → newest first
GET /articles/?sort=title                → A→Z
GET /articles/?sort=-created_at,title    → multiple fields
```

- Prefix `-` = DESC, no prefix = ASC
- Unknown field → `400 Bad Request`
- Works in both sync and async mode

---

## Filters

Declare filter fields via `filter_class`. Each field becomes an optional query param.

```python
from fastcms import Filter

class ArticleFilter(Filter):
    published: bool | None = None
    author_id: int | None = None

class ArticleResource(Resource):
    model = Article
    filter_class = ArticleFilter
```

```
GET /articles/                               → all
GET /articles/?published=true                → published only
GET /articles/?author_id=5                   → by author
GET /articles/?published=true&author_id=5    → combined
```

`None` fields are ignored — no WHERE clause added. Fields absent from the model are silently skipped.

---

## Permissions

Protect any endpoint by implementing `BasePermission`.

```python
from fastapi import HTTPException, Request
from fastcms.permission import BasePermission

class IsAuthenticated(BasePermission):
    async def __call__(self, request: Request) -> None:
        if not request.headers.get("Authorization"):
            raise HTTPException(status_code=401, detail="Not authenticated")

class IsAdmin(BasePermission):
    async def __call__(self, request: Request) -> None:
        user = await get_current_user(request)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Forbidden")
```

Assign per action:

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

| Action     | Endpoint              |
|------------|-----------------------|
| `list`     | `GET /articles/`      |
| `retrieve` | `GET /articles/{id}`  |
| `create`   | `POST /articles/`     |
| `update`   | `PATCH /articles/{id}`|
| `delete`   | `DELETE /articles/{id}`|

Missing key = open endpoint. Both sync and async `__call__` supported.

---

## Hooks

Intercept create / update / delete lifecycle with hooks on the resource class.

```python
class ArticleResource(Resource):
    model = Article

    async def before_create(self, data: dict, session, request) -> dict:
        data["created_by"] = request.state.user_id
        return data

    async def after_create(self, obj, session, request) -> None:
        await notify_subscribers(obj)

    async def before_update(self, obj, data: dict, session, request) -> dict:
        return data

    async def after_update(self, obj, session, request) -> None: ...

    async def before_delete(self, obj, session, request) -> None: ...

    async def after_delete(self, obj, session, request) -> None: ...
```

- `before_*` hooks return (optionally mutated) data dict
- `after_*` hooks receive the saved/deleted object
- Both sync and async hooks supported
- Default stubs are no-ops — safe to omit any hook

---

## Field & Route Control

### `read_only` / `write_only`

Exclude fields from the Create/Update or Read schema — independent of permissions, enforced at the schema level for every request.

```python
class ArticleResource(Resource):
    model = Article
    read_only = {"created_at", "updated_at"}   # never in Create/Update, still in Read
    write_only = {"internal_note"}             # never in Read, still writable
```

A `read_only` field sent in a request body is silently ignored — the server-side/default value wins, not a `422`.

### `actions`

Restrict which routes get generated at all. Excluded actions are absent from the router entirely — not just permission-denied, also gone from `/docs` and `openapi.json`.

```python
from fastcms.resource import Action

class ReadOnlyResource(Resource):
    model = Article
    actions = frozenset({Action.LIST, Action.RETRIEVE})
```

| `Action`   | Endpoint                |
|------------|--------------------------|
| `LIST`     | `GET /articles/`         |
| `RETRIEVE` | `GET /articles/{id}`     |
| `CREATE`   | `POST /articles/`        |
| `UPDATE`   | `PATCH /articles/{id}`   |
| `DELETE`   | `DELETE /articles/{id}`  |

Default: all actions enabled. Useful for duplicating a resource under a different `prefix` to expose a narrower API (e.g. public read-only vs admin full CRUD) without juggling permissions.

---

## Resource Options

```python
class ArticleResource(Resource):
    model = Article

    prefix = "/posts"              # default: /{model_name_lowercase}s
    tags = ["Posts"]               # default: [model.__name__]

    filter_class = ArticleFilter   # optional
    sort_fields = ["title", "created_at"]  # optional

    read_only = {"created_at", "updated_at"}  # optional
    write_only = {"internal_note"}            # optional
    actions = frozenset({Action.LIST, Action.RETRIEVE})  # optional, default: all

    permissions = {
        "create": IsAuthenticated(),
        "update": IsAdmin(),
        "delete": IsAdmin(),
    }
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features.

**Current:** v0.3.0 — sorting, filters, hooks, permissions, field/route control, sync/async  
**Next:** full-text search (`search_fields`), relation expansion (`expand=author`)
