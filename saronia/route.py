import dataclasses
import inspect
import io
import pathlib
import re
import secrets
import types
import typing
import urllib.parse
from functools import partial, wraps
from http import HTTPMethod

import kungfu
import msgspex
from kungfu import Option, Some
from kungfu.library.monad.option import NOTHING
from msgspex.tools.fullname import fullname
from msgspex.tools.model import get_class_annotations  # type: ignore

from saronia.api import join_path
from saronia.client.abc import MultipartFile
from saronia.controller import Controller
from saronia.tools.model_from_signature import create_model_from_function_signature
from saronia.tools.parameters import (
    Body,
    File,
    HeaderParameter,
    JSONParameter,
    PathParameter,
    QueryParameter,
    URLencodedParameter,
    XHeaderParameter,
    get_annotated_parameter,
    is_header,
    is_json,
    is_path,
    is_query,
    is_urlencoded,
)
from saronia.tools.parameters import (
    header as as_header,
)
from saronia.tools.parameters import (
    json as as_json,
)
from saronia.tools.parameters import (
    path as as_path,
)
from saronia.tools.parameters import (
    query as as_query,
)
from saronia.tools.parameters import (
    urlencoded as as_urlencoded,
)
from saronia.tools.signature import get_function_signature

type ParameterName = str
type ParameterAliasName = ParameterName | None
type Parameters = dict[ParameterName, ParameterAliasName]
type FieldName = str
type FileName = str | None
type MimeType = str | None
type Files = dict[FieldName, tuple[FileName, MimeType]]

type APIResult[Value, Err = typing.Never] = kungfu.Result[Value, Err]

_ROUTE_DEPRECATED_ATTR: typing.Final = "__saronia_route_deprecated__"
_PATH_PARAM_RE: typing.Final = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")
_NORESPONSE: typing.Final = object()
_NOAUTH: typing.Final = object()


def _resolve_auth(controller_auth: typing.Any, method_auth: typing.Any) -> typing.Any:
    if method_auth is None:
        return None

    if method_auth is _NOAUTH:
        return controller_auth

    if controller_auth is None:
        return method_auth

    from saronia.auth import AuthComposite

    if (isinstance(method_auth, AuthComposite) and method_auth.op == "AND") and (isinstance(method_auth.left, AuthComposite) and method_auth.left.op == "NOT"):
        return method_auth.right

    return AuthComposite("OR", controller_auth, method_auth)


def _extract_path_param_names(path: str, /) -> set[str]:
    return set(_PATH_PARAM_RE.findall(path))


def _to_header_name(name: str) -> str:
    return "-".join(part.capitalize() for part in name.split("_"))


def _to_x_header_name(name: str) -> str:
    return "X-" + "-".join(part.capitalize() for part in name.split("_"))


def _render_path(path_template: str, path_params: typing.Mapping[str, typing.Any], /) -> str:
    return path_template.format_map(
        {name: urllib.parse.quote(str(value), safe="") for name, value in path_params.items()},
    )


def _get_body_parameter(
    form_model: type[msgspex.Model],
    annotations: dict[str, typing.Any],
) -> tuple[str, Body] | None:
    res = None

    for field_name in form_model.__model_accessible_fields__:
        if type(b := get_annotated_parameter(annotations.get(field_name))) is Body:
            if res is None:
                res = (field_name, b)
            else:
                raise LookupError("Only one parameter of type `Body` is allowed.")

    return res


def _build_form_spec(
    *,
    form_model: type[msgspex.Model],
    is_decorated: bool,
    body: tuple[str, Body] | None,
    path_parameters: Parameters,
    query_parameters: Parameters,
    header_parameters: Parameters,
    json_parameters: Parameters,
    urlencoded_parameters: Parameters,
    files: Files,
) -> FormSpec:
    if body is not None and any((json_parameters, urlencoded_parameters, files)):
        raise LookupError("`JSON`, `URLencoded`, `File` parameters is not allowed with `Body`.")

    if json_parameters and urlencoded_parameters:
        raise LookupError(
            "Combination of `JSON` and `URLencoded` parameters is not allowed because "
            "`Content-Type` is completely different (`application/json` and `{}`).".format(
                "application/x-www-form-urlencoded" if not files else "multipart/form-data",
            ),
        )

    if json_parameters and files:
        raise LookupError(
            "Combination of `JSON` and `File` parameters is not allowed because "
            "`Content-Type` is completely different, but `File` parameters can be "
            "combined with `URLencoded` parameters, e.g. (`multipart/form-data`).",
        )

    return FormSpec(
        form_model=form_model,
        is_body=(not is_decorated and not any((path_parameters, query_parameters, urlencoded_parameters, header_parameters, files))),
        files=files,
        body_parameter=None if body is None else body[0],
        path_parameters=path_parameters,
        json_parameters=json_parameters,
        query_parameters=query_parameters,
        urlencoded_parameters=urlencoded_parameters,
        header_parameters=header_parameters,
    )


