# pyright: reportAttributeAccessIssue=false, reportMissingImports=false

import typing
from http import HTTPMethod, HTTPStatus
from io import IOBase

from kungfu import Error, Ok, Option, Result
from msgspex import decoder, encoder

from saronia.client.abc import ABCClient, MultipartFile
from saronia.error import APIError, NetworkError

if typing.TYPE_CHECKING:
    import rnet


class RnetClient(ABCClient):
    __slots__ = ("_client", "_base_url")

    def __init__(self, client: "rnet.Client", base_url: str = "") -> None:
        self._client = client
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
        import rnet
        import rnet.exceptions

        url = f"{self._base_url}{path}" if self._base_url else path

        try:
            kwargs: dict[str, typing.Any] = {}

            if headers:
                kwargs["headers"] = {k: v if isinstance(v, str) else encoder.encode(v).strip('"') for k, v in headers.unwrap().items()}

            if query_params:
                kwargs["query"] = {k: v if isinstance(v, str) else encoder.encode(v).strip('"') for k, v in query_params.unwrap().items()}

            if json:
                json_data = json.unwrap()
                ct_header = {"Content-Type": "application/json"}
                if "headers" in kwargs:
                    kwargs["headers"].update(ct_header)
                else:
                    kwargs["headers"] = ct_header
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

            resp = await self._client.request(getattr(rnet.Method, method.name), url, **kwargs)
            status = HTTPStatus(resp.status.as_int())

            if 200 <= resp.status.as_int() < 300:
                return Ok(decoder.decode(await resp.bytes(), type=response_type.unwrap_or(typing.Any)))

            error_data = await resp.bytes()
            request_id = resp.headers.get("x-request-id") or resp.headers.get("request-id")
            request_id = None if not request_id else request_id.decode()

            if not error_data:
                return Error(APIError(None, method, status, path=path, request_id=request_id))

            for error_type in errors:
                try:
                    error_obj = decoder.decode(error_data, type=error_type)
                    return Error(APIError(error_obj, method, status, path=path, request_id=request_id))
                except Exception:
                    continue

            return Error(APIError(error_data, method, status, path=path, request_id=request_id))

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
                    NetworkError("Rnet network error occurred", error),
                    method,
                    status=HTTPStatus.BAD_REQUEST,
                    path=path,
                ),
            )


__all__ = ("RnetClient",)
