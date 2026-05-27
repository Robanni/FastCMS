from fastapi import APIRouter

from fastcms.resource import Resource
from fastcms.schema import SchemaFactory
from fastcms.service import CrudService
from fastcms._sync_routes import build_sync_routes
from fastcms._async_routes import build_async_routes


def create_router(resource: type[Resource], get_session) -> APIRouter:
    model = resource.model
    prefix = resource.prefix or f"/{model.__name__.lower()}s"
    tags = resource.tags or [model.__name__]

    service = CrudService(model, get_session)
    schemas = SchemaFactory.create_schema(model)

    router = APIRouter(prefix=prefix, tags=tags)

    if service.async_mode:
        build_async_routes(router, resource, service, get_session, schemas)
    else:
        build_sync_routes(router, resource, service, get_session, schemas)

    return router
