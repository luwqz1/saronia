import asyncio
from http import HTTPStatus
from uuid import UUID

from kungfu import Error
from msgspex import Model
from rnet import Client

from saronia import API, RnetClient, StatusError, get, post


class Book(Model):
    id: UUID
    name: str
    author: str


# Using StatusError decorator to associate errors with HTTP statuses
@StatusError[HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY]
class ValidationError(Model):
    message: str
    details: dict[str, list[str]] | None = None


@StatusError[HTTPStatus.NOT_FOUND]
class NotFoundError(Model):
    message: str
    resource: str


@StatusError[HTTPStatus.UNAUTHORIZED]
class UnauthorizedError(Model):
    message: str


@StatusError[HTTPStatus.INTERNAL_SERVER_ERROR]
class ServerError(Model):
    message: str
    trace_id: str | None = None


class CreateBookDTO(Model):
    name: str
    author: str


cool_api = API.endpoint("/api/v1")


@cool_api("/books")
class BooksController:
    @get("/{book_id}")
    async def get_book_by_id(self, book_id: UUID) -> "APIResult[Book, ValidationError | NotFoundError | UnauthorizedError]": ...

    @post("/create", CreateBookDTO)
    async def create_book(self) -> "APIResult[Book, ValidationError | ServerError]": ...


books = BooksController()


async def main() -> None:
    client = Client()
    cool_api.build(RnetClient(client, base_url="https://httpbin.org"))

    # Example 1: Handle specific error types
    result = await books.get_book_by_id(UUID("12345678-1234-5678-1234-567812345678"))

    match result:
        case Error(api_error):
            print(f"\n=== Error Details ===")
            print(f"Status: {api_error.status.value} {api_error.status.phrase}")
            print(f"Method: {api_error.method}")
            print(f"Path: {api_error.path}")
            print(f"Request ID: {api_error.request_id}")
            print(f"Is Client Error: {api_error.is_client_error}")
            print(f"Is Server Error: {api_error.is_server_error}")

            # Pattern match on specific error types
            match api_error.error:
                case NotFoundError(message=msg, resource=res):
                    print(f"\nResource not found: {res}")
                    print(f"Message: {msg}")
                case ValidationError(message=msg, details=details):
                    print(f"\nValidation failed: {msg}")
                    if details:
                        print(f"Details: {details}")
                case UnauthorizedError(message=msg):
                    print(f"\nUnauthorized: {msg}")
                case _:
                    print(f"\nUnexpected error: {api_error.error}")
        case _:
            book = result.unwrap()
            print(f"\n=== Success ===")
            print(f"Book: {book.name} by {book.author}")

    # Example 2: Create book with error handling
    print("\n\n=== Creating Book ===")
    create_result = await books.create_book(name="The Great Gatsby", author="F. Scott Fitzgerald")

    match create_result:
        case Error(api_error):
            print(f"Failed to create book: {api_error}")

            if isinstance(api_error.error, ValidationError):
                print(f"Validation error: {api_error.error.message}")
                if api_error.error.details:
                    for field, errors in api_error.error.details.items():
                        print(f"  {field}: {', '.join(errors)}")
            elif isinstance(api_error.error, ServerError):
                print(f"Server error: {api_error.error.message}")
                if api_error.error.trace_id:
                    print(f"Trace ID: {api_error.error.trace_id}")
        case _:
            book = create_result.unwrap()
            print(f"Book created: {book.name} by {book.author}")


if __name__ == "__main__":
    asyncio.run(main())
