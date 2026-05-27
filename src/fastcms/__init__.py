from fastapi import FastAPI
from fastcms.filter import Filter
from fastcms.resource import Resource
from fastcms.registry import registry
from fastcms.router import create_router


def setup(app: FastAPI, resources: list[type[Resource]], get_session) -> None:
    for resource in resources:
        registry.register(resource)
        router = create_router(resource, get_session)
        app.include_router(router)


__all__ = ["Resource", "Filter", "setup", "registry"]
