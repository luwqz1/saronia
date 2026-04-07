# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import datetime
import typing
from http import HTTPMethod, HTTPStatus
from io import IOBase

from kungfu import Option
from msgspex import encoder

from saronia.client.abc import ContentType
from saronia.client.base import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, BaseClient, MultipartFile, ResponseHandler

if typing.TYPE_CHECKING:
    import wreq


class RnetClient(BaseClient):
    def __init__(
        self,
        client: "wreq.Client",
        base_url: str = "",
        *,
        user_agent: str | None = None,
        request_timeout: int | float | datetime.timedelta = DEFAULT_TIMEOUT,
        default_headers: bool = False,
    ) -> None:
        super().__init__(
            user_agent=user_agent or DEFAULT_USER_AGENT.format(http_client="wreq"),
            base_url=base_url.rstrip("/"),
        )

        self.client = client
        self.default_headers = default_headers
        self.request_timeout = datetime.timedelta(seconds=request_timeout) if isinstance(request_timeout, int | float) else request_timeout

    async def request(
        self,
        path: str,
        method: HTTPMethod,
        *,
        as_result: bool = False,
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
        import wreq
        import wreq.exceptions

        url = f"{self.base_url}{path}" if self.base_url else path
        status = request_id = None

        try:
            kwargs: dict[str, typing.Any] = {
                "headers": self.headers.copy(),
                "query": self.query_parameters.copy(),
                "cookies": self.cookies.copy(),
            }

            self._apply_auth(auth, kwargs["headers"], kwargs["query"], kwargs["cookies"])

            if headers:
                kwargs["headers"] |= {k.title(): v if isinstance(v, str) else encoder.encode(v).strip('"') for k, v in headers.unwrap().items()}

            if query_params:
                kwargs["query"] |= {k: v if isinstance(v, str | int | float | bool) else encoder.encode(v).strip('"') for k, v in query_params.unwrap().items()}

            if json:
                json_data = json.unwrap()
                kwargs["headers"]["Content-Type"] = "application/json"
                kwargs["body"] = json_data if isinstance(json_data, bytes) else json_data.encode()
            elif body:
                kwargs["body"] = body.unwrap()
            elif urlencoded_params and not files:
                kwargs["form"] = {
                    k: v if isinstance(v, str | int | bool | float) else encoder.encode(v).strip('"') for k, v in urlencoded_params.unwrap().items()
                }
            elif files:
                parts: list[wreq.Part] = []

                for k, v in urlencoded_params.unwrap().items():
                    parts.append(wreq.Part(k, v if isinstance(v, str) else encoder.encode(v).strip('"')))

                for field_name, file_info in files.unwrap().items():
                    content = file_info.content.read() if isinstance(file_info.content, typing.IO | IOBase) else file_info.content
                    parts.append(
                        wreq.Part(
                            name=field_name,
                            value=content,
                            filename=file_info.name,
                            mime=file_info.mime,
                        ),
                    )

                kwargs["multipart"] = wreq.Multipart(*parts)

            response = await self.client.request(
                getattr(wreq.Method, method.name),
                url,
                default_headers=self.default_headers,
                timeout=self.request_timeout,
                **kwargs,
            )
            request_id = None if not (req_id := response.headers.get("x-request-id") or response.headers.get("request-id")) else req_id.decode()
            status = HTTPStatus(response.status.as_int())

            if status.is_success:
                return self._validate_response(
                    await response.bytes() if content_type != "text" else await response.text(),
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
                payload=await response.bytes(),
                errors=errors,
                request_id=request_id,
            )
        except BaseException as exception:
            return self._handle_error(
                status,
                method,
                path,
                request_id,
                exception,
                wreq.exceptions.ConnectionError,
                wreq.exceptions.ConnectionResetError,
                wreq.exceptions.ProxyConnectionError,
                wreq.exceptions.RequestError,
                wreq.exceptions.TimeoutError,
                wreq.exceptions.RustPanic,
                wreq.exceptions.TlsError,
                wreq.exceptions.BodyError,
                wreq.exceptions.RedirectError,
                as_result=as_result,
            )


__all__ = ("RnetClient",)
