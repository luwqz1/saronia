import dataclasses
import inspect
import typing
from functools import cache, cached_property

type AnnotationForm = typing.Any


@cache
def get_function_signature(func: typing.Callable[..., typing.Any], /) -> Signature:
    return Signature.from_callable(func)


@dataclasses.dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    annotation: AnnotationForm
    default: typing.Any = dataclasses.field(default_factory=lambda: inspect.Parameter.empty)

    @property
    def has_default(self) -> bool:
        return self.default is not inspect.Parameter.empty


@dataclasses.dataclass(frozen=True)
class Signature:
    sig: inspect.Signature
    var_pos_only: Parameter | None = dataclasses.field(default=None)
    args: tuple[Parameter, ...] = dataclasses.field(default_factory=tuple)
    var_kw_only: Parameter | None = dataclasses.field(default=None)
    kw_only_args: tuple[Parameter, ...] = dataclasses.field(default_factory=tuple)
    kw_args: tuple[Parameter, ...] = dataclasses.field(default_factory=tuple)
    return_type: typing.Any = dataclasses.field(default_factory=lambda: inspect.Parameter.empty)

    def bind_arguments(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Mapping[str, typing.Any]:
        return self.sig.bind(*args, **kwargs).arguments

    @classmethod
    def from_callable(cls, callable: typing.Callable[..., typing.Any], /) -> typing.Self:
        signature = inspect.signature(callable, eval_str=True)
        setattr(callable, "__signature__", signature)

        var_pos_only: Parameter | None = None
        var_kw_only: Parameter | None = None
        kw_args: list[Parameter] = []
        pos_only_args: list[Parameter] = []
        kw_only_args: list[Parameter] = []

        for name, parameter in signature.parameters.items():
            param = Parameter(
                name,
                typing.Any if parameter.annotation is inspect.Parameter.empty else parameter.annotation,
                default=parameter.default,
            )

            match parameter.kind:
                case inspect.Parameter.VAR_POSITIONAL:
                    var_pos_only = param
                case inspect.Parameter.VAR_KEYWORD:
                    var_kw_only = param
                case inspect.Parameter.POSITIONAL_ONLY:
                    pos_only_args.append(param)
                case inspect.Parameter.KEYWORD_ONLY:
                    kw_only_args.append(param)
                case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    kw_args.append(param)
                case _:
                    typing.assert_never(parameter.kind)

        return cls(
            sig=signature,
            var_pos_only=var_pos_only,
            args=tuple(pos_only_args),
            var_kw_only=var_kw_only,
            kw_only_args=tuple(kw_only_args),
            kw_args=tuple(kw_args),
            return_type=signature.return_annotation,
        )

    @property
    def has_return_type(self) -> bool:
        return self.return_type is not inspect.Parameter.empty

    @cached_property
    def kwargs(self) -> tuple[Parameter, ...]:
        return self.kw_args + self.kw_only_args

    @cached_property
    def all_params(self) -> tuple[Parameter, ...]:
        return self.args + self.kwargs


__all__ = ("get_function_signature",)
