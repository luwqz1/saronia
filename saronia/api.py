import typing

from saronia.client.abc import ABCClient
from saronia.controller import Controller

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance

    from saronia.auth import Auth

    type AuthMethod[**P] = typing.Callable[P, DataclassInstance]

_SARONIA_CONTROLLER_PATH_ATTR: typing.Final = "__saronia_controller_path__"
_SARONIA_CONTROLLER_AUTH_ATTR: typing.Final = "__saronia_controller_auth__"


def join_path(base: str, path: str, /) -> str:
    if not base:
        return path

    if not path:
        return base

    return (f"{base.rstrip('/')}/{path.lstrip('/')}".rstrip("/")) or "/"


class API[**P = [], R = None]:
    __slots__ = ("path", "controllers", "_auth_model", "_client")

    path: str
    controllers: set[type[Controller]]
    _auth_model: AuthMethod[P] | None
    _client: ABCClient | None

    def __init__(self, path: str, /) -> None:
        self.path = path
        self.controllers = set()
        self._auth_model = None
        self._client = None

    def __call__[T](self, path: str, /, *, auth: "Auth | type[Auth] | None" = None) -> typing.Callable[[type[T]], type[T]]:
        def register_controller(x: type[Controller], /) -> type[Controller]:
            setattr(x, "path", path)
            setattr(x, _SARONIA_CONTROLLER_PATH_ATTR, path)
            setattr(x, _SARONIA_CONTROLLER_AUTH_ATTR, auth)
            self.controllers.add(x)
            return x

        return register_controller  # type: ignore

    def auth(self, *args: P.args, **kwargs: P.kwargs) -> None:
        if self._auth_model is None:
            raise TypeError(
                "Auth model is not defined, need to bind via `.bind_auth()` with a specific auth model.",
            )

        self.client.auth(self._auth_model(*args, **kwargs))

    def build(self, client: ABCClient, /) -> typing.Self:
        self._client = client

        for controller in self.controllers:
            setattr(controller, "client", client)
            original_path = getattr(controller, _SARONIA_CONTROLLER_PATH_ATTR, getattr(controller, "path", ""))
            setattr(controller, "path", join_path(self.path, original_path))

        return self

    def bind_auth[**Params](self, meth: AuthMethod[Params], /) -> API[Params]:
        self._auth_model = meth  # type: ignore
        return self  # type: ignore

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
