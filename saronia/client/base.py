import abc
import platform
import sys
import typing
from contextlib import suppress
from http import HTTPMethod, HTTPStatus

from kungfu import Error, Option, Result
from msgspex import decoder

from saronia.__meta__ import __version__
from saronia.client.abc import ABCClient, MultipartFile
from saronia.error import APIError, StatusError, UnknownError
from saronia.security import APIKey, CookieAPIKey, HeaderAPIKey, HTTPAuthorization, QueryAPIKey

type AuthMethod = APIKey | HTTPAuthorization

DEFAULT_TIMEOUT: typing.Final = 30.0
DEFAULT_USER_AGENT: typing.Final = "CPython/{py_major}.{py_minor}; ({system}; {platform}) {saronia} {http_client}".format(
    py_major=sys.version_info.major,
    py_minor=sys.version_info.minor,
    system=platform.system() or "Unknown",
    platform=platform.platform(terse=True) or "Unknown",
    saronia=f"saronia/{__version__}",
    http_client="{http_client}",
)


class BaseClient(ABCClient[AuthMethod], abc.ABC):
    base_url: str
    headers: dict[str, str]
    query_parameters: dict[str, str]
    cookies: dict[str, str]

    def __init__(self, user_agent: str, base_url: str = "") -> None:
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent}
        self.query_parameters = {}
        self.cookies = {}

    def auth_security(self, auth_method: AuthMethod) -> None:
        match auth_method:
            case CookieAPIKey():
                self.cookies.update(auth_method.mapping)
            case HeaderAPIKey():
                self.headers.update(auth_method.mapping)
            case QueryAPIKey():
                self.query_parameters.update(auth_method.mapping)
            case HTTPAuthorization():
                self.headers.update(auth_method.header)
            case _:
                raise NotImplementedError(f"No implementation found for `{auth_method!r}`")

    def to_api_error(
        self,
        path: str,
        method: HTTPMethod,
        status: HTTPStatus,
        payload: bytes,
        errors: tuple[typing.Any, ...],
        request_id: str | None = None,
    ) -> Error[APIError[typing.Any]]:
        if payload:
            for error_type in errors:
                if isinstance(error_type, StatusError) and status not in error_type.STATUSES:
                    continue

                with suppress(Exception):
                    error_obj = decoder.decode(payload, type=error_type)
                    return Error(APIError(error_obj, method, status, path=path, request_id=request_id))

        return Error(APIError(UnknownError(payload), method, status, path=path, request_id=request_id))

    @abc.abstractmethod
    async def request(
        self,
        path: str,
        method: HTTPMethod,
        *,
        errors: tuple[typing.Any, ...],
        response_type: Option[typing.Any],
        json: Option[str | bytes],
        headers: Option[typing.Mapping[str, typing.Any]],
        urlencoded_params: Option[typing.Mapping[str, typing.Any]],
        query_params: Option[typing.Mapping[str, typing.Any]],
        body: Option[typing.Any],
        files: Option[typing.Mapping[str, MultipartFile]],
    ) -> Result[typing.Any, APIError[typing.Any]]:
        pass


__all__ = ("BaseClient",)
