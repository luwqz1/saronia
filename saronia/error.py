from __future__ import annotations

import dataclasses
import typing
from http import HTTPMethod, HTTPStatus
from reprlib import recursive_repr

if typing.TYPE_CHECKING:
    from saronia.auth import AuthError


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


class APIError[E = typing.Never](Exception):
    """Represents an API error response.

    Attributes:
        error: The parsed error object (can be a Model, dict, bytes, or None)
        method: The HTTP method that was used
        status: The HTTP status code returned
        path: The request path (optional)
        request_id: Request ID for tracing (optional)

    """

    error: E | AuthError | NetworkError | UnknownError

    __match_args__ = ("error", "method", "status", "path", "request_id")

    def __init__(
        self,
        error: E,
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

    @property
    def is_client_error(self) -> bool:
        """Returns True if status is 4xx."""
        return 400 <= self.status.value < 500

    @property
    def is_server_error(self) -> bool:
        """Returns True if status is 5xx."""
        return 500 <= self.status.value < 600


__all__ = ("APIError", "NetworkError", "StatusError", "UnknownError")
