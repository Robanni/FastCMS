from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fastcms.resource import Resource
from fastcms.schema import SchemaFactory
from fastcms.service import CrudService

type AnySchema = type[BaseModel]


def create_router(resource: type[Resource], get_session) -> APIRouter:
    model = resource.model
    prefix = resource.prefix or f"/{model.__name__.lower()}s"
    tags = resource.tags or [model.__name__]

    service = CrudService(model, get_session)
    ReadSchema, CreateSchema, UpdateSchema = SchemaFactory.create_schema(model)

    router = APIRouter(prefix=prefix, tags=tags)

    if service.async_mode:
        _build_async_routes(router, service, get_session, ReadSchema, CreateSchema, UpdateSchema)
    else:
        _build_sync_routes(router, service, get_session, ReadSchema, CreateSchema, UpdateSchema)

    return router


def _build_sync_routes(
    router: APIRouter,
    service: CrudService,
    get_session,
    ReadSchema: AnySchema,
    CreateSchema: AnySchema,
    UpdateSchema: AnySchema,
) -> None:
    @router.get("/", response_model=list[ReadSchema])
    def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session)):
        return service.get_list(session, offset, limit)

    @router.get("/{id}", response_model=ReadSchema)
    def get_item(id: int, session=Depends(get_session)):
        obj = service.get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.post("/", response_model=ReadSchema, status_code=201)
    def create_item(data: CreateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        return service.create(session, data.model_dump())  # type: ignore[union-attr]

    @router.patch("/{id}", response_model=ReadSchema)
    def update_item(id: int, data: UpdateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        obj = service.update(session, id, data.model_dump(exclude_unset=True))  # type: ignore[union-attr]
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.delete("/{id}", status_code=204)
    def delete_item(id: int, session=Depends(get_session)):
        if not service.delete(session, id):
            raise HTTPException(status_code=404, detail="Item not found")


def _build_async_routes(
    router: APIRouter,
    service: CrudService,
    get_session,
    ReadSchema: AnySchema,
    CreateSchema: AnySchema,
    UpdateSchema: AnySchema,
) -> None:
    @router.get("/", response_model=list[ReadSchema])
    async def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session)):
        return await service.async_get_list(session, offset, limit)

    @router.get("/{id}", response_model=ReadSchema)
    async def get_item(id: int, session=Depends(get_session)):
        obj = await service.async_get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.post("/", response_model=ReadSchema, status_code=201)
    async def create_item(data: CreateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        return await service.async_create(session, data.model_dump())  # type: ignore[union-attr]

    @router.patch("/{id}", response_model=ReadSchema)
    async def update_item(id: int, data: UpdateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        obj = await service.async_update(session, id, data.model_dump(exclude_unset=True))  # type: ignore[union-attr]
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.delete("/{id}", status_code=204)
    async def delete_item(id: int, session=Depends(get_session)):
        if not await service.async_delete(session, id):
            raise HTTPException(status_code=404, detail="Item not found")
