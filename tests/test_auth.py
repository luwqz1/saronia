import threading
import time
from http import HTTPStatus

import msgspex
import pytest
import pytest_asyncio
import uvicorn
from fastapi import FastAPI, Header, HTTPException

from saronia import API, APIResult, HeaderAPIKey, HTTPBearer, StatusError, get
from saronia.client.aiohttp_client import AiohttpClient


class ApiKeyAuth(HeaderAPIKey["x-api-key"]):
    pass


class BearerAuth(HTTPBearer):
    pass


class AUTH(msgspex.Model):
    api_key: ApiKeyAuth | None = None
    token: BearerAuth | None = None


# FastAPI test server
app = FastAPI()


@app.get("/api/test/public")
async def public_endpoint():
    return {"message": "public"}


@app.get("/api/test/api-key")
async def api_key_endpoint(x_api_key: str = Header()):
    if x_api_key != "secret123":
        raise HTTPException(401, "Invalid API key")
    return {"message": "api-key-ok"}


@app.get("/api/test/bearer")
async def bearer_endpoint(authorization: str = Header()):
    if authorization != "Bearer token456":
        raise HTTPException(401, "Invalid bearer token")
    return {"message": "bearer-ok"}


@app.get("/api/test/both")
async def both_endpoint(
    x_api_key: str | None = Header(None),
    authorization: str | None = Header(None),
):
    if x_api_key == "secret123" or authorization == "Bearer token456":
        return {"message": "both-ok"}
    raise HTTPException(401, "Auth required")


class Response(msgspex.Model):
    message: str


class ErrorResponse(msgspex.Model, StatusError[HTTPStatus.UNAUTHORIZED]):
    detail: str


api = API.endpoint("/api").bind_auth(AUTH)


@api("/test", auth=ApiKeyAuth)
class TestController:
    @get("/public", auth=None)
    async def public(self) -> APIResult[Response, ErrorResponse]: ...

    @get("/api-key")
    async def api_key_only(self) -> APIResult[Response, ErrorResponse]: ...

    @get("/bearer", auth=BearerAuth)
    async def bearer_or_api_key(self) -> APIResult[Response, ErrorResponse]: ...

    @get("/both", auth=ApiKeyAuth & BearerAuth)
    async def both_required(self) -> APIResult[Response, ErrorResponse]: ...


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 18766


@pytest.fixture(scope="session", autouse=True)
def fastapi_server():
    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    import socket

    max_retries = 50
    for _ in range(max_retries):
        try:
            with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=1):
                break
        except ConnectionRefusedError, OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Server failed to start on {SERVER_HOST}:{SERVER_PORT}")

    yield
    server.should_exit = True


@pytest_asyncio.fixture
async def client():
    import aiohttp

    async with aiohttp.ClientSession(base_url="http://localhost:18766") as session:
        yield AiohttpClient(session)


@pytest.mark.asyncio
async def test_public_endpoint(client):
    api.build(client)
    result = await TestController().public()
    assert result
    assert result.unwrap().message == "public"


@pytest.mark.asyncio
async def test_api_key_auth(client):
    api.build(client)
    api.auth(ApiKeyAuth("secret123"))
    result = await TestController().api_key_only()
    assert result
    assert result.unwrap().message == "api-key-ok"


@pytest.mark.asyncio
async def test_bearer_or_api_key(client):
    api.build(client)
    api.auth(token=BearerAuth("token456"))
    result = await TestController().bearer_or_api_key()
    assert result
    assert result.unwrap().message == "bearer-ok"


@pytest.mark.asyncio
async def test_both_required(client):
    api.build(client)
    api.auth(api_key=ApiKeyAuth("secret123"), token=BearerAuth("token456"))
    result = await TestController().both_required()
    assert result
    assert result.unwrap().message == "both-ok"
