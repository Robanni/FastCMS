# FastCMS Roadmap

## v0.1 — MVP ✅

Minimal resource declaration generates full CRUD API.

```python
class ArticleResource(Resource):
    model = Article
```

- Auto CRUD routes (`GET`, `POST`, `PATCH`, `DELETE`)
- Auto Pydantic schema generation from SQLAlchemy model
- Sync / async mode detected from session type
- Offset/limit pagination
- OpenAPI support

## v0.2 — Filters, Permissions, Hooks

- **Typed filters** via `Filter` class

```python
class ArticleFilter(Filter):
    published: bool
    author_id: int
```

- **Per-action permissions**

```python
class ArticleResource(Resource):
    permissions = {
        "list": IsAuthenticated,
        "create": IsEditor,
        "delete": IsAdmin,
    }
```

- **Lifecycle hooks**

```python
class ArticleResource(Resource):
    async def before_create(self, data, user): ...
    async def after_update(self, obj, user): ...
```

## v0.3 — Search, Sorting, Relations

- `search_fields` — full-text search via `LIKE`
- `sort_fields` — `?sort=-created_at`
- `expand` — inline relation expansion

```python
GET /articles/1?expand=author
```

## v1.0 — Production Ready

- Nested resources
- Bulk operations
- Soft delete
- Audit log
