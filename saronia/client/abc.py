import abc
import typing
from http import HTTPMethod

from kungfu import Option

if typing.TYPE_CHECKING:
    from io import IOBase
    from pathlib import Path


class MultipartFile(typing.NamedTuple):
    name: str
    content: typing.Union[
        typing.AsyncGenerator[bytes, typing.Any],
        typing.Generator[bytes, typing.Any, typing.Any],
        typing.IO[bytes],
        IOBase,
        Path,
        bytes,
    ]
    mime: str | None = None


class ABCClient(abc.ABC):
    @abc.abstractmethod
    def auth(self, auth_model: typing.Any) -> None:
        pass

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


__all__ = ("ABCClient",)
