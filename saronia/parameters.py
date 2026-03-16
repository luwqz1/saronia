import dataclasses
import io
import pathlib
import typing

from msgspex import Model, decoder, fullname, get_origin

if typing.TYPE_CHECKING:
    type AnnotationForm = typing.Any

MULTIPART_URL_ENCODED_MODEL_ATTR: typing.Final = "__saronia_multipart_urlencoded_model__"
PATH_MODEL_ATTR: typing.Final = "__saronia_path_model__"
JSON_MODEL_ATTR: typing.Final = "__saronia_json_model__"
HEADER_MODEL_ATTR: typing.Final = "__saronia_header_model__"
QUERY_MODEL_ATTR: typing.Final = "__saronia_query_model__"


@decoder.set_default_dec_hook
def saronia_default_decoder(t: typing.Any, obj: typing.Any) -> typing.Any:
    orig_type = get_origin(t)

    if isinstance(obj, orig_type):
        return obj

    raise TypeError(f"Expected `{fullname(orig_type)}`, got `{fullname(obj)}`")


def is_urlencoded(model: typing.Any, /) -> bool:
    return getattr(model, MULTIPART_URL_ENCODED_MODEL_ATTR, False) is True


def is_path(model: typing.Any, /) -> bool:
    return getattr(model, PATH_MODEL_ATTR, False) is True


def is_query(model: typing.Any, /) -> bool:
    return getattr(model, QUERY_MODEL_ATTR, False) is True


def is_header(model: typing.Any, /) -> bool:
    return getattr(model, HEADER_MODEL_ATTR, False) is True


def is_json(model: typing.Any, /) -> bool:
    return getattr(model, JSON_MODEL_ATTR, False) is True


def urlencoded[T: Model](model: type[T], /) -> type[T]:
    setattr(model, MULTIPART_URL_ENCODED_MODEL_ATTR, True)
    return model


def path[T: Model](model: type[T], /) -> type[T]:
    setattr(model, PATH_MODEL_ATTR, True)
    return model


def query[T: Model](model: type[T], /) -> type[T]:
    setattr(model, QUERY_MODEL_ATTR, True)
    return model


def header[T: Model](model: type[T], /) -> type[T]:
    setattr(model, HEADER_MODEL_ATTR, True)
    return model


def json[T: Model](model: type[T], /) -> type[T]:
    setattr(model, JSON_MODEL_ATTR, True)
    return model


def get_annotated_parameter(annotation: AnnotationForm, /) -> Parameter | None:
    if annotation is None:
        return None

    if isinstance(typing.get_origin(annotation) or annotation, typing.TypeAliasType):
        annotation = annotation.__value__

    if not isinstance(annotation, typing._AnnotatedAlias):  # type: ignore
        return None

    if len(metadata := getattr(annotation, "__metadata__")) != 1 or not isinstance(param := metadata[0], Parameter):
        return None

    return param


@dataclasses.dataclass(frozen=True)
class Parameter: ...


@dataclasses.dataclass(frozen=True)
class PathParameter(Parameter):
    alias_name: str | None = None


@dataclasses.dataclass(frozen=True)
class QueryParameter(PathParameter): ...


@dataclasses.dataclass(frozen=True)
class HeaderParameter(PathParameter): ...


@dataclasses.dataclass(frozen=True)
class XHeaderParameter(PathParameter): ...


@dataclasses.dataclass(frozen=True)
class URLencodedParameter(PathParameter): ...


@dataclasses.dataclass(frozen=True)
class JSONParameter(PathParameter): ...


@dataclasses.dataclass(frozen=True)
class Body(Parameter): ...


@dataclasses.dataclass(frozen=True, slots=True)
class File(Parameter):
    name: str | None = None
    mime: str | None = None


# Parameter
type Path[T] = typing.Annotated[T, PathParameter()]
type Header[T] = typing.Annotated[T, HeaderParameter()]
type XHeader[T] = typing.Annotated[T, XHeaderParameter()]
type Query[T] = typing.Annotated[T, QueryParameter()]
type URLencoded[T] = typing.Annotated[T, URLencodedParameter()]
type JSON[T] = typing.Annotated[T, JSONParameter()]

# Body
AnyBody = typing.Annotated[typing.Any, Body()]
BytesBody = typing.Annotated[bytes, Body()]
StringBody = typing.Annotated[str, Body()]
ModelBody = typing.Annotated[Model, Body()]
MappingBody = typing.Annotated[typing.Mapping[str, typing.Any], Body()]

# Stream Body
AsyncStream = typing.Annotated[typing.AsyncGenerator[bytes, typing.Any], Body()]
Stream = typing.Annotated[typing.Generator[bytes, typing.Any, typing.Any], Body()]

# File
IO = typing.Annotated[typing.IO[bytes], File()]
BytesIO = typing.Annotated[io.BytesIO, File()]
FileIO = typing.Annotated[io.FileIO, File()]
FilePath = typing.Annotated[pathlib.Path, File()]
FileBinary = typing.Annotated[typing.BinaryIO, File()]

if typing.TYPE_CHECKING:
    FileBuffer = typing.Annotated[typing.BinaryIO, File()]
else:
    FileBuffer = typing.Annotated[io.BufferedIOBase, File()]


if typing.TYPE_CHECKING:
    from typing import Annotated as Param

else:

    @dataclasses.dataclass(frozen=True, slots=True)
    class Param:
        annotation: typing.Any
        parameter: Parameter = dataclasses.field(default_factory=PathParameter)
        name: str | None = None

        def __class_getitem__(cls, item: typing.Any, /) -> typing.Any:
            if not isinstance(item, tuple):
                raise ValueError(f"Expected annotation and parameter, got `{item!r}`.")

            if len(item) > 3:
                raise ValueError(f"Expected at most 3 arguments: `annotation`, `parameter` and optional `name`, but {len(item)} were given.")

            if len(item) >= 2:
                parameter = get_annotated_parameter(item[1])

                if parameter is None:
                    raise ValueError(f"Expected kind of Parameter, but `{item[1]!r}` were given.")

                item = (item[0], parameter) + item[2:]

            return cls(*item)


__all__ = (
    "IO",
    "JSON",
    "AnyBody",
    "AsyncStream",
    "BytesBody",
    "BytesIO",
    "FileBinary",
    "FileBuffer",
    "FileIO",
    "FilePath",
    "Header",
    "MappingBody",
    "ModelBody",
    "Param",
    "Path",
    "Query",
    "Stream",
    "StringBody",
    "URLencoded",
    "XHeader",
    "get_annotated_parameter",
    "header",
    "is_header",
    "is_json",
    "is_path",
    "is_query",
    "is_urlencoded",
    "json",
    "path",
    "query",
    "urlencoded",
)
