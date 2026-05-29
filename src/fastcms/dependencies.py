from __future__ import annotations

import inspect
import types
from typing import TYPE_CHECKING, Annotated, Union, get_args, get_origin

from fastapi import Depends, Query, Request
from fastapi.params import Depends as DependsType
from pydantic import ValidationError

if TYPE_CHECKING:
    from fastcms.resource import Resource


def _is_list_field(field_info) -> bool:
    """Return True if field annotation is list[X] or list[X] | None."""
    ann = field_info.annotation
    origin = get_origin(ann)
    _UnionType = getattr(types, "UnionType", None)
    if (_UnionType is not None and origin is _UnionType) or origin is Union:
        return any(get_origin(arg) is list for arg in get_args(ann))
    return origin is list


def _make_list_filter_dep(filter_cls) -> DependsType:
    """Build a dependency with an explicit typed signature so FastAPI generates
    correct OpenAPI docs and performs 422 validation for all query params."""
    # Build __signature__ so FastAPI sees named Query params with correct types.
    # Query() without default goes in Annotated; default=None is on the Parameter.
    params_list = []
    for name, fi in filter_cls.model_fields.items():
        params_list.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[fi.annotation, Query()],
            )
        )

    def _dep(**kwargs):
        params = {k: v for k, v in kwargs.items() if v is not None}
        try:
            return filter_cls.model_validate(params)
        except ValidationError as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=exc.errors(include_url=False)) from exc

    _dep.__signature__ = inspect.Signature(params_list)  # type: ignore[attr-defined]
    _dep.__name__ = f"filter_dep_{filter_cls.__name__}"

    return Depends(_dep)


def make_filter_dep(resource: Resource) -> DependsType | None:
    if resource.filter_class is None:
        return None

    filter_cls = resource.filter_class
    has_list_field = any(
        _is_list_field(fi) for fi in filter_cls.model_fields.values()
    )

    if not has_list_field:
        return Depends(filter_cls)

    return _make_list_filter_dep(filter_cls)


def make_sort_dep(resource: Resource) -> DependsType | None:
    allowed = resource.sort_fields
    if not allowed:
        return None

    def _dep(sort: str | None = Query(default=None)) -> list[tuple[str, bool]] | None:
        if sort is None:
            return None
        result = []
        for part in sort.split(","):
            part = part.strip()
            if not part:
                continue
            desc = part.startswith("-")
            field = part.lstrip("-")
            if field not in allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=400,
                    detail=f"Sort field '{field}' not allowed. Allowed: {', '.join(allowed)}",
                )
            result.append((field, desc))
        return result or None

    return Depends(_dep)


def make_permission_dep(action: str, resource: Resource) -> DependsType | None:
    async def dep(request: Request) -> None:
        permission = resource.permissions.get(action)
        if permission is None:
            return
        result = permission(request)
        if inspect.isawaitable(result):
            await result

    return Depends(dep)
