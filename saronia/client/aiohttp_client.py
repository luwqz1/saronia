# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import typing
from http import HTTPMethod, HTTPStatus

from kungfu import Option
from kungfu.library.monad.option import NOTHING
from msgspex import encoder

from saronia.client.abc import ContentType
from saronia.client.base import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, BaseClient, MultipartFile, ResponseHandler

if typing.TYPE_CHECKING:
    import aiohttp


class AiohttpClient(BaseClient):
    def __init__(
        self,
        session: "aiohttp.ClientSession",
        *,
        user_agent: str | None = None,
        request_timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        from aiohttp import __version__

        super().__init__(
            user_agent=user_agent or DEFAULT_USER_AGENT.format(http_client=f"aiohttp/{__version__}"),
        )

        self.session = session
        self.request_timeout = request_timeout

    async def request(
        self,
        path: str,
        method: HTTPMethod,
        *,
        as_result: bool,
        errors: tuple[typing.Any, ...],
        content_type: ContentType,
        response_type: Option[typing.Any],
        json: Option[str | bytes],
        headers: Option[typing.Mapping[str, typing.Any]],
        urlencoded_params: Option[typing.Mapping[str, typing.Any]],
        query_params: Option[typing.Mapping[str, typing.Any]],
        body: Option[typing.Any],
        files: Option[typing.Mapping[str, MultipartFile]],
        response_handler: Option[ResponseHandler],
        auth: typing.Any = None,
    ) -> typing.Any:
        import aiohttp
        import aiohttp.client_exceptions
        import aiohttp.http_exceptions

        status = request_id = None

        try:
            kwargs: dict[str, typing.Any] = {
                "headers": self.headers.copy(),
                "params": self.query_parameters.copy(),
                "cookies": self.cookies.copy(),
            }

            self._apply_auth(auth, kwargs["headers"], kwargs["params"], kwargs["cookies"])

            if headers:
                kwargs["headers"] = {k.title(): v if isinstance(v, str) else encoder.encode(v).strip('"') for k, v in headers.unwrap().items()}

            if query_params:
                kwargs["params"] = {k: v if isinstance(v, str | int | float | bool) else encoder.encode(v).strip('"') for k, v in query_params.unwrap().items()}

            if json:
                json_data = json.unwrap()
                kwargs["headers"]["Content-Type"] = "application/json"
                kwargs["data"] = json_data if isinstance(json_data, bytes) else json_data.encode()
            elif body is not NOTHING:
                kwargs["data"] = body.unwrap()
            elif urlencoded_params and not files:
                kwargs["data"] = dict(urlencoded_params.unwrap())
            elif files:
                form_data = aiohttp.FormData(quote_fields=False)

                for k, v in urlencoded_params.unwrap().items():
                    form_data.add_field(k, v if isinstance(v, str) else encoder.encode(v).strip('"'))

                for field_name, file_info in files.unwrap().items():
                    form_data.add_field(
                        field_name,
                        file_info.content,
                        filename=file_info.name,
                        content_type=file_info.mime or "application/octet-stream",
                    )

                kwargs["data"] = form_data

            async with self.session.request(method.value, path, **kwargs) as response:
                status = HTTPStatus(response.status)
                payload = await response.read()

                if status.is_success:
                    return self._validate_response(
                        payload if content_type != "text" else await response.text(),
                        status,
                        content_type=content_type,
                        response_type=response_type.unwrap_or(typing.Any),
                        response_handler=response_handler.unwrap_or(self.response_handler),
                        as_result=as_result,
                    )

                self._raise_error(
                    path,
                    method,
                    status=status,
                    payload=payload,
                    errors=errors,
                    request_id=(request_id := response.headers.get("X-Request-ID") or response.headers.get("Request-ID")),
                )
        except BaseException as exception:
            return self._handle_error(
                status,
                method,
                path,
                request_id,
                exception,
                TimeoutError,
                aiohttp.client_exceptions.ClientError,
                aiohttp.http_exceptions.HttpProcessingError,
                as_result=as_result,
            )


__all__ = ("AiohttpClient",)