def _check_form_is_decorated(form_model: type[msgspex.Model], /) -> bool:
    clause = (
        is_json(form_model),
        is_urlencoded(form_model),
        is_path(form_model),
        is_query(form_model),
        is_header(form_model),
    )

    if sum(clause) > 1:
        raise LookupError(
            f"Model `{fullname(form_model)}` can be only one of: `path`, `query`, `header`, `json` or `urlencoded`.",
        )

    return any(clause)


def _get_form_spec(form_model: type[msgspex.Model], /) -> FormSpec:
    is_decorated = _check_form_is_decorated(form_model)
    model_annotations = typing.cast("dict[str, typing.Any]", get_class_annotations(form_model))
    body = _get_body_parameter(form_model, model_annotations)

    path_parameters: Parameters = {}
    query_parameters: Parameters = {}
    urlencoded_parameters: Parameters = {}
    header_parameters: Parameters = {}
    json_parameters: Parameters = {}
    files: Files = {}
    aliases = form_model.__model_aliases_fields__

    for field_name in form_model.__model_accessible_fields__:
        field_alias_name = aliases.get(field_name)
        parameter = get_annotated_parameter(model_annotations.get(field_name))

        if parameter is None and is_decorated:
            if is_header(form_model):
                header_parameters[field_name] = _to_header_name(field_alias_name or field_name)
            elif is_path(form_model):
                path_parameters[field_name] = field_alias_name
            elif is_query(form_model):
                query_parameters[field_name] = field_alias_name
            elif is_urlencoded(form_model):
                urlencoded_parameters[field_name] = field_alias_name
            elif is_json(form_model):
                json_parameters[field_name] = field_alias_name

        match parameter:
            case None:
                continue
            case Body() if body is not None and parameter is not body[1]:
                raise LookupError(
                    f"Another body-like parameter type of `{fullname(parameter)}` called `{field_name}` "
                    f"is not allowed to be used with `Body` parameter called `{body[0]}`.",
                )
            case QueryParameter(alias_name):
                query_parameters[field_name] = alias_name or field_alias_name
            case XHeaderParameter(alias_name):
                header_parameters[field_name] = _to_x_header_name(alias_name or field_alias_name or field_name)
            case HeaderParameter(alias_name):
                header_parameters[field_name] = _to_header_name(alias_name or field_alias_name or field_name)
            case JSONParameter(alias_name):
                json_parameters[field_name] = alias_name or field_alias_name
            case URLencodedParameter(alias_name):
                urlencoded_parameters[field_name] = alias_name or field_alias_name
            case PathParameter(alias_name):
                path_parameters[field_name] = alias_name or field_alias_name
            case File(filename, mime):
                files[field_alias_name or field_name] = (filename, mime)
            case _:
                pass

    return _build_form_spec(
        form_model=form_model,
        is_decorated=is_decorated,
        body=body,
        path_parameters=dict(path_parameters),
        query_parameters=dict(query_parameters),
        header_parameters=dict(header_parameters),
        json_parameters=dict(json_parameters),
        urlencoded_parameters=dict(urlencoded_parameters),
        files=files,
    )


