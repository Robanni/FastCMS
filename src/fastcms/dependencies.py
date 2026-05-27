from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from fastapi import Depends, Request
from fastapi.params import Depends as DependsType

if TYPE_CHECKING:
    from fastcms.resource import Resource


def make_filter_dep(resource: type[Resource]) -> DependsType | None:
    if resource.filter_class is None:
        return None
    return Depends(resource.filter_class)


def make_permission_dep(action: str, resource: type[Resource]) -> DependsType | None:
    async def dep(request: Request) -> None:
        permission = resource.permissions.get(action)
        if permission is None:
            return
        result = permission(request)
        if inspect.isawaitable(result):
            await result

    return Depends(dep)
