import base64
import dataclasses
import typing


@dataclasses.dataclass(slots=True, repr=False)
class APIKey:
    key: str
    name: str = dataclasses.field(init=False)

    def __class_getitem__(cls, name: str, /) -> typing.Any:
        return dataclasses.make_dataclass(
            cls.__name__,
            (("name", str, dataclasses.field(init=False, default=name)),),
            bases=(cls,),
            namespace=dict(__module__=cls.__module__),
            slots=True,
            repr=False,
        )

    @property
    def mapping(self) -> typing.Mapping[str, str]:
        return {self.name: self.key}


@dataclasses.dataclass(slots=True, repr=False)
class HTTPAuthorization:
    credentials: str
    scheme: str

    @property
    def header(self) -> typing.Mapping[str, str]:
        return {"Authorization": f"{self.scheme} {self.credentials}"}


@dataclasses.dataclass(slots=True, repr=False)
class HTTPBearer(HTTPAuthorization):
    token: dataclasses.InitVar[str]
    scheme: typing.Literal["Bearer"] = dataclasses.field(default="Bearer", init=False)
    credentials: str = dataclasses.field(init=False)

    def __post_init__(self, token: str) -> None:
        self.credentials = token


@dataclasses.dataclass(slots=True, repr=False)
class HTTPBasic(HTTPAuthorization):
    username: dataclasses.InitVar[str]
    password: dataclasses.InitVar[str]
    scheme: typing.Literal["Basic"] = dataclasses.field(default="Basic", init=False)
    credentials: str = dataclasses.field(init=False)

    def __post_init__(self, username: str, password: str) -> None:
        self.credentials = base64.b64encode(f"{username}:{password}".encode()).decode()


@dataclasses.dataclass(slots=True, repr=False)
class HeaderAPIKey(APIKey):
    pass


@dataclasses.dataclass(slots=True, repr=False)
class QueryAPIKey(APIKey):
    pass


@dataclasses.dataclass(slots=True, repr=False)
class CookieAPIKey(APIKey):
    pass


__all__ = (
    "APIKey",
    "CookieAPIKey",
    "HTTPAuthorization",
    "HTTPBasic",
    "HTTPBearer",
    "HeaderAPIKey",
    "QueryAPIKey",
)
