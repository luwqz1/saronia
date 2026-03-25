<div align="center">
  <p>
    <a href="https://github.com/luwqz1/saronia">
      <picture>
        <img alt="Logo" src="https://raw.githubusercontent.com/luwqz1/saronia/main/assets/logo.svg" width="150">
      </picture>
    </a>
  </p>

  <h1>saronia</h1>

  <p>
    <i>A lightweight, spec-driven builder for API clients and controllers.</i>
  </p>

  <a href="https://www.python.org/"><img alt="python version" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fluwqz1%2Fsaronia%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&style=flat-square&logo=python&logoColor=fff&labelColor=black&cacheSeconds=3600"></img></a>
  <a href="https://github.com/luwqz1/saronia"><img alt="saronia version" src="https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fluwqz1%2Fsaronia%2Frefs%2Fheads%2Fmain%2Fsaronia%2F__meta__.py&search=__version__%5Cs*%3D%5Cs*%22(%3F%3Cversion%3E%5B%5E%22%5D%2B)%22&replace=v%24%3Cversion%3E&style=flat-square&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB3aWR0aD0iMjQwIiBoZWlnaHQ9IjI0MCIgdmlld0JveD0iMCAwIDI0MCAyNDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgcm9sZT0iaW1nIiBhcmlhLWxhYmVsbGVkYnk9InRpdGxlIGRlc2MiPgogIDx0aXRsZSBpZD0idGl0bGUiPnNhcm9uaWEgaWNvbjwvdGl0bGU%2BCiAgPGRlc2MgaWQ9ImRlc2MiPk1pbmltYWxpc3QgaWNvbiBmb3Igc2Fyb25pYS48L2Rlc2M%2BCgogIDxyZWN0IHg9IjAiIHk9IjAiIHdpZHRoPSIyNDAiIGhlaWdodD0iMjQwIiByeD0iNTYiIGZpbGw9IiMwRjE3MkEiLz4KCiAgPHBhdGggZD0iTTU4IDcySDExMlYxMjBIMTcwIiBzdHJva2U9IiNFMkU4RjAiIHN0cm9rZS13aWR0aD0iMTQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgogIDxwYXRoIGQ9Ik0xMTIgMTIwVjE3MkgxNzAiIHN0cm9rZT0iIzM4QkRGOCIgc3Ryb2tlLXdpZHRoPSIxNCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8%2BCgogIDxwYXRoIGQ9Ik0xNzAgMTIwVjcyIiBzdHJva2U9IiMzOEJERjgiIHN0cm9rZS13aWR0aD0iMTQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgogIDxwYXRoIGQ9Ik0xNDggOTRMMTcwIDcyTDE5MiA5NCIgc3Ryb2tlPSIjMzhCREY4IiBzdHJva2Utd2lkdGg9IjE0IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KCiAgPGNpcmNsZSBjeD0iNTgiIGN5PSI3MiIgcj0iMTIiIGZpbGw9IiNFMkU4RjAiLz4KICA8cmVjdCB4PSIxMDAiIHk9IjEwOCIgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiByeD0iNyIgZmlsbD0iI0UyRThGMCIvPgogIDxjaXJjbGUgY3g9IjE3MCIgY3k9IjEyMCIgcj0iMTIiIGZpbGw9IiMzOEJERjgiLz4KICA8Y2lyY2xlIGN4PSIxNzAiIGN5PSIxNzIiIHI9IjEyIiBmaWxsPSIjMzhCREY4Ii8%2BCjwvc3ZnPgo%3D&label=saronia&labelColor=black&color=gray&cacheSeconds=3600"></img></a>
  <a href="https://docs.basedpyright.com/latest/"><img alt="basedpyright strict" src="https://img.shields.io/badge/basedpyright-strict-black?logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAAFUAAAAyCAYAAAAtBJe4AAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9Txa%2BKgx1EFDJUJwuiIh2likWwUNoKrTqYXPoFTRqSFBdHwbXg4Mdi1cHFWVcHV0EQ%2FABxdnBSdJES%2F5cUWsR4cNyPd%2Fced%2B8AoV5mqtkxCaiaZSRjUTGTXRW7XtGDUQQQQZ%2FETD2eWkzDc3zdw8fXuzDP8j735%2BhXciYDfCLxHNMNi3iDeHbT0jnvEwdZUVKIz4knDLog8SPXZZffOBccFnhm0Egn54mDxGKhjeU2ZkVDJZ4hDimqRvlCxmWF8xZntVxlzXvyFwZy2kqK6zRHEMMS4khAhIwqSijDQphWjRQTSdqPeviHHX%2BCXDK5SmDkWEAFKiTHD%2F4Hv7s189NTblIgCnS%2B2PbHGNC1CzRqtv19bNuNE8D%2FDFxpLX%2BlDkQ%2BSa%2B1tNARMLANXFy3NHkPuNwBhp50yZAcyU9TyOeB9zP6piwweAv0rrm9Nfdx%2BgCkqavlG%2BDgEBgvUPa6x7u723v790yzvx%2B5A3LDePDLDQAAAAZiS0dEAAAAAAAA%2BUO7fwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB%2BgJHQ8wL%2BZrkusAAABpSURBVHja7dgxDoAgEEXBj%2FH%2BV8beUKwUmqwzF1jyslCQAAAAAJ2NJPOlOXdt5x72SlRR%2F%2BosvkNP7bxbbebaVNdfVFERVVRREVVUURFVVFERVVRRqVl9Us%2BPztJmrk11%2FUUFAAAAgJoLG3gJMmo%2FwwcAAAAASUVORK5CYII%3D&labelColor=edb641&style=flat-square"></img></a>
