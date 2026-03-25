# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import datetime
import typing
from http import HTTPMethod, HTTPStatus
from io import IOBase

from kungfu import Option
from msgspex import encoder

from saronia.client.base import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, BaseClient, MultipartFile

if typing.TYPE_CHECKING:
    import rnet


class RnetClient(BaseClient):
    def __init__(
        self,
        client: "rnet.Client",
        base_url: str = "",
        *,
        user_agent: str | None = None,
        request_timeout: int | float | datetime.timedelta = DEFAULT_TIMEOUT,
        default_headers: bool = False,
    ) -> None:
        super().__init__(
            user_agent=user_agent or DEFAULT_USER_AGENT.format(http_client="rnet3"),
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
        response_type: Option[typing.Any],
        json: Option[str | bytes],
        headers: Option[typing.Mapping[str, typing.Any]],
        urlencoded_params: Option[typing.Mapping[str, typing.Any]],
        query_params: Option[typing.Mapping[str, typing.Any]],
        body: Option[typing.Any],
        files: Option[typing.Mapping[str, MultipartFile]],
        auth: typing.Any = None,
    ) -> typing.Any:
        import rnet
        import rnet.exceptions

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
                parts: list[rnet.Part] = []

                for k, v in urlencoded_params.unwrap().items():
                    parts.append(rnet.Part(k, v if isinstance(v, str) else encoder.encode(v).strip('"')))

                for field_name, file_info in files.unwrap().items():
                    content = file_info.content.read() if isinstance(file_info.content, typing.IO | IOBase) else file_info.content
                    parts.append(
                        rnet.Part(
                            name=field_name,
                            value=content,
                            filename=file_info.name,
                            mime=file_info.mime,
                        ),
                    )

                kwargs["multipart"] = rnet.Multipart(*parts)

            resp = await self.client.request(
                getattr(rnet.Method, method.name),
                url,
                default_headers=self.default_headers,
                timeout=self.request_timeout,
                **kwargs,
            )
            payload = await resp.bytes()

            if 200 <= resp.status.as_int() < 300:
                return self._validate_response(payload, response_type.unwrap_or(typing.Any), as_result=as_result)

            self._raise_error(
                path,
                method,
                status=(status := HTTPStatus(resp.status.as_int())),
                payload=payload,
                errors=errors,
                request_id=(request_id := None if not (req_id := resp.headers.get("x-request-id") or resp.headers.get("request-id")) else req_id.decode()),
            )
        except BaseException as exception:
            return self._handle_error(
                status,
                method,
                path,
                request_id,
                exception,
                rnet.exceptions.ConnectionError,
                rnet.exceptions.ConnectionResetError,
                rnet.exceptions.ProxyConnectionError,
                rnet.exceptions.RequestError,
                rnet.exceptions.TimeoutError,
                rnet.exceptions.RustPanic,
                rnet.exceptions.TlsError,
                rnet.exceptions.BodyError,
                rnet.exceptions.RedirectError,
                as_result=as_result,
            )


__all__ = ("RnetClient",)
