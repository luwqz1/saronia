import typing

from saronia.client.abc import ABCClient


class Controller(typing.Protocol):
    path: typing.Final[str]
    client: typing.Final[ABCClient]


__all__ = ("Controller",)
