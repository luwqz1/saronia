import abc
import dataclasses
import platform
import sys
import typing
from contextlib import suppress
from http import HTTPMethod, HTTPStatus

from kungfu import Error, Ok, Option
from msgspex import decoder

from saronia.__meta__ import __version__
from saronia.auth import AuthError
from saronia.client.abc import ABCClient, MultipartFile
from saronia.error import STATUS_ERROR, APIError, BaseStatusError, NetworkError, UnknownError

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance

    from saronia.auth import Auth, AuthComposite

_NONE_TYPES: typing.Final = frozenset((None, type(None)))
_SENTINEL: typing.Final = object()
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
    auth_model: DataclassInstance | None

    def __init__(self, user_agent: str, base_url: str = "") -> None:
        self.base_url = base_url
        self.headers = {"User-Agent": user_agent}
        self.query_parameters = {}
        self.cookies = {}
        self.auth_model = None

    def auth(self, auth_model: DataclassInstance) -> None:
        self.auth_model = auth_model

    @abc.abstractmethod
    async def request(
        self,
        path: str,
        method: HTTPMethod,
        *,
        as_result: bool,
        errors: tuple[typing.Any, ...],
        response_type: Option[typing.Any],
        json: Option[str | bytes],
        headers: Option[typing.Mapping[str, typing.Any]],
        urlencoded_params: Option[typing.Mapping[str, typing.Any]],
        query_params: Option[typing.Mapping[str, typing.Any]],
        body: Option[typing.Any],
        files: Option[typing.Mapping[str, MultipartFile]],
        auth: typing.Any = None,
    ) -> typing.Any:
        pass

    def _validate_response(
        self,
        payload: bytes,
        response_type: typing.Any,
        as_result: bool = False,
    ) -> typing.Any:
        response = None if response_type in _NONE_TYPES else decoder.decode(payload, type=response_type)
        return Ok(response) if as_result else response

    def _handle_error(
        self,
        status: HTTPStatus | None,
        method: HTTPMethod,
        path: str,
        request_id: str | None,
        exception: BaseException,
        /,
        *http_errors: type[BaseException],
        as_result: bool = False,
    ) -> Error[APIError[typing.Any]]:
        api_error_kwargs: dict[str, typing.Any] = dict(
            method=method,
            path=path,
            request_id=request_id,
        )

        if isinstance(exception, http_errors):
            error = APIError(
                error=NetworkError("Network issue", exception),
                status=status or HTTPStatus.BAD_REQUEST,
                **api_error_kwargs,
            )

        elif isinstance(exception, (AuthError, STATUS_ERROR)):
            error = APIError(
                error=exception,
                status=status or HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED,
                **api_error_kwargs,
            )

        elif isinstance(exception, APIError):
            error = exception  # type: ignore

        else:
            error = APIError(
                error=UnknownError(b"", exception),
                status=status or HTTPStatus.BAD_REQUEST,
                **api_error_kwargs,
            )

        if as_result:
            return Error(error)

        raise error

    def _raise_error(
        self,
        path: str,
        method: HTTPMethod,
        status: HTTPStatus,
        payload: bytes,
        errors: tuple[typing.Any, ...],
        request_id: str | None = None,
    ) -> typing.NoReturn:
        for error_type in errors:
            if isinstance(error_type, type) and issubclass(error_type, BaseStatusError):
                status_error = error_type.get_status_error(status)

                if status_error is not None:
                    raise status_error

                continue

            if payload:
                statuses = getattr(error_type, "STATUSES", ())

                if statuses and status not in statuses:
                    continue

                error_obj = _SENTINEL

                with suppress(Exception):
                    error_obj = decoder.decode(payload, type=error_type)

                if error_obj is not _SENTINEL:
                    raise APIError(error_obj, method, status, path=path, request_id=request_id)

        raise APIError(UnknownError(payload), method, status, path=path, request_id=request_id)

    def _apply_auth(
        self,
        auth: Auth | AuthComposite | None,
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
                raise AuthError(f"Auth `{auth.__name__}` required but no credentials provided")

            for field in dataclasses.fields(self.auth_model):
                field_value = getattr(self.auth_model, field.name)
                if field_value is not None and type(field_value) is auth:
                    auth = field_value
                    break
            else:
                raise AuthError(f"Auth `{auth.__name__}` is not defined in `{self.auth_model.__class__.__name__}`")

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


__all__ = ("BaseClient",)
