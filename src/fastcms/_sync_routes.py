from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from fastcms.dependencies import make_filter_dep, make_permission_dep
from fastcms.resource import Resource
from fastcms.service import CrudService

type AnySchema = type[BaseModel]


def build_sync_routes(
    router: APIRouter,
    resource: Resource,
    service: CrudService,
    get_session,
    schemas: tuple[AnySchema, AnySchema, AnySchema],
) -> None:
    ReadSchema, CreateSchema, UpdateSchema = schemas
    filter_dep = make_filter_dep(resource)

    if filter_dep is not None:
        @router.get("/", response_model=list[ReadSchema], dependencies=[make_permission_dep("list", resource)])
        def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session), filters=filter_dep):
            return service.get_list(session, offset, limit, filters=filters)
    else:
        @router.get("/", response_model=list[ReadSchema], dependencies=[make_permission_dep("list", resource)])
        def get_list(limit: int = 20, offset: int = 0, session=Depends(get_session)):  # type: ignore[misc]
            return service.get_list(session, offset, limit)

    @router.get("/{id}", response_model=ReadSchema, dependencies=[make_permission_dep("retrieve", resource)])
    def get_item(id: int, session=Depends(get_session)):
        obj = service.get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return obj

    @router.post("/", response_model=ReadSchema, status_code=201, dependencies=[make_permission_dep("create", resource)])
    def create_item(request: Request, data: CreateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        payload = resource.before_create(data.model_dump(), session, request)  # type: ignore[union-attr]
        obj = service.create(session, payload)
        resource.after_create(obj, session, request)
        return obj

    @router.patch("/{id}", response_model=ReadSchema, dependencies=[make_permission_dep("update", resource)])
    def update_item(id: int, request: Request, data: UpdateSchema, session=Depends(get_session)):  # type: ignore[valid-type]
        obj = service.get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        patch = data.model_dump(exclude_unset=True)  # type: ignore[union-attr]
        patch = resource.before_update(obj, patch, session, request)
        updated = service.update(session, id, patch)
        if updated is None:
            raise HTTPException(status_code=404, detail="Item not found")
        resource.after_update(updated, session, request)
        return updated

    @router.delete("/{id}", status_code=204, dependencies=[make_permission_dep("delete", resource)])
    def delete_item(id: int, request: Request, session=Depends(get_session)):
        obj = service.get_one(session, id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Item not found")
        resource.before_delete(obj, session, request)
        service.delete(session, id)
        resource.after_delete(obj, session, request)
