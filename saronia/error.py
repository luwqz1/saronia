from __future__ import annotations

import dataclasses
import typing
from http import HTTPMethod, HTTPStatus
from reprlib import recursive_repr

if typing.TYPE_CHECKING:
    from saronia.auth import AuthError

type BaseError = AuthError | STATUS_ERROR | NetworkError | UnknownError

STATUS_ERROR: typing.Final = type("StatusError", (Exception,), {"__module__": __name__})


def status(code: int, description: str = "", /) -> tuple[HTTPStatus, str]:
    http_status = HTTPStatus(code)
    return (http_status, description or http_status.description)


def status_error(code: int, description: str = "", /) -> BaseStatusError:
    return StatusError[status(code, description)]  # type: ignore


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


class BaseStatusError:
    _errors: dict[HTTPStatus, STATUS_ERROR]

    @classmethod
    def get_status_error(cls, status: HTTPStatus, /) -> STATUS_ERROR | None:
        return cls._errors.get(status)


class StatusError(STATUS_ERROR):
    if typing.TYPE_CHECKING:
        STATUSES: typing.ClassVar[tuple[HTTPStatus, ...]]

    def __class_getitem__(
        cls,
        statuses: HTTPStatus | tuple[HTTPStatus, ...] | tuple[tuple[HTTPStatus, str], ...],
        /,
    ) -> typing.Any:
        statuses = (statuses,) if not isinstance(statuses, tuple) else statuses

        if statuses and (isinstance(statuses[0], tuple)) or (len(statuses) == 2 and isinstance(statuses[0], HTTPStatus) and isinstance(statuses[1], str)):
            statuses_with_descriptions = ((statuses[0], statuses[1]),) if len(statuses) == 2 and not isinstance(statuses[0], tuple) else statuses
            return type(
                cls.__name__,
                (BaseStatusError,),
                {
                    "_errors": {
                        http_status: StatusError(description)
                        for http_status, description in typing.cast("tuple[tuple[HTTPStatus, str]]", statuses_with_descriptions)
                    },
                },
            )

        return type(cls.__name__ + "Mixin", (), {"STATUSES": statuses, "__module__": cls.__module__})


class APIError[Error = typing.Never](Exception):
    """Represents an API error response.

    Attributes:
        error: The parsed error object
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


__all__ = ("APIError", "NetworkError", "StatusError", "UnknownError", "status", "status_error")
