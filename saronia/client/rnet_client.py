# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import datetime
import typing
from http import HTTPMethod, HTTPStatus
from io import IOBase

from kungfu import Error, Ok, Option, Result
from msgspex import decoder, encoder

from saronia.client.base import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, BaseClient, MultipartFile
from saronia.error import APIError, NetworkError, UnknownError

if typing.TYPE_CHECKING:
    import rnet


class RnetClient(BaseClient):
    def __init__(
        self,
        client: "rnet.Client",
        base_url: str = "",
        *,
        user_agent: str | None = None,
        request_timeout: datetime.timedelta | float = DEFAULT_TIMEOUT,
        default_headers: bool = False,
    ) -> None:
        super().__init__(
            user_agent=user_agent or DEFAULT_USER_AGENT.format(http_client="rnet3"),
            base_url=base_url.rstrip("/"),
        )

        self.client = client
        self.default_headers = default_headers
        self.request_timeout = (
            request_timeout
            if request_timeout is None
            else datetime.timedelta(seconds=request_timeout)
            if isinstance(request_timeout, int | float)
            else request_timeout
        )

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
        import rnet
        import rnet.exceptions

        url = f"{self.base_url}{path}" if self.base_url else path

        try:
            kwargs: dict[str, typing.Any] = {
                "headers": self.headers.copy(),
                "query": self.query_parameters.copy(),
                "cookies": self.cookies.copy(),
            }

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

            if 200 <= resp.status.as_int() < 300:
                return Ok(decoder.decode(await resp.bytes(), type=response_type.unwrap_or(typing.Any)))

            request_id = resp.headers.get("x-request-id") or resp.headers.get("request-id")
            request_id = None if not request_id else request_id.decode()
            return self.to_api_error(
                path,
                method,
                status=HTTPStatus(resp.status.as_int()),
                payload=await resp.bytes(),
                errors=errors,
                request_id=request_id,
            )
        except SystemExit, KeyboardInterrupt:
            raise
        except (
            rnet.exceptions.ConnectionError,
            rnet.exceptions.ConnectionResetError,
            rnet.exceptions.ProxyConnectionError,
            rnet.exceptions.RequestError,
            rnet.exceptions.TimeoutError,
            rnet.exceptions.RustPanic,
            rnet.exceptions.TlsError,
            rnet.exceptions.BodyError,
            rnet.exceptions.RedirectError,
        ) as error:
            return Error(
                APIError(
                    NetworkError("RNET network error occurred", error),
                    method,
                    status=HTTPStatus.BAD_REQUEST,
                    path=path,
                ),
            )
        except BaseException as exc:
            return Error(
                APIError(
                    UnknownError(b"", orig_error=exc),
                    method,
                    status=HTTPStatus.BAD_REQUEST,
                    path=path,
                ),
            )


__all__ = ("RnetClient",)
