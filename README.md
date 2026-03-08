# saronia

A lightweight, spec-driven builder for API clients and controllers.

- Declarative API controller syntax
- Type-safe request/response handling with `APIResult`
- Support for multiple HTTP clients (`rnet`, `aiohttp`, or custom)
- Comprehensive error handling with `StatusError` mixin
- Support for path parameters, query parameters, headers, body, JSON, form data, and file uploads
- Built on top of `msgspex` for fast serialization and `kungfu` for functional types

## Getting Started

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
from uuid import UUID
from http import HTTPStatus

from kungfu import Error
from msgspex import Model
from saronia import API, APIResult, HTTPBearer, StatusError, get, post

from rnet import Client
from saronia import RnetClient

cool_api = API.endpoint("/coolapi/v1").bind_auth(HTTPBearer)


class ValidationError(Model, StatusError[HTTPStatus.INTERNAL_SERVER_ERROR]):
    message: str


class NotFoundError(Model, StatusError[HTTPStatus.NOT_FOUND]):
    message: str


class Book(Model):
    id: UUID
    name: str


class CreateBookDTO(Model):
    id: UUID
    name: str


@cool_api("/books")
class BooksController:
    @get("/{book_id}")
    async def get_book_by_id(self, book_id: UUID) -> APIResult[Book, ValidationError | NotFoundError]:
        ...

    @post("/create", CreateBookDTO)
    async def create_book(self) -> APIResult[Book, ValidationError | NotFoundError]:
        ...


books = BooksController()


async def main() -> None:
    client = Client()

    cool_api.build(RnetClient(client, base_url="https://api.example.com", request_timeout=45.0))
    cool_api.auth(token="abc123...")

    # Or using aiohttp
    # async with ClientSession() as session:
    #     cool_api.build(AiohttpClient(session, base_url="https://api.example.com"))

    book = (await books.get_book_by_id(UUID("12345678-1234-5678-1234-567812345678"))).unwrap()
    print(f"Book: {book.name}")

    match await books.create_book(id=UUID("87654321-4321-8765-4321-876543218765"), name="New Book"):
        case Error(error):
            print(f"Error: {error}")


asyncio.run(main())
```

## License
saronia is [MIT licensed](https://github.com/luwqz1/saronia/blob/main/LICENSE)
