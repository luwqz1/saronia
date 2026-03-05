import asyncio
from uuid import UUID

from kungfu import Error
from msgspex import Model
from rnet import Client

from saronia import API, RnetClient, get, post


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


cool_api = API.endpoint("/api/v1")


@cool_api("/books")
class BooksController:
    @get("/{book_id}")
    async def get_book_by_id(self, book_id: UUID) -> "APIResult[Book, ValidationError | NotFoundError]": ...

    @post("/create", CreateBookDTO)
    async def create_book(self) -> "APIResult[Book, ValidationError | NotFoundError]": ...


books = BooksController()


async def main() -> None:
    client = Client()
    cool_api.build(RnetClient(client, base_url="https://httpbin.org"))

    # Example: get book by id
    result = await books.get_book_by_id(UUID("12345678-1234-5678-1234-567812345678"))

    match result:
        case Error(error):
            print(f"Error getting book: {error}")
        case _:
            book = result.unwrap()
            print(f"Book: {book.name}")

    # Example: create book
    match await books.create_book(id=UUID("87654321-4321-8765-4321-876543218765"), name="New Book"):
        case Error(error):
            print(f"Error creating book: {error}")
        case _:
            print("Book created successfully")


if __name__ == "__main__":
    asyncio.run(main())
