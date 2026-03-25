"""Example demonstrating the saronia authentication system."""

import typing
from http import HTTPStatus

import msgspex
from attr import dataclass

from saronia import API, APIResult, HeaderAPIKey, HTTPBearer, ModelStatusError, QueryAPIKey, get, post


# Define auth classes
class ApiKeyAuth(HeaderAPIKey["x-api-key"]):
    pass


class BearerAuth(HTTPBearer):
    pass


class TokenAuth(QueryAPIKey["token"]):
    pass


@dataclass
class Authorization:
    api_key: ApiKeyAuth | None = None
    token: TokenAuth | None = None
    bearer: BearerAuth | None = None


# Define models
class User(msgspex.Model):
    id: int
    name: str


class ErrorResponse(msgspex.Model, ModelStatusError[HTTPStatus.UNAUTHORIZED]):
    detail: str


# Create API
api = API.endpoint("/api/v1").bind_auth(Authorization)


USERS_AUTH = ApiKeyAuth


# Controller with API key auth by default
@api("/users", auth=USERS_AUTH)
class UsersController:
    @get("/{id}")
    async def get_user(self, id: int) -> APIResult[User, ErrorResponse]:
        """Requires ApiKeyAuth (inherited from controller)."""
        ...

    @post("/", auth=None)
    async def create_user(self, name: str) -> APIResult[User, ErrorResponse]:
        """Public endpoint (auth=None)."""
        ...

    @get("/{id}/profile", auth=BearerAuth)
    async def get_profile(self, id: int) -> APIResult[User, ErrorResponse]:
        """Accepts ApiKeyAuth OR BearerAuth (method auth ORs with controller)."""
        ...

    @post("/{id}/delete", auth=~USERS_AUTH & BearerAuth)
    async def delete_user(self, id: int) -> APIResult[User, ErrorResponse]:
        """Requires ONLY BearerAuth (negates controller auth)."""
        ...


# Controller requiring both API key and Bearer
@api("/admin", auth=ApiKeyAuth & BearerAuth)
class AdminController:
    @get("/stats")
    async def get_stats(self) -> APIResult[dict[str, typing.Any], ErrorResponse]:
        """Requires both ApiKeyAuth AND BearerAuth."""
        ...

    @get("/public", auth=None)
    async def public_stats(self) -> APIResult[dict[str, typing.Any], ErrorResponse]:
        """Public endpoint."""
        ...


# Controller with no default auth
@api("/public")
class PublicController:
    @get("/info")
    async def get_info(self) -> APIResult[dict[str, typing.Any], ErrorResponse]:
        """Public endpoint (no auth)."""
        ...

    @get("/protected", auth=TokenAuth)
    async def protected_info(self) -> APIResult[dict[str, typing.Any], ErrorResponse]:
        """Requires TokenAuth."""
        ...


# Usage example
async def main():
    import aiohttp

    from saronia.client.aiohttp_client import AiohttpClient

    async with aiohttp.ClientSession(base_url="https://api.example.com") as session:
        client = AiohttpClient(session)

        api.build(client)
        api.auth(
            api_key=ApiKeyAuth("my-secret-key"),
            token=TokenAuth("my-api-token"),
            bearer=BearerAuth("my-bearer-token"),
        )

        users = UsersController()

        result = await users.get_user(id=123)

        if result:
            user = result.unwrap()
            print(f"User: {user.name}")
        else:
            error = result.unwrap_err()
            print(f"Error: {error}")
