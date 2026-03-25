from __future__ import annotations

import typing
from http import HTTPMethod, HTTPStatus
from reprlib import recursive_repr

if typing.TYPE_CHECKING:
    from msgspec import ValidationError

    from saronia.auth import AuthError

    type BaseError = AuthError | ValidationError | NetworkError | UnknownError | UncaughtError


class ModelStatusError:
    if typing.TYPE_CHECKING:
        STATUSES: typing.Final[tuple[HTTPStatus, ...]] = ()

    def __class_getitem__(cls, items: HTTPStatus | tuple[HTTPStatus, ...], /) -> typing.Any:
        return type(cls.__name__ + "Mixin", (), {"STATUSES": (items,) if not isinstance(items, tuple) else items, "__module__": cls.__module__})


class StatusError(Exception):
    description: typing.ClassVar[str]
    status: typing.ClassVar[HTTPStatus]
    error: typing.ClassVar[typing.Self]

    def __init__(self, description: str, /) -> None:
        super().__init__(description)

    def __init_subclass__(cls) -> None:
        cls.error = cls(cls.description)

    def __class_getitem__(cls, item: typing.Any, /) -> typing.Any:
        if not isinstance(item, int):
            raise ValueError(f"Excepted value of `int` type, but value of `{type(item).__name__}` type were given.")

        status = HTTPStatus(item)
        description = cls.__doc__ or status.description
        return type(
            cls.__name__,
            (StatusError,),
            dict(description=description, status=status),
        )


class NetworkError(Exception):
    __match_args__ = ("network_exception",)

    def __init__(self, network_exception: BaseException) -> None:
        super().__init__()

        self.network_exception = network_exception

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}: There was a network issue of {}: {}".format(
            type(self).__name__,
            type(self.network_exception).__name__,
            repr(self.network_exception),
        )


class UncaughtError(Exception):
    __match_args__ = ("uncaught_exception",)

    def __init__(self, uncaught_exception: BaseException | None = None) -> None:
        super().__init__(uncaught_exception)

        self.uncaught_exception = uncaught_exception


class UnknownError(Exception):
    __match_args__ = ("status", "payload")

    def __init__(self, status: HTTPStatus, payload: bytes = b"") -> None:
        super().__init__()

        self.status = status
        self.payload = payload

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"Unknown error with status code `{self.status.value}`, payload: {self.payload!r}"


class APIError[Error = typing.Never](Exception):
    """Represents an API error response.

    Attributes:
        error: The error
        method: The HTTP method that was used
        status: The HTTP status code returned
        path: The request path (optional)
        request_id: Request ID for tracing (optional)

    """

    __match_args__ = ("error", "method", "status", "path", "request_id")

    error: Error | BaseError

    def __init__(
        self,
        error: Error | BaseError,
        method: HTTPMethod,
        status: HTTPStatus,
        *,
        path: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__()

        self.error = error
        self.method = method
        self.status = status
        self.path = path
        self.request_id = request_id

    def __str__(self) -> str:
        return self.__repr__()

    @recursive_repr()
    def __repr__(self) -> str:
        parts = [f"{type(self).__name__} [{self.status.value}] ({self.status.phrase})"]

        if self.path:
            parts.append(f"path={self.path}")

        if self.request_id:
            parts.append(f"request_id={self.request_id}")

        parts.append(f"error={self.error!r}")
        return f"<{' '.join(parts)}>"


__all__ = ("APIError", "ModelStatusError", "NetworkError", "StatusError", "UncaughtError", "UnknownError")
