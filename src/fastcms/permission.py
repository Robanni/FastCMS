from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from fastapi import Depends, Request

if TYPE_CHECKING:
    from fastcms.resource import Resource


class BasePermission:
    async def __call__(self, request: Request) -> None:
        """
        Raise HTTPException to deny access.
        Silent return = access granted.
        """
        raise NotImplementedError("Permission check not implemented")


def _make_permission_dependency(action: str, resource: type[Resource]) -> Depends:
    async def dep(request: Request) -> None:
        permission = resource.permissions.get(action)
        if permission is None:
            return
        result = permission(request)
        if inspect.isawaitable(result):
            await result

    return Depends(dep)
