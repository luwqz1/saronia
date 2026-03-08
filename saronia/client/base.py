import abc
import platform
import sys
import typing
from contextlib import suppress
from http import HTTPMethod, HTTPStatus

from kungfu import Error, Option, Result
from msgspex import decoder
from msgspex.model import Model

from saronia.__meta__ import __version__
from saronia.client.abc import ABCClient, MultipartFile
from saronia.error import APIError, StatusError, UnknownError

if typing.TYPE_CHECKING:
    from saronia.auth import Auth, AuthComposite

DEFAULT_TIMEOUT: typing.Final = 30.0
DEFAULT_USER_AGENT: typing.Final = "CPython/{py_major}.{py_minor}; ({system}; {platform}) {saronia} {http_client}".format(
    py_major=sys.version_info.major,
    py_minor=sys.version_info.minor,
    system=platform.system() or "Unknown",
    platform=platform.platform(terse=True) or "Unknown",
    saronia=f"saronia/{__version__}",
    http_client="{http_client}",
)


class BaseClient(ABCClient, abc.ABC):
    base_url: str
    headers: dict[str, str]
    query_parameters: dict[str, str]
    cookies: dict[str, str]
    auth_model: Model | None

    def __init__(self, user_agent: str, base_url: str = "") -> None:
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent}
        self.query_parameters = {}
        self.cookies = {}
        self.auth_model = None

    def auth(self, auth_model: Model) -> None:
        self.auth_model = auth_model

    def _to_api_error(
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

    def _apply_auth(
        self,
        auth: "Auth | AuthComposite | None",
        headers: dict[str, str],
        query_params: dict[str, str],
        cookies: dict[str, str],
    ) -> None:
        if auth is None:
            return

        from saronia.auth import AuthComposite, AuthError
        from saronia.security import CookieAPIKey, HeaderAPIKey, HTTPAuthorization, QueryAPIKey

        if isinstance(auth, type):
            if self.auth_model is None:
                raise AuthError(f"Auth {auth.__name__} required but no credentials provided")

            for field_value in self.auth_model.to_dict().values():
                if field_value is not None and isinstance(field_value, auth):
                    auth = field_value
                    break
            else:
                raise AuthError(f"Auth {auth.__name__} not found in auth model")

        if isinstance(auth, AuthComposite):
            match auth.op:
                case "AND":
                    self._apply_auth(auth.left, headers, query_params, cookies)
                    self._apply_auth(auth.right, headers, query_params, cookies)
                case "OR":
                    try:
                        self._apply_auth(auth.left, headers, query_params, cookies)
                        return
                    except AuthError:
                        self._apply_auth(auth.right, headers, query_params, cookies)
                case "NOT":
                    raise AuthError("NOT operator requires combination with other auth")
                case _:
                    typing.assert_never(auth.op)

            return

        match auth:
            case CookieAPIKey():
                cookies.update(auth.mapping)
            case HeaderAPIKey():
                headers.update(auth.mapping)
            case QueryAPIKey():
                query_params.update(auth.mapping)
            case HTTPAuthorization():
                headers.update(auth.header)
            case _:
                raise AuthError(f"Unknown auth type: `{type(auth)}`")

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
        auth: typing.Any = None,
    ) -> Result[typing.Any, APIError[typing.Any]]:
        pass


__all__ = ("BaseClient",)
