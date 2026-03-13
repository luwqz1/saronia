from __future__ import annotations

import dataclasses
import typing
from http import HTTPMethod, HTTPStatus
from reprlib import recursive_repr

if typing.TYPE_CHECKING:
    from saronia.auth import AuthError

type BaseError = AuthError | NetworkError | UnknownError


@dataclasses.dataclass(frozen=True, slots=True)
class UnknownError:
    message: bytes
    orig_error: BaseException | None = None


class NetworkError(Exception):
    """Raised when a network-level error occurs (connection failed, timeout, etc)."""

    __match_args__ = ("message", "original_error")

    def __init__(self, message: str, original_error: BaseException | None = None) -> None:
        self.message = message
        self.original_error = original_error
        super().__init__(message)

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message}: {self.original_error}"
        return self.message


class StatusError:
    """Usage:
    ```python
    class NotFoundError(Model, StatusError[HTTPStatus.NOT_FOUND]):
        message: str

    class ValidationError(Model, StatusError[HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY]):
        message: str
        details: dict[str, list[str]]
    ```
    """

    if typing.TYPE_CHECKING:
        STATUSES: typing.ClassVar[tuple[HTTPStatus, ...]]
    else:
        STATUSES = ()

    def __class_getitem__(cls, statuses: HTTPStatus | tuple[HTTPStatus, ...], /) -> typing.Any:
        return type(
            cls.__name__,
            (),
            {
                "STATUSES": (statuses,) if not isinstance(statuses, tuple) else statuses,
                "__module__": cls.__module__,
            },
        )


class APIError[Error = typing.Never](Exception):
    """Represents an API error response.

    Attributes:
        error: The parsed error object (can be a Model, dict, bytes, or None)
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
        self.error = error
        self.method = method
        self.status = status
        self.path = path
        self.request_id = request_id
        super().__init__()

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


__all__ = ("APIError", "NetworkError", "StatusError", "UnknownError")
