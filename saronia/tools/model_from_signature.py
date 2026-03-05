import typing

import msgspec
import msgspex

from saronia.tools.signature import get_function_signature


def create_model_from_function_signature(func: typing.Callable[..., typing.Any], /) -> type[msgspex.Model]:
    signature = get_function_signature(func)
    model = msgspec.defstruct(
        name=func.__name__,
        fields=tuple(
            (
                parameter.name,
                parameter.annotation,
                parameter.default if parameter.has_default else msgspec.NODEFAULT,
            )
            for parameter in signature.all_params
            if parameter.name not in ("self", "cls")
        ),
        bases=(msgspex.Model,),
        module=func.__module__,
    )
    return typing.cast("type[msgspex.Model]", model)


__all__ = ("create_model_from_function_signature",)
