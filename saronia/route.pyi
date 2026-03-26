# pyright: reportInvalidTypeVarUse=false

import typing
from http import HTTPMethod
from warnings import deprecated as route_deprecated

from kungfu import Result
from msgspex import Model

from saronia.client.abc import ResponseHandler
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
def route[**P, **X, C, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    form: typing.Callable[P, Model],
    path: bool = True,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    form: typing.Callable[P, Model],
    query: bool,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    form: typing.Callable[P, Model],
    header: bool,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    form: typing.Callable[P, Model],
    json: bool,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, **X, C, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    form: typing.Callable[P, Model],
    urlencoded: bool,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[R]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[R]],
]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    __path: str,
    /,
    *errors: typing.Any,
    path: bool = True,
    auth: Authorization | None = ...,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    query: bool,
    auth: Authorization | None = ...,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    header: bool,
    auth: Authorization | None = ...,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    json: bool,
    auth: Authorization | None = ...,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
) -> RouteDecorator[P, R]: ...
@typing.overload
def route[**P, R](
    method: HTTPMethod,
    path: str,
    /,
    *errors: typing.Any,
    urlencoded: bool,
    auth: Authorization | None = ...,
    response: typing.Any = ...,
    response_handler: ResponseHandler = ...,
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
