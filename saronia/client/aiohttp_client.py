# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import typing
from http import HTTPMethod, HTTPStatus

from kungfu import Error, Ok, Option, Result
from kungfu.library.monad.option import NOTHING
from msgspex import decoder, encoder

from saronia.client.abc import ABCClient, MultipartFile
from saronia.error import APIError, NetworkError

if typing.TYPE_CHECKING:
    import aiohttp


class AiohttpClient(ABCClient):
    __slots__ = ("_session", "_base_url")

    def __init__(self, session: "aiohttp.ClientSession", base_url: str = "") -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

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

        url = f"{self._base_url}{path}" if self._base_url else path

        try:
            kwargs: dict[str, typing.Any] = {}

            if headers:
                kwargs["headers"] = {k: str(v) for k, v in headers.unwrap().items()}

            if query_params:
                kwargs["params"] = {k: str(v) for k, v in query_params.unwrap().items()}

            if json:
                json_data = json.unwrap()
                ct_header = {"Content-Type": "application/json"}
                if "headers" in kwargs:
                    kwargs["headers"].update(ct_header)
                else:
                    kwargs["headers"] = ct_header
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

            async with self._session.request(method.value, url, **kwargs) as resp:
                status = HTTPStatus(resp.status)

                if 200 <= resp.status < 300:
                    return Ok(decoder.decode(await resp.read(), type=response_type.unwrap_or(typing.Any)))

                error_data = await resp.read()
                request_id = resp.headers.get("X-Request-ID") or resp.headers.get("Request-ID")

                if not error_data:
                    return Error(APIError(None, method, status, path=path, request_id=request_id))

                for error_type in errors:
                    try:
                        error_obj = decoder.decode(error_data, type=error_type)
                        return Error(APIError(error_obj, method, status, path=path, request_id=request_id))
                    except Exception:
                        continue

                return Error(APIError(error_data, method, status, path=path, request_id=request_id))

        except (aiohttp.client_exceptions.ClientError, aiohttp.http_exceptions.HttpProcessingError) as error:
            return Error(
                APIError(
                    NetworkError("AIOHTTP network error occurred", error),
                    method,
                    status=HTTPStatus.BAD_REQUEST,
                    path=path,
                ),
            )


__all__ = ("AiohttpClient",)
