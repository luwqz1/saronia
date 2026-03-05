# pyright: reportInvalidTypeVarUse=false

import typing
from http import HTTPMethod

from kungfu import Result
from msgspex import Model

from saronia.error import APIError

type APIResult[T, E] = Result[T, APIError[E]]
type Coroutine[R] = typing.Coroutine[typing.Any, typing.Any, R]
type RouteDecorator[**P, R] = typing.Callable[[typing.Callable[P, Coroutine[R]]], typing.Callable[P, Coroutine[R]]]

@typing.overload
def route[**P, T, E](method: HTTPMethod, path: str, /) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    __path: str,
    /,
    *,
    path: bool = True,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    query: bool,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    headers: bool,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    json: bool,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    urlencoded: bool,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, C, T, E](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *,
    response: type[T] = ...,
) -> RouteDecorator[typing.Concatenate[C, P], APIResult[T, E]]: ...
def __route_http_method[**P, R](
    route_callable: typing.Callable[typing.Concatenate[typing.Any, P], R],
    /,
) -> typing.Callable[P, R]: ...

connect = delete = get = head = options = patch = post = put = trace = __route_http_method(route)

__all__ = (
    "APIResult",
    "connect",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "route",
    "trace",
)
