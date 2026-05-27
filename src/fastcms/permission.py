from __future__ import annotations

from fastapi import Request


class BasePermission:
    async def __call__(self, request: Request) -> None:
        """
        Raise HTTPException to deny access.
        Silent return = access granted.
        """
        raise NotImplementedError("Permission check not implemented")
