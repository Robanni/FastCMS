import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from fastcms.dependencies import (
    make_filter_dep,
    make_guard_deps,
    make_permission_dep,
    make_sort_dep,
)
from fastcms.resource import Action, Resource
from fastcms.service import CrudService

type AnySchema = type[BaseModel]


async def _call(hook, *args):
    result = hook(*args)
    if inspect.isawaitable(result):
        return await result
    return result


def build_async_routes(
    router: APIRouter,
    resource: Resource,
    service: CrudService,
    get_session,
    schemas: tuple[AnySchema, AnySchema, AnySchema],
) -> None:
    ReadSchema, CreateSchema, UpdateSchema = schemas
    filter_dep = make_filter_dep(resource)
    sort_dep = make_sort_dep(resource)

    if Action.LIST in resource.actions:
        if filter_dep is not None and sort_dep is not None:

            @router.get(
                "/",
                response_model=list[ReadSchema],
                dependencies=[
                    make_permission_dep("list", resource),
                    *make_guard_deps(Action.LIST, resource),
                ],
            )
            async def get_list(
                limit: int = 20,
                offset: int = 0,
                session=Depends(get_session),
                filters=filter_dep,
                sort=sort_dep,
            ):
                return await service.async_get_list(
                    session, offset=offset, limit=limit, filters=filters, sort=sort
                )
        elif filter_dep is not None:

            @router.get(
                "/",
                response_model=list[ReadSchema],
                dependencies=[
                    make_permission_dep("list", resource),
                    *make_guard_deps(Action.LIST, resource),
                ],
            )
            async def get_list(
                limit: int = 20,
                offset: int = 0,
                session=Depends(get_session),
                filters=filter_dep,
            ):  # type: ignore[misc]
                return await service.async_get_list(
                    session, offset=offset, limit=limit, filters=filters
                )
        elif sort_dep is not None:

            @router.get(
                "/",
                response_model=list[ReadSchema],
                dependencies=[
                    make_permission_dep("list", resource),
                    *make_guard_deps(Action.LIST, resource),
                ],
            )
            async def get_list(
                limit: int = 20,
                offset: int = 0,
                session=Depends(get_session),
                sort=sort_dep,
            ):  # type: ignore[misc]
                return await service.async_get_list(
                    session, offset=offset, limit=limit, sort=sort
                )
        else:

            @router.get(
                "/",
                response_model=list[ReadSchema],
                dependencies=[
                    make_permission_dep("list", resource),
                    *make_guard_deps(Action.LIST, resource),
                ],
            )
            async def get_list(
                limit: int = 20, offset: int = 0, session=Depends(get_session)
            ):  # type: ignore[misc]
                return await service.async_get_list(session, offset=offset, limit=limit)

    if Action.RETRIEVE in resource.actions:

        @router.get(
            "/{id}",
            response_model=ReadSchema,
            dependencies=[
                make_permission_dep("retrieve", resource),
                *make_guard_deps(Action.RETRIEVE, resource),
            ],
        )
        async def get_item(id: int, session=Depends(get_session)):
            obj = await service.async_get_one(session, id)
            if obj is None:
                raise HTTPException(status_code=404, detail="Item not found")
            return obj

    if Action.CREATE in resource.actions:

        @router.post(
            "/",
            response_model=ReadSchema,
            status_code=201,
            dependencies=[
                make_permission_dep("create", resource),
                *make_guard_deps(Action.CREATE, resource),
            ],
        )
        async def create_item(
            request: Request, data: CreateSchema, session=Depends(get_session)
        ):  # type: ignore[valid-type]
            payload = await _call(
                resource.before_create, data.model_dump(), session, request
            )  # type: ignore[union-attr]
            if payload is None:
                raise ValueError(
                    f"{resource.__class__.__name__}.before_create must return a dict, got None"
                )
            obj = await service.async_create(session, payload)
            await _call(resource.after_create, obj, session, request)
            return obj

    if Action.UPDATE in resource.actions:

        @router.patch(
            "/{id}",
            response_model=ReadSchema,
            dependencies=[
                make_permission_dep("update", resource),
                *make_guard_deps(Action.UPDATE, resource),
            ],
        )
        async def update_item(
            id: int, request: Request, data: UpdateSchema, session=Depends(get_session)
        ):  # type: ignore[valid-type]
            obj = await service.async_get_one(session, id)
            if obj is None:
                raise HTTPException(status_code=404, detail="Item not found")
            patch = data.model_dump(exclude_unset=True)  # type: ignore[union-attr]
            patch = await _call(resource.before_update, obj, patch, session, request)
            if patch is None:
                raise ValueError(
                    f"{resource.__class__.__name__}.before_update must return a dict, got None"
                )
            updated = await service.async_update(session, obj, patch)
            await _call(resource.after_update, updated, session, request)
            return updated

    if Action.DELETE in resource.actions:

        @router.delete(
            "/{id}",
            status_code=204,
            dependencies=[
                make_permission_dep("delete", resource),
                *make_guard_deps(Action.DELETE, resource),
            ],
        )
        async def delete_item(id: int, request: Request, session=Depends(get_session)):
            obj = await service.async_get_one(session, id)
            if obj is None:
                raise HTTPException(status_code=404, detail="Item not found")
            await _call(resource.before_delete, obj, session, request)
            deleted_data = await service.async_delete(session, obj)
            await _call(resource.after_delete, deleted_data, session, request)
