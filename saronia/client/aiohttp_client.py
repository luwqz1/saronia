# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import typing
from http import HTTPMethod, HTTPStatus

from kungfu import Error, Ok, Option, Result
from kungfu.library.monad.option import NOTHING
from msgspex import decoder, encoder

from saronia.client.base import DEFAULT_USER_AGENT, BaseClient, MultipartFile
from saronia.error import APIError, NetworkError, UnknownError

if typing.TYPE_CHECKING:
    import aiohttp


class AiohttpClient(BaseClient):
    def __init__(
        self,
        session: "aiohttp.ClientSession",
        *,
        user_agent: str | None = None,
        request_timeout: float | None = None,
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
        errors: tuple[typing.Any, ...],
        response_type: Option[typing.Any],
        json: Option[str | bytes],
        headers: Option[typing.Mapping[str, typing.Any]],
        urlencoded_params: Option[typing.Mapping[str, typing.Any]],
        query_params: Option[typing.Mapping[str, typing.Any]],
        body: Option[typing.Any],
        files: Option[typing.Mapping[str, MultipartFile]],
    ) -> Result[typing.Any, APIError[typing.Any]]:
        import aiohttp
        import aiohttp.client_exceptions
        import aiohttp.http_exceptions

        try:
            kwargs: dict[str, typing.Any] = {
                "headers": self.headers.copy(),
                "params": self.query_parameters.copy(),
                "cookies": self.cookies,
            }

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

            async with self.session.request(method.value, path, **kwargs) as resp:
                if 200 <= resp.status < 300:
                    return Ok(decoder.decode(await resp.read(), type=response_type.unwrap_or(typing.Any)))

                return self.to_api_error(
                    path,
                    method,
                    status=HTTPStatus(resp.status),
                    payload=await resp.read(),
                    errors=errors,
                    request_id=resp.headers.get("X-Request-ID") or resp.headers.get("Request-ID"),
                )
        except SystemExit, KeyboardInterrupt:
            raise
        except (aiohttp.client_exceptions.ClientError, aiohttp.http_exceptions.HttpProcessingError) as error:
            return Error(
                APIError(
                    NetworkError("AIOHTTP network error occurred", error),
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


__all__ = ("AiohttpClient",)