</div>

## Features

- Declarative API controller syntax
- Type-safe request/response handling
- Support for multiple HTTP clients (`rnet`, `aiohttp`, or custom)
- Comprehensive error handling
- Support for path parameters, query parameters, headers, body, JSON, form data, and file uploads
- Built on top of `msgspex` for fast serialization and `kungfu` for functional types (optional)

## Getting started

```bash
# Base installation
pip install saronia

# With rnet client
pip install saronia[rnet]

# With aiohttp client
pip install saronia[aiohttp]
```

```python
import asyncio
from dataclasses import dataclass
from uuid import UUID
from http import HTTPStatus

from kungfu import Error, Ok
from msgspex import Model
from saronia import API, APIError, APIResult, HTTPBearer, ModelStatusError, get, post

from rnet import Client
from saronia import RnetClient

Token = HTTPBearer


@dataclass
class Auth:
    token: Token


cool_api = API.endpoint("/coolapi/v1").bind_auth(Auth)


class ValidationError(Model, ModelStatusError[HTTPStatus.INTERNAL_SERVER_ERROR]):
    message: str


class NotFoundError(Model, ModelStatusError[HTTPStatus.NOT_FOUND]):
    message: str


class Book(Model):
    id: UUID
    name: str


class CreateBookDTO(Model, kw_only=True):
    book_id: UUID
    name: str


@cool_api("/books", auth=Token)
class BooksController:
    @get("/{book_id}", ValidationError, NotFoundError)
    async def get_book_by_id(self, book_uuid: UUID) -> Book:
        ...

    @post("/create", CreateBookDTO)  # or as a Result
    async def create_book(self) -> APIResult[Book, ValidationError | NotFoundError]:
        ...


books = BooksController()


async def main() -> None:
    client = Client()

    cool_api.build(RnetClient(client, base_url="https://api.example.com", request_timeout=45.0))
    cool_api.auth(token=Token("abc123..."))

    try:
        book = await books.get_book_by_id(book_uuid=UUID("12345678-1234-5678-1234-567812345678"))
        print("Book:", book)
    except APIError as error:
        print("API error:", error)
        return

    match await books.create_book(book_id=UUID("87654321-4321-8765-4321-876543218765"), name="New Book"):
        case Ok(new_book):
            print("New book:", new_book)
        case Error(error):
            print("API error:", error)


asyncio.run(main())
```

## License
saronia is [MIT licensed](https://github.com/luwqz1/saronia/blob/main/LICENSE)
