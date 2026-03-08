import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from saronia.security import CookieAPIKey, HeaderAPIKey, HTTPAuthorization, QueryAPIKey

    type Auth = typing.Union[HTTPAuthorization, HeaderAPIKey, QueryAPIKey, CookieAPIKey, AuthComposite, type]


@dataclass(frozen=True, slots=True)
class AuthComposite:
    op: typing.Literal["AND", "OR", "NOT"]
    left: typing.Any
    right: typing.Any

    def __or__(self, other: typing.Any) -> "AuthComposite":
        return AuthComposite("OR", self, other)

    def __and__(self, other: typing.Any) -> "AuthComposite":
        return AuthComposite("AND", self, other)

    def __invert__(self) -> "AuthComposite":
        return AuthComposite("NOT", self, None)


class AuthCompositeMeta(type):
    if not typing.TYPE_CHECKING:

        def __or__(cls, other: typing.Any, /) -> AuthComposite:
            return AuthComposite("OR", cls, other)

    def __and__(cls, other: typing.Any) -> AuthComposite:
        return AuthComposite("AND", cls, other)

    def __invert__(cls) -> AuthComposite:
        return AuthComposite("NOT", cls, None)


class AuthError(Exception):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


__all__ = ("AuthComposite", "AuthCompositeMeta", "AuthError")
