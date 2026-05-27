from fastcms.resource import Resource


class ResourceRegistry:
    def __init__(self):
        self._resources: list[type[Resource]] = []

    def register(self, resource: type[Resource]) -> None:
        if resource in self._resources:
            raise ValueError(f"Resource {resource.__name__} is already registered")
        self._resources.append(resource)

    def all(self) -> list[type[Resource]]:
        return self._resources


registry = ResourceRegistry()
