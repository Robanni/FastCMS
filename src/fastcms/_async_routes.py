from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fastcms.dependencies import make_filter_dep, make_permission_dep
from fastcms.resource import Resource
from fastcms.service import CrudService

type AnySchema = type[BaseModel]


def build_async_routes(
    router: APIRouter,
    resource: type[Resource],
    service: CrudService,
    get_session,
    schemas: tuple[AnySchema, AnySchema, AnySchema],
) -> None:
    ReadSchema, CreateSchema, UpdateSchema = schemas
    filter_dep = make_filter_dep(resource)

    if filter_dep is not None:
        @router.get("/", response_model=list[ReadSchema], dependencies=[make_permission_dep("list", resource)])
        async def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session), filters=filter_dep):
            return await service.async_get_list(session, offset, limit, filters=filters)
    else:
        @router.get("/", response_model=list[ReadSchema], dependencies=[make_permission_dep("list", resource)])
        async def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session)):  # type: ignore[misc]
            return await service.async_get_list(session, offset, limit)

    @router.get("/{id}", response_model=ReadSchema, dependencies=[make_permission_dep("retrieve", resource)])
    async def get_item(id: int, session=Depends(get_session)):
        obj = await service.async_get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.post("/", response_model=ReadSchema, status_code=201, dependencies=[make_permission_dep("create", resource)])
    async def create_item(data: CreateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        return await service.async_create(session, data.model_dump())  # type: ignore[union-attr]

    @router.patch("/{id}", response_model=ReadSchema, dependencies=[make_permission_dep("update", resource)])
    async def update_item(id: int, data: UpdateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        obj = await service.async_update(session, id, data.model_dump(exclude_unset=True))  # type: ignore[union-attr]
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.delete("/{id}", status_code=204, dependencies=[make_permission_dep("delete", resource)])
    async def delete_item(id: int, session=Depends(get_session)):
        if await service.async_delete(session, id) is None:
            raise HTTPException(status_code=404, detail="Item not found")