def _create_form_spec(
    path: str,
    form: type[msgspex.Model] | None = None,
    function: typing.Callable[..., typing.Any] | None = None,
    is_path: bool = False,
    is_query: bool = False,
    is_header: bool = False,
    is_urlencoded: bool = False,
    is_json: bool = False,
) -> FormSpec:
    if form is None and function is not None:
        form = create_model_from_function_signature(function)

        if hasattr(function, _ROUTE_DEPRECATED_ATTR):
            deprecated_kwargs = getattr(function, _ROUTE_DEPRECATED_ATTR)
            form = msgspex.model_deprecated(
                deprecated_kwargs["message"],
                category=deprecated_kwargs.get("category", PendingDeprecationWarning),
                stacklevel=deprecated_kwargs.get("stacklevel", 3),
            )(form)

        if is_path:
            form = as_path(form)
        elif is_query:
            form = as_query(form)
        elif is_header:
            form = as_header(form)
        elif is_urlencoded:
            form = as_urlencoded(form)
        elif is_json:
            form = as_json(form)

    if form is None:
        raise AssertionError

    form_spec = _get_form_spec(form)
    missing_path_params = _extract_path_param_names(path) - set(alias or name for name, alias in form_spec.path_parameters.items())

    if missing_path_params:
        raise TypeError(f"`{form.__name__}` misses path params: {', '.join(missing_path_params)}.")

    return form_spec


def _parse_method_form(
    *,
    method: HTTPMethod,
    path_template: str,
    form: msgspex.Model,
    form_spec: FormSpec,
) -> ParsedForm:
    if form_spec.is_body:
        return ParsedForm(
            method=method,
            path_template=path_template,
            path=path_template,
            body=Some(form.to_raw()),
            json=NOTHING,
            urlencoded_params=NOTHING,
            query_params=NOTHING,
            header_params=NOTHING,
            files=NOTHING,
        )

    values = form.to_dict()

    path_params: dict[str, typing.Any] = {}
    query_params: dict[str, typing.Any] = {}
    urlencoded_params: dict[str, typing.Any] = {}
    header_params: dict[str, typing.Any] = {}
    json: dict[str, typing.Any] = {}

    for param_kind, params, form_spec_params in (
        ("Path", path_params, form_spec.path_parameters),
        ("Query", query_params, form_spec.query_parameters),
        ("URLencoded", urlencoded_params, form_spec.urlencoded_parameters),
        ("Header", header_params, form_spec.header_parameters),
        ("JSON", json, form_spec.json_parameters),
    ):
        for name, alias_name in form_spec_params.items():
            if name not in values:
                raise TypeError(f"{param_kind} parameter `{name}` is missing in `{fullname(form)}`.")

            params[alias_name or name] = values.pop(name)

    files: dict[str, MultipartFile] = {}

    for name, (mime, filename) in form_spec.files.items():
        if name not in values:
            raise TypeError(f"File parameter `{name}` is missing in `{fullname(form)}`.")

        content = values[name]

        if not filename and isinstance(content, io.IOBase | pathlib.Path):
            filename = getattr(content, "name", None)

        if not filename:
            filename = secrets.token_hex(8)

        files[name] = MultipartFile(filename, content, mime)

    body: Option[typing.Any] = NOTHING

    if form_spec.body_parameter:
        if form_spec.body_parameter not in values:
            raise TypeError(f"Body parameter `{form_spec.body_parameter}` is missing in `{fullname(form)}`.")

        body = Some(values[form_spec.body_parameter])

    return ParsedForm(
        method=method,
        path_template=path_template,
        path=_render_path(path_template, path_params),
        body=body,
        json=NOTHING if not json else Some(msgspex.encoder.encode(json)),
        urlencoded_params=NOTHING if not urlencoded_params else Some(urlencoded_params),
        query_params=NOTHING if not query_params else Some(query_params),
        header_params=NOTHING if not header_params else Some(header_params),
        files=NOTHING if not files else Some(files),
    )


def route_deprecated(
    message: str | None = None,
    *,
    category: type[Warning] = PendingDeprecationWarning,
    stacklevel: int = 5,
) -> typing.Callable[..., typing.Any]:
    def decorator(fn: typing.Callable[..., typing.Any], /) -> typing.Callable[..., typing.Any]:
        if not hasattr(fn, _ROUTE_DEPRECATED_ATTR):
            setattr(
                fn,
                _ROUTE_DEPRECATED_ATTR,
                dict(
                    message=message or f"Route `{fn.__name__}` is deprecated and will be removed in future releases.",
                    category=category,
                    stacklevel=stacklevel,
                ),
            )

        return fn

    return decorator


