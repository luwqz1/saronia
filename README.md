# saronia

A lightweight, spec-driven builder for API clients and controllers.

## Installation

```bash
# Base installation
pip install saronia

# With rnet client
pip install saronia[rnet]

# With aiohttp client
pip install saronia[aiohttp]
```

## Features

- Declarative API controller syntax
- Type-safe request/response handling with `APIResult`
- Support for multiple HTTP clients (rnet, aiohttp, or custom)
- Comprehensive error handling with `StatusError`
- Support for path parameters, query params, headers, JSON, form data, and file uploads
- Built on top of `msgspex` for fast serialization and `kungfu` for Result types

## Quick Start

```python
import asyncio
from uuid import UUID

from kungfu import Error
from msgspex import Model
from saronia import API, APIResult, get, post

# With rnet
from rnet import Client
from saronia import RnetClient

# Or with aiohttp
# from aiohttp import ClientSession
# from saronia import AiohttpClient

cool_api = API.endpoint("/coolapi/v1")


class Book(Model):
    id: UUID
    name: str


class ValidationError(Model):
    message: str


class NotFoundError(Model):
    message: str


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
    # Using rnet
    client = Client()
    cool_api.build(RnetClient(client, base_url="https://api.example.com"))

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

## Error Handling

saronia provides comprehensive error handling following OpenAPI best practices:

```python
from http import HTTPStatus
from saronia import StatusError

# Associate error types with HTTP status codes
class NotFoundError(Model, StatusError[HTTPStatus.NOT_FOUND]):
    message: str
    resource: str


class ValidationError(Model, StatusError[HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY]):
    message: str
    details: dict[str, list[str]] | None = None

# Use in controller
@get("/{book_id}")
async def get_book(self, book_id: UUID) -> APIResult[Book, NotFoundError | ValidationError]:
    ...

# Handle errors
result = await books.get_book(book_id)

match result:
    case Error(api_error):
        print(f"Status: {api_error.status}")  # HTTPStatus enum
        print(f"Path: {api_error.path}")  # Request path
        print(f"Request ID: {api_error.request_id}")  # For tracing
        print(f"Is client error: {api_error.is_client_error}")  # 4xx
        print(f"Is server error: {api_error.is_server_error}")  # 5xx

        # Pattern match on specific error types
        match api_error.error:
            case NotFoundError(message=msg):
                print(f"Not found: {msg}")
            case ValidationError(message=msg, details=details):
                print(f"Validation failed: {msg}")
    case _:
        book = result.unwrap()
        print(f"Success: {book.name}")
```

## Custom HTTP Client

You can implement your own HTTP client by inheriting from `ABCClient`:

```python
from saronia.client.abc import ABCClient

class MyCustomClient(ABCClient):
    async def request(self, path, method, *, errors, response_type, ...):
        # Your implementation
        ...
```
