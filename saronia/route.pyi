# pyright: reportInvalidTypeVarUse=false

import typing
from http import HTTPMethod

from kungfu import Result
from msgspex import Model

from saronia.error import APIError

type APIResult[T, E] = Result[T, APIError[E]]
type Authorization = typing.Any
type CoroutineType[R] = typing.Coroutine[typing.Any, typing.Any, R]
type RouteDecorator[**P, R] = typing.Callable[[typing.Callable[P, CoroutineType[R]]], typing.Callable[P, CoroutineType[R]]]

@typing.overload
def route[**P, T, E](method: HTTPMethod, path: str, /) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    auth: Authorization | None = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, **X, C, T, E](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *,
    auth: Authorization | None = ...,
) -> typing.Callable[
    [typing.Callable[typing.Concatenate[C, X], CoroutineType[Result[T, APIError[E]]]]],
    typing.Callable[typing.Concatenate[C, P], CoroutineType[Result[T, APIError[E]]]],
]: ...
@typing.overload
def route[**P, C, T, E](
    method: HTTPMethod,
    path: str,
    form: typing.Callable[P, Model],
    /,
    *,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[typing.Concatenate[C, P], APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    __path: str,
    /,
    *,
    path: bool = True,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    query: bool,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    headers: bool,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    json: bool,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
@typing.overload
def route[**P, T, E](
    method: HTTPMethod,
    path: str,
    /,
    *,
    urlencoded: bool,
    auth: Authorization | None = ...,
    response: type[T] = ...,
) -> RouteDecorator[P, APIResult[T, E]]: ...
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
    "trace",
)