def route(
    method: HTTPMethod,
    __path: str,
    _form: type[msgspex.Model] | None = None,
    /,
    *errors: typing.Any,
    form: type[msgspex.Model] | None = None,
    auth: typing.Any = _NOAUTH,
    response: typing.Any = _NORESPONSE,
    path: bool = True,
    query: bool = False,
    header: bool = False,
    urlencoded: bool = False,
    json: bool = False,
) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Callable[..., typing.Any]]:
    form_spec: FormSpec | None = None
    _errors: tuple[typing.Any, ...] = errors
    as_result = False

    if form is not None:
        form_spec = _create_form_spec(__path, form)

    def decorator(fn: typing.Callable[..., typing.Any], /) -> typing.Callable[..., typing.Any]:
        if isinstance(fn, classmethod | staticmethod):
            raise TypeError("classmethods and staticmethods is not allowed for decorated controller method.")

        if not inspect.iscoroutinefunction(fn):
            raise TypeError("Decorated controller method must be async.")

        sig = get_function_signature(fn)

        nonlocal form_spec, _errors, response, as_result

        if sig.has_return_type and (typing.get_origin(sig.return_type) or sig.return_type in (APIResult, kungfu.Result)):
            if form is None and _form is not None:
                form_spec = _create_form_spec(__path, _form)

            if len(typing.get_args(sig.return_type)) == 2:
                as_result = True
                resp, error = typing.get_args(sig.return_type)
                _errors = typing.get_args(error) if isinstance(error, types.UnionType) else (error,)
            elif len(typing.get_args(sig.return_type)) == 1:
                as_result = True
                resp = typing.get_args(sig.return_type)[0]
            else:
                resp = response

            response = resp if response is _NORESPONSE else response
        else:
            if sig.has_return_type:
                response = sig.return_type

            if _form is not None and form is not None:
                _errors = (_form,) + _errors

            elif form is None and _form is not None:
                form_spec = _create_form_spec(__path, _form)

        if form_spec is None:
            form_spec = _create_form_spec(
                path=__path,
                function=fn,
                is_path=path,
                is_query=query,
                is_header=header,
                is_urlencoded=urlencoded,
                is_json=json,
            )

        from saronia.api import SARONIA_CONTROLLER_AUTH_ATTR

        @wraps(fn)
        async def wrapper(controller: Controller, /, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if form_spec is None:
                raise AssertionError("form_spec is None")

            parsed = _parse_method_form(
                method=method,
                path_template=join_path(controller.path, __path),
                form_spec=form_spec,
                form=form_spec.form_model.from_data(*args, **kwargs),
            )
            return await controller.client.request(
                parsed.path,
                method,
                as_result=as_result,
                auth=_resolve_auth(getattr(type(controller), SARONIA_CONTROLLER_AUTH_ATTR, None), auth),
                errors=_errors,
                response_type=NOTHING if response is _NORESPONSE else Some(response),
                json=parsed.json,
                headers=parsed.header_params,
                urlencoded_params=parsed.urlencoded_params,
                query_params=parsed.query_params,
                body=parsed.body,
                files=parsed.files,
            )

        del sig
        return wrapper

    return decorator


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class FormSpec:
    form_model: type[msgspex.Model]
    is_body: bool
    body_parameter: str | None
    files: Files
    json_parameters: Parameters
    path_parameters: Parameters
    query_parameters: Parameters
    urlencoded_parameters: Parameters
    header_parameters: Parameters


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class ParsedForm:
    method: HTTPMethod
    path_template: str
    path: str
    json: Option[str | bytes]
    body: Option[typing.Any]
    urlencoded_params: Option[dict[str, typing.Any]]
    query_params: Option[dict[str, typing.Any]]
    header_params: Option[dict[str, typing.Any]]
    files: Option[dict[str, MultipartFile]]


get = partial(route, HTTPMethod.GET)
post = partial(route, HTTPMethod.POST)
delete = partial(route, HTTPMethod.DELETE)
head = partial(route, HTTPMethod.HEAD)
options = partial(route, HTTPMethod.OPTIONS)
patch = partial(route, HTTPMethod.PATCH)
put = partial(route, HTTPMethod.PUT)
trace = partial(route, HTTPMethod.TRACE)


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
