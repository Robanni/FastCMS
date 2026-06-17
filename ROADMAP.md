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

## v0.2 — Permissions, Filters, Hooks ✅ (permissions + filters done)

### Permissions ✅

```python
class IsAuthenticated(BasePermission):
    async def __call__(self, request: Request) -> None:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401)

class ArticleResource(Resource):
    model = Article
    permissions = {
        "list": IsAuthenticated(),
        "create": IsEditor(),
        "delete": IsAdmin(),
    }
```

- `BasePermission` — contract, user implements auth logic
- Sync and async `__call__` both supported
- Missing key = open endpoint (no permission check)

### Filters ✅

```python
class ArticleFilter(Filter):
    published: bool
    author_id: int
```

Auto query params: `GET /articles?published=true&author_id=5`

- Equality filtering only (current implementation)
- Future: lookup expressions via `__` suffix (`price__gte`, `title__contains`, `created_at__lt`)

### Hooks ✅

```python
class ArticleResource(Resource):
    async def before_create(self, data: dict, session, request) -> dict: ...
    async def after_create(self, obj, session, request) -> None: ...
    async def before_update(self, obj, data: dict, session, request) -> dict: ...
    async def after_update(self, obj, session, request) -> None: ...
    async def before_delete(self, obj, session, request) -> None: ...
    async def after_delete(self, obj, session, request) -> None: ...
```

- Sync and async hooks both supported
- `before_*` hooks can mutate and return data
- Default no-op stubs — no error if hook not defined

## v0.3 — Search, Sorting, Relations ✅ (sorting done)

### Sorting ✅

```python
class ArticleResource(Resource):
    model = Article
    sort_fields = ["title", "created_at", "author_id"]
```

`GET /articles/?sort=-created_at,title`

- `-field` = DESC, `field` = ASC
- Multiple fields via comma
- Whitelist via `sort_fields` — unknown field → 400
- Sync and async both supported

### Search (planned)

- `search_fields` — full-text search via `LIKE`

### Relations (planned)

- `expand` — inline relation expansion

```python
GET /articles/1?expand=author
```

### Field & route control ✅

```python
class ArticleResource(Resource):
    model = Article
    read_only = {"created_at", "updated_at"}
    write_only = {"internal_note"}
    actions = frozenset({Action.LIST, Action.RETRIEVE})
```

- `read_only` — field excluded from Create/Update schemas, still in Read
- `write_only` — field excluded from Read schema, still writable
- `actions` — restrict which routes get generated (`Action.LIST/RETRIEVE/CREATE/UPDATE/DELETE`); excluded routes are absent from OpenAPI, not just permission-denied

### Per-role field visibility (planned)

- Dynamic, per-request field read/write rules (e.g. owner vs admin) — separate axis from the static `read_only`/`write_only` allowlist
- Needs object-level permission support (`obj` reaching `BasePermission.__call__`) before this can land

## v1.0 — Production Ready

- Nested resources
- Bulk operations
- Soft delete
- Audit log
