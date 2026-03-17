import typing

import msgspec
import msgspex

from saronia.tools.parameters import Param
from saronia.tools.signature import get_function_signature


def create_model_from_function_signature(func: typing.Callable[..., typing.Any], /) -> type[msgspex.Model]:
    signature = get_function_signature(func)
    annotations: dict[str, typing.Any] = {}
    fields: dict[str, typing.Any] = {}

    for parameter in signature.all_params:
        if parameter.name in ("self", "cls"):
            continue

        annotation = parameter.annotation
        name: str | None = None

        if isinstance(annotation, Param):  # type: ignore
            annotation = annotation.to_annotated()  # type: ignore
            name = getattr(annotation, "name")

        annotations[parameter.name] = annotation
        fields[parameter.name] = msgspec.field(
            default=parameter.default if parameter.has_default else msgspec.NODEFAULT,
            name=name,
        )

    return msgspex.ModelMeta.__new__(  # type: ignore
        msgspex.ModelMeta,
        f"Model:{func.__name__}",
        (msgspex.Model,),
        {
            "__type_params__": getattr(func, "__type_params__", ()),
            "__module__": func.__module__,
            "__annotations__": annotations,
        }
        | fields,
    )


__all__ = ("create_model_from_function_signature",)
