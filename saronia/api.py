import typing

from saronia.client.abc import ABCClient
from saronia.controller import Controller

_SARONIA_CONTROLLER_PATH_ATTR: typing.Final = "__saronia_controller_path__"


def _join_path(base: str, path: str) -> str:
    if not base:
        return path
    if not path:
        return base
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


class API:
    __slots__ = ("path", "controllers", "_client")

    path: str
    controllers: set[type[Controller]]
    _client: ABCClient | None

    def __init__(self, path: str, /) -> None:
        self.path = path
        self.controllers = set()
        self._client = None

    def __call__[T](self, path: str, /) -> typing.Callable[[type[T]], type[T]]:
        def register_controller(x: type[Controller], /) -> type[Controller]:
            setattr(x, "path", path)
            setattr(x, _SARONIA_CONTROLLER_PATH_ATTR, path)
            self.controllers.add(x)
            return x

        return register_controller  # type: ignore

    def build(self, client: ABCClient, /) -> typing.Self:
        self._client = client

        for controller in self.controllers:
            setattr(controller, "client", client)
            original_path = getattr(controller, _SARONIA_CONTROLLER_PATH_ATTR, getattr(controller, "path", ""))
            setattr(controller, "path", _join_path(self.path, original_path))

        return self

    @classmethod
    def endpoint(cls, path: str, /) -> typing.Self:
        return cls(path)

    @property
    def client(self) -> ABCClient:
        if self._client is None:
            raise ValueError(
                "API has no client, need to build via `.build()` with a specific http client.",
            )

        return self._client


__all__ = ("API",)
