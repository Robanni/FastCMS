from __future__ import annotations

from fastapi import Request


class BaseGuard:
    async def __call__(self, request: Request) -> None:
        """
        Raise HTTPException to block. Silent return = pass.
        """
        raise NotImplementedError("Guard check not implemented")
