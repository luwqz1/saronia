# pyright: reportInvalidTypeVarUse=false

import typing
from http import HTTPMethod
from warnings import deprecated as route_deprecated

from kungfu import Result
from msgspex import Model

from saronia.error import APIError

type ParameterName = str
type DeprecationMessage = str
type Anything = typing.Never
type APIResult[T, E = Anything] = Result[T, APIError[E]]
type Authorization = typing.Any
type CoroutineType[R] = typing.Coroutine[typing.Any, typing.Any, R]
type RouteDecorator[**P, R] = typing.Callable[[typing.Callable[P, CoroutineType[R]]], typing.Callable[P, CoroutineType[R]]]

@typing.overload
def route[**P, R](method: HTTPMethod, path: str, /) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *,
    auth: Authorization | None = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    auth: Authorization | None = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *errors: typing.Any,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *errors: typing.Any,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    path: bool = True,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    query: bool,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    headers: bool,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    json: bool,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    urlencoded: bool,
    auth: Authorization | None = ...,
    response: type[R] = ...,
) -> RouteDecorator[P, R]: ...

def __route_http_method[**P, R](
    route_callable: typing.Callable[typing.Concatenate[typing.Any, P], R],
    /,
) -> typing.Callable[P, R]: ...

delete = get = head = options = patch = post = put = trace = __route_http_method(route)

__all__ = (
    "APIResult",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "route",
    "route_deprecated",
    "trace",
)
