"""Comprehensive tests for saronia using a real FastAPI server.
Tests both AiohttpClient and RnetClient across all parameter types and error scenarios."""

import base64
import io
import threading
import time
import typing
from http import HTTPMethod, HTTPStatus

import kungfu
import pytest
import pytest_asyncio
import uvicorn
from fastapi import FastAPI, File, Form, Header, Path, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from msgspex import Model

import saronia
from saronia import API, AiohttpClient, APIResult, RnetClient, delete, get, patch, post, put
from saronia.error import StatusError, UnknownError
from saronia.security import (
    CookieAPIKey,
    HeaderAPIKey,
    HTTPBasic,
    HTTPBearer,
    QueryAPIKey,
)
from saronia.tools.parameters import (
    JSON,
    FileBuffer,
    URLencoded,
)
from saronia.tools.parameters import (
    Header as SHeader,
)
from saronia.tools.parameters import (
    Path as SPath,
)
from saronia.tools.parameters import (
    Query as SQuery,
)
from saronia.tools.parameters import (
    XHeader as SXHeader,
)

app = FastAPI()


@app.get("/items/{item_id}")
async def server_get_item(
    item_id: int = Path(...),
    q: str | None = Query(None),
    tag: str | None = Query(None),
):
    return {"item_id": item_id, "q": q, "tag": tag}


@app.get("/items")
async def server_list_items(
    limit: int = Query(10),
    offset: int = Query(0),
    search: str | None = Query(None),
):
    return {"limit": limit, "offset": offset, "search": search, "items": []}


@app.post("/items", status_code=201)
async def server_create_item(request: Request):
    body = await request.json()
    return {"id": 1, **body}


@app.put("/items/{item_id}")
async def server_update_item(item_id: int, request: Request):
    body = await request.json()
    return {"item_id": item_id, **body}


@app.patch("/items/{item_id}")
async def server_patch_item(item_id: int, request: Request):
    body = await request.json()
    return {"item_id": item_id, "patched": True, **body}


@app.delete("/items/{item_id}")
async def server_delete_item(item_id: int):
    return {"deleted": True, "item_id": item_id}


@app.get("/headers-echo")
async def server_echo_headers(
    x_token: str | None = Header(None),
    x_user_id: str | None = Header(None),
):
    return {"x_token": x_token, "x_user_id": x_user_id}


@app.get("/x-headers-echo")
async def server_echo_x_headers(
    x_token: str | None = Header(None),
    x_correlation_id: str | None = Header(None),
):
    return {"x_token": x_token, "x_correlation_id": x_correlation_id}


@app.post("/form")
async def server_form(username: str = Form(...), password: str = Form(...)):
    return {"username": username, "password": password}


@app.post("/upload")
async def server_upload(file: UploadFile = File(...), description: str = Form("")):
    content = await file.read()
    return {
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
        "description": description,
    }


@app.get("/errors/400")
async def server_error_400():
    return JSONResponse({"message": "bad request"}, status_code=400)


@app.get("/errors/404")
async def server_error_404():
    return JSONResponse({"message": "not found"}, status_code=404)


@app.get("/errors/422")
async def server_error_422():
    return JSONResponse(
        {"message": "unprocessable entity", "details": {"field": ["required"]}},
        status_code=422,
    )


@app.get("/errors/500")
async def server_error_500():
    return JSONResponse({"message": "internal server error"}, status_code=500)


@app.get("/errors/502")
async def server_error_502():
    return Response(status_code=502)


@app.get("/errors/empty")
async def server_error_empty():
    return Response(status_code=404)


@app.get("/request-id")
async def server_request_id():
    return JSONResponse({"ok": True}, headers={"X-Request-ID": "test-req-42"})


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 18765
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


@pytest.fixture(scope="session", autouse=True)
def fastapi_server():
    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    import socket

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=0.5):
                break
        except OSError:
            time.sleep(0.05)
    else:
        pytest.fail("Test server did not start in time")

    yield
    server.should_exit = True
    thread.join(timeout=5)


class ItemResponse(Model):
    item_id: int
    q: str | None = None
    tag: str | None = None


class ListResponse(Model):
    limit: int
    offset: int
    items: list
    search: str | None = None


class CreateItemResponse(Model):
    id: int
    name: str
    price: float
    in_stock: bool


class UpdateItemResponse(Model):
    item_id: int
    name: str
    price: float


class PatchItemResponse(Model):
    item_id: int
    patched: bool
    name: str


class DeleteResponse(Model):
    deleted: bool
    item_id: int


class HeadersResponse(Model):
    x_token: str | None = None
    x_user_id: str | None = None


class XHeadersResponse(Model):
    x_token: str | None = None
    x_correlation_id: str | None = None


class FormResponse(Model):
    username: str
    password: str


class UploadResponse(Model):
    filename: str
    size: int
    content_type: str | None
    description: str


class ErrorMessage(Model):
    message: str


class ErrorDetail(Model):
    message: str
    details: dict


class OkResponse(Model):
    ok: bool


class BadGatewayError(StatusError[502]):
    """Something went wrong."""


aiohttp_api = API.endpoint("")


@aiohttp_api("/items")
class AiohttpItemsController:
    @get("/{item_id}")
    async def get_item(
        self,
        item_id: SPath[int],
    ) -> APIResult[ItemResponse, ErrorMessage]: ...

    @get("/{item_id}")
    async def get_item_with_query(
        self,
        item_id: SPath[int],
        q: SQuery[str],
        tag: SQuery[str],
    ) -> APIResult[ItemResponse, ErrorMessage]: ...

    @get("")
    async def list_items(
        self,
        limit: SQuery[int] = 10,
        offset: SQuery[int] = 0,
    ) -> APIResult[ListResponse, ErrorMessage]: ...

    @get("")
    async def list_items_with_search(
        self,
        limit: SQuery[int],
        offset: SQuery[int],
        search: SQuery[str],
    ) -> APIResult[ListResponse, ErrorMessage]: ...

    @post("")
    async def create_item(
        self,
        name: JSON[str],
        price: JSON[float],
        in_stock: JSON[bool],
    ) -> APIResult[CreateItemResponse, ErrorMessage]: ...

    @put("/{item_id}")
    async def update_item(
        self,
        item_id: SPath[int],
        name: JSON[str],
        price: JSON[float],
    ) -> APIResult[UpdateItemResponse, ErrorMessage]: ...

    @patch("/{item_id}")
    async def patch_item(
        self,
        item_id: SPath[int],
        name: JSON[str],
    ) -> APIResult[PatchItemResponse, ErrorMessage]: ...

    @delete("/{item_id}")
    async def delete_item(
        self,
        item_id: SPath[int],
    ) -> APIResult[DeleteResponse, ErrorMessage]: ...


aiohttp_headers_api = API.endpoint("")


@aiohttp_headers_api("/headers-echo")
class AiohttpHeadersController:
    @get("")
    async def echo_headers(
        self,
        x_token: SHeader[str],
        x_user_id: SHeader[str],
    ) -> APIResult[HeadersResponse, ErrorMessage]: ...


aiohttp_xheaders_api = API.endpoint("")


@aiohttp_xheaders_api("/x-headers-echo")
class AiohttpXHeadersController:
    @get("")
    async def echo_x_headers(
        self,
        token: SXHeader[str],
        correlation_id: SXHeader[str],
    ) -> APIResult[XHeadersResponse, ErrorMessage]: ...


aiohttp_form_api = API.endpoint("")


@aiohttp_form_api("/form")
class AiohttpFormController:
    @post("")
    async def submit_form(
        self,
        username: URLencoded[str],
        password: URLencoded[str],
    ) -> APIResult[FormResponse, ErrorMessage]: ...


aiohttp_upload_api = API.endpoint("")


@aiohttp_upload_api("/upload")
class AiohttpUploadController:
    @post("")
    async def upload(
        self,
        file: FileBuffer,
        description: URLencoded[str] = "",
    ) -> APIResult[UploadResponse, ErrorMessage]: ...


aiohttp_errors_api = API.endpoint("/errors")


@aiohttp_errors_api("")
class AiohttpErrorsController:
    @get("/400")
    async def get_400(self) -> APIResult[None, ErrorMessage]: ...

    @get("/404")
    async def get_404(self) -> APIResult[None, ErrorMessage]: ...

    @get("/422")
    async def get_422(self) -> APIResult[None, ErrorDetail]: ...

    @get("/500")
    async def get_500(self) -> APIResult[None, ErrorMessage]: ...

    @get("/502")
    async def get_502(self) -> APIResult[None, BadGatewayError]: ...

    @get("/empty")
    async def get_empty(self) -> APIResult[None, ErrorMessage]: ...


aiohttp_misc_api = API.endpoint("")


@aiohttp_misc_api("/request-id")
class AiohttpMiscController:
    @get("")
    async def get_with_request_id(self) -> APIResult[OkResponse, ErrorMessage]: ...


rnet_api = API.endpoint("")


@rnet_api("/items")
class RnetItemsController:
    @get("/{item_id}")
    async def get_item(
        self,
        item_id: SPath[int],
    ) -> APIResult[ItemResponse, ErrorMessage]: ...

    @get("/{item_id}")
    async def get_item_with_query(
        self,
        item_id: SPath[int],
        q: SQuery[str],
        tag: SQuery[str],
    ) -> APIResult[ItemResponse, ErrorMessage]: ...

    @get("")
    async def list_items(
        self,
        limit: SQuery[int] = 10,
        offset: SQuery[int] = 0,
    ) -> APIResult[ListResponse, ErrorMessage]: ...

    @get("")
    async def list_items_with_search(
        self,
        limit: SQuery[int],
        offset: SQuery[int],
        search: SQuery[str],
    ) -> APIResult[ListResponse, ErrorMessage]: ...

    @post("")
    async def create_item(
        self,
        name: JSON[str],
        price: JSON[float],
        in_stock: JSON[bool],
    ) -> APIResult[CreateItemResponse, ErrorMessage]: ...

    @put("/{item_id}")
    async def update_item(
        self,
        item_id: SPath[int],
        name: JSON[str],
        price: JSON[float],
    ) -> APIResult[UpdateItemResponse, ErrorMessage]: ...

    @patch("/{item_id}")
    async def patch_item(
        self,
        item_id: SPath[int],
        name: JSON[str],
    ) -> APIResult[PatchItemResponse, ErrorMessage]: ...

    @delete("/{item_id}")
    async def delete_item(
        self,
        item_id: SPath[int],
    ) -> APIResult[DeleteResponse, ErrorMessage]: ...


rnet_headers_api = API.endpoint("")


@rnet_headers_api("/headers-echo")
class RnetHeadersController:
    @get("")
    async def echo_headers(
        self,
        x_token: SHeader[str],
        x_user_id: SHeader[str],
    ) -> APIResult[HeadersResponse, ErrorMessage]: ...


rnet_xheaders_api = API.endpoint("")


@rnet_xheaders_api("/x-headers-echo")
class RnetXHeadersController:
    @get("")
    async def echo_x_headers(
        self,
        token: SXHeader[str],
        correlation_id: SXHeader[str],
    ) -> APIResult[XHeadersResponse, ErrorMessage]: ...


rnet_form_api = API.endpoint("")


@rnet_form_api("/form")
class RnetFormController:
    @post("")
    async def submit_form(
        self,
        username: URLencoded[str],
        password: URLencoded[str],
    ) -> APIResult[FormResponse, ErrorMessage]: ...


rnet_upload_api = API.endpoint("")


@rnet_upload_api("/upload")
class RnetUploadController:
    @post("")
    async def upload(
        self,
        file: FileBuffer,
        description: URLencoded[str] = "",
    ) -> APIResult[UploadResponse, ErrorMessage]: ...


rnet_errors_api = API.endpoint("/errors")  # base prefix is prepended to controller path on build()


@rnet_errors_api("")
class RnetErrorsController:
    @get("/400")
    async def get_400(self) -> APIResult[None, ErrorMessage]: ...

    @get("/404")
    async def get_404(self) -> APIResult[None, ErrorMessage]: ...

    @get("/422")
    async def get_422(self) -> APIResult[None, ErrorDetail]: ...

    @get("/500")
    async def get_500(self) -> APIResult[None, ErrorMessage]: ...

    @get("/502")
    async def get_502(self) -> APIResult[None, BadGatewayError]: ...

    @get("/empty")
    async def get_empty(self) -> APIResult[None, ErrorMessage]: ...


rnet_misc_api = API.endpoint("")


@rnet_misc_api("/request-id")
class RnetMiscController:
    @get("")
    async def get_with_request_id(self) -> APIResult[OkResponse, ErrorMessage]: ...


@pytest_asyncio.fixture
async def aiohttp_items():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_api.build(AiohttpClient(session))
        yield AiohttpItemsController()


@pytest_asyncio.fixture
async def aiohttp_headers():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_headers_api.build(AiohttpClient(session))
        yield AiohttpHeadersController()


@pytest_asyncio.fixture
async def aiohttp_xheaders():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_xheaders_api.build(AiohttpClient(session))
        yield AiohttpXHeadersController()


@pytest_asyncio.fixture
async def aiohttp_form():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_form_api.build(AiohttpClient(session))
        yield AiohttpFormController()


@pytest_asyncio.fixture
async def aiohttp_upload():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_upload_api.build(AiohttpClient(session))
        yield AiohttpUploadController()


@pytest_asyncio.fixture
async def aiohttp_errors():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_errors_api.build(AiohttpClient(session))
        yield AiohttpErrorsController()


@pytest_asyncio.fixture
async def aiohttp_misc():
    import aiohttp

    async with aiohttp.ClientSession(base_url=BASE_URL) as session:
        aiohttp_misc_api.build(AiohttpClient(session))
        yield AiohttpMiscController()


@pytest_asyncio.fixture
async def rnet_items():
    import rnet

    rnet_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetItemsController()


@pytest_asyncio.fixture
async def rnet_headers():
    import rnet

    rnet_headers_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetHeadersController()


@pytest_asyncio.fixture
async def rnet_xheaders():
    import rnet

    rnet_xheaders_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetXHeadersController()


@pytest_asyncio.fixture
async def rnet_form():
    import rnet

    rnet_form_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetFormController()


@pytest_asyncio.fixture
async def rnet_upload():
    import rnet

    rnet_upload_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetUploadController()


@pytest_asyncio.fixture
async def rnet_errors():
    import rnet

    rnet_errors_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetErrorsController()


@pytest_asyncio.fixture
async def rnet_misc():
    import rnet

    rnet_misc_api.build(RnetClient(rnet.Client(), base_url=BASE_URL))
    yield RnetMiscController()


def assert_ok(result: typing.Any) -> typing.Any:
    if isinstance(result, kungfu.Error):
        pytest.fail(f"Expected Ok but got Error: {result.error}")
    return result.unwrap()


def assert_error(result: typing.Any) -> saronia.APIError:
    if isinstance(result, kungfu.Ok):
        pytest.fail(f"Expected Error but got Ok: {result.unwrap()}")
    api_err = result.error
    assert isinstance(api_err, saronia.APIError)
    return api_err


class TestAiohttpGetItemNoQuery:
    @pytest.mark.asyncio
    async def test_returns_item(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.get_item(item_id=42))
        assert item.item_id == 42

    @pytest.mark.asyncio
    async def test_different_ids(self, aiohttp_items):
        for item_id in (1, 100, 999):
            item = assert_ok(await aiohttp_items.get_item(item_id=item_id))
            assert item.item_id == item_id


class TestAiohttpGetItemWithQuery:
    @pytest.mark.asyncio
    async def test_both_query_params_sent(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.get_item_with_query(item_id=7, q="hello", tag="python"))
        assert item.item_id == 7
        assert item.q == "hello"
        assert item.tag == "python"

    @pytest.mark.asyncio
    async def test_query_params_different_values(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.get_item_with_query(item_id=1, q="search", tag="test"))
        assert item.q == "search"
        assert item.tag == "test"


class TestAiohttpListItems:
    @pytest.mark.asyncio
    async def test_default_pagination(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.list_items())
        assert data.limit == 10
        assert data.offset == 0

    @pytest.mark.asyncio
    async def test_custom_pagination(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.list_items(limit=5, offset=20))
        assert data.limit == 5
        assert data.offset == 20

    @pytest.mark.asyncio
    async def test_with_search_param(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.list_items_with_search(limit=10, offset=0, search="widget"))
        assert data.search == "widget"
        assert data.limit == 10


class TestAiohttpPostJson:
    @pytest.mark.asyncio
    async def test_create_in_stock(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.create_item(name="Widget", price=9.99, in_stock=True))
        assert item.id == 1
        assert item.name == "Widget"
        assert item.price == 9.99
        assert item.in_stock is True

    @pytest.mark.asyncio
    async def test_create_out_of_stock(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.create_item(name="Rare", price=0.01, in_stock=False))
        assert item.in_stock is False

    @pytest.mark.asyncio
    async def test_create_preserves_name(self, aiohttp_items):
        item = assert_ok(await aiohttp_items.create_item(name="Special Item", price=100.0, in_stock=True))
        assert item.name == "Special Item"


class TestAiohttpPut:
    @pytest.mark.asyncio
    async def test_update_item(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.update_item(item_id=5, name="Updated", price=19.99))
        assert data.item_id == 5
        assert data.name == "Updated"
        assert data.price == 19.99

    @pytest.mark.asyncio
    async def test_update_preserves_item_id(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.update_item(item_id=99, name="X", price=1.0))
        assert data.item_id == 99


class TestAiohttpPatch:
    @pytest.mark.asyncio
    async def test_patch_sets_patched_flag(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.patch_item(item_id=3, name="Patched"))
        assert data.item_id == 3
        assert data.patched is True
        assert data.name == "Patched"


class TestAiohttpDelete:
    @pytest.mark.asyncio
    async def test_delete_returns_deleted(self, aiohttp_items):
        data = assert_ok(await aiohttp_items.delete_item(item_id=99))
        assert data.deleted is True
        assert data.item_id == 99

    @pytest.mark.asyncio
    async def test_delete_different_ids(self, aiohttp_items):
        for item_id in (1, 42, 999):
            data = assert_ok(await aiohttp_items.delete_item(item_id=item_id))
            assert data.item_id == item_id


class TestAiohttpHeaders:
    @pytest.mark.asyncio
    async def test_headers_echoed(self, aiohttp_headers):
        data = assert_ok(await aiohttp_headers.echo_headers(x_token="secret123", x_user_id="user-456"))
        assert data.x_token == "secret123"
        assert data.x_user_id == "user-456"

    @pytest.mark.asyncio
    async def test_headers_different_values(self, aiohttp_headers):
        data = assert_ok(await aiohttp_headers.echo_headers(x_token="tkn", x_user_id="uid"))
        assert data.x_token == "tkn"
        assert data.x_user_id == "uid"


class TestAiohttpXHeaders:
    @pytest.mark.asyncio
    async def test_x_headers_sent(self, aiohttp_xheaders):
        # token: SXHeader[str] → sends X-Token, correlation_id: SXHeader[str] → sends X-Correlation-Id
        data = assert_ok(await aiohttp_xheaders.echo_x_headers(token="my-token", correlation_id="req-123"))
        assert data.x_token == "my-token"
        assert data.x_correlation_id == "req-123"


class TestAiohttpForm:
    @pytest.mark.asyncio
    async def test_form_submitted(self, aiohttp_form):
        data = assert_ok(await aiohttp_form.submit_form(username="alice", password="s3cr3t"))
        assert data.username == "alice"
        assert data.password == "s3cr3t"

    @pytest.mark.asyncio
    async def test_form_different_credentials(self, aiohttp_form):
        data = assert_ok(await aiohttp_form.submit_form(username="bob", password="pass"))
        assert data.username == "bob"


class TestAiohttpUpload:
    @pytest.mark.asyncio
    async def test_upload_with_description(self, aiohttp_upload):
        content = b"Hello, file content!"
        data = assert_ok(await aiohttp_upload.upload(file=io.BytesIO(content), description="test upload"))
        assert data.size == len(content)
        assert data.description == "test upload"

    @pytest.mark.asyncio
    async def test_upload_default_description(self, aiohttp_upload):
        content = b"minimal content"
        data = assert_ok(await aiohttp_upload.upload(file=io.BytesIO(content)))
        assert data.size == len(content)
        assert data.description == ""

    @pytest.mark.asyncio
    async def test_upload_size_matches(self, aiohttp_upload):
        content = b"x" * 1024
        data = assert_ok(await aiohttp_upload.upload(file=io.BytesIO(content)))
        assert data.size == 1024


class TestAiohttpErrors:
    @pytest.mark.asyncio
    async def test_400_parsed_as_error_message(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_400())
        assert err.status == HTTPStatus.BAD_REQUEST
        assert err.status.is_client_error
        assert not err.status.is_server_error
        assert isinstance(err.error, ErrorMessage)
        assert err.error.message == "bad request"

    @pytest.mark.asyncio
    async def test_404_parsed_as_error_message(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_404())
        assert err.status == HTTPStatus.NOT_FOUND
        assert err.status.is_client_error
        assert isinstance(err.error, ErrorMessage)
        assert err.error.message == "not found"

    @pytest.mark.asyncio
    async def test_422_parsed_as_error_detail(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_422())
        assert err.status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert isinstance(err.error, ErrorDetail)
        assert err.error.message == "unprocessable entity"
        assert "field" in err.error.details

    @pytest.mark.asyncio
    async def test_500_is_server_error(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_500())
        assert err.status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert err.status.is_server_error
        assert not err.status.is_client_error
        assert isinstance(err.error, ErrorMessage)

    @pytest.mark.asyncio
    async def test_502_status_error(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_502())
        assert err.status == HTTPStatus.BAD_GATEWAY
        assert err.status.is_server_error
        assert not err.status.is_client_error
        assert isinstance(err.error, BadGatewayError)

    @pytest.mark.asyncio
    async def test_empty_body_error_is_none(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_empty())
        assert err.status == HTTPStatus.NOT_FOUND
        assert isinstance(err.error, UnknownError)
        assert not err.error.payload

    @pytest.mark.asyncio
    async def test_error_carries_http_method(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_400())
        assert err.method == HTTPMethod.GET

    @pytest.mark.asyncio
    async def test_error_carries_path(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_404())
        assert err.path is not None
        assert "404" in err.path


class TestAiohttpMisc:
    @pytest.mark.asyncio
    async def test_ok_response_parsed(self, aiohttp_misc):
        data = assert_ok(await aiohttp_misc.get_with_request_id())
        assert data.ok is True


class TestRnetGetItemNoQuery:
    @pytest.mark.asyncio
    async def test_returns_item(self, rnet_items):
        item = assert_ok(await rnet_items.get_item(item_id=42))
        assert item.item_id == 42

    @pytest.mark.asyncio
    async def test_different_ids(self, rnet_items):
        for item_id in (1, 100, 999):
            item = assert_ok(await rnet_items.get_item(item_id=item_id))
            assert item.item_id == item_id


class TestRnetGetItemWithQuery:
    @pytest.mark.asyncio
    async def test_both_query_params_sent(self, rnet_items):
        item = assert_ok(await rnet_items.get_item_with_query(item_id=7, q="hello", tag="python"))
        assert item.item_id == 7
        assert item.q == "hello"
        assert item.tag == "python"

    @pytest.mark.asyncio
    async def test_query_params_different_values(self, rnet_items):
        item = assert_ok(await rnet_items.get_item_with_query(item_id=1, q="search", tag="test"))
        assert item.q == "search"
        assert item.tag == "test"


class TestRnetListItems:
    @pytest.mark.asyncio
    async def test_default_pagination(self, rnet_items):
        data = assert_ok(await rnet_items.list_items())
        assert data.limit == 10
        assert data.offset == 0

    @pytest.mark.asyncio
    async def test_custom_pagination(self, rnet_items):
        data = assert_ok(await rnet_items.list_items(limit=25, offset=50))
        assert data.limit == 25
        assert data.offset == 50

    @pytest.mark.asyncio
    async def test_with_search_param(self, rnet_items):
        data = assert_ok(await rnet_items.list_items_with_search(limit=10, offset=0, search="gadget"))
        assert data.search == "gadget"


class TestRnetPostJson:
    @pytest.mark.asyncio
    async def test_create_in_stock(self, rnet_items):
        item = assert_ok(await rnet_items.create_item(name="Gadget", price=49.95, in_stock=True))
        assert item.name == "Gadget"
        assert item.price == 49.95
        assert item.in_stock is True

    @pytest.mark.asyncio
    async def test_create_out_of_stock(self, rnet_items):
        item = assert_ok(await rnet_items.create_item(name="Rare", price=999.0, in_stock=False))
        assert item.in_stock is False

    @pytest.mark.asyncio
    async def test_create_preserves_name(self, rnet_items):
        item = assert_ok(await rnet_items.create_item(name="Special", price=1.0, in_stock=True))
        assert item.name == "Special"


class TestRnetPut:
    @pytest.mark.asyncio
    async def test_update_item(self, rnet_items):
        data = assert_ok(await rnet_items.update_item(item_id=10, name="New Name", price=5.0))
        assert data.item_id == 10
        assert data.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_preserves_item_id(self, rnet_items):
        data = assert_ok(await rnet_items.update_item(item_id=77, name="X", price=1.0))
        assert data.item_id == 77


class TestRnetPatch:
    @pytest.mark.asyncio
    async def test_patch_sets_flag(self, rnet_items):
        data = assert_ok(await rnet_items.patch_item(item_id=2, name="Partial"))
        assert data.item_id == 2
        assert data.patched is True
        assert data.name == "Partial"


class TestRnetDelete:
    @pytest.mark.asyncio
    async def test_delete_returns_deleted(self, rnet_items):
        data = assert_ok(await rnet_items.delete_item(item_id=77))
        assert data.deleted is True
        assert data.item_id == 77

    @pytest.mark.asyncio
    async def test_delete_different_ids(self, rnet_items):
        for item_id in (1, 42, 999):
            data = assert_ok(await rnet_items.delete_item(item_id=item_id))
            assert data.item_id == item_id


class TestRnetHeaders:
    @pytest.mark.asyncio
    async def test_headers_echoed(self, rnet_headers):
        data = assert_ok(await rnet_headers.echo_headers(x_token="rnet-token", x_user_id="rnet-user"))
        assert data.x_token == "rnet-token"
        assert data.x_user_id == "rnet-user"


class TestRnetXHeaders:
    @pytest.mark.asyncio
    async def test_x_headers_sent(self, rnet_xheaders):
        data = assert_ok(await rnet_xheaders.echo_x_headers(token="rnet-tok", correlation_id="corr-42"))
        assert data.x_token == "rnet-tok"
        assert data.x_correlation_id == "corr-42"


class TestRnetForm:
    @pytest.mark.asyncio
    async def test_form_submitted(self, rnet_form):
        data = assert_ok(await rnet_form.submit_form(username="bob", password="p4ssw0rd"))
        assert data.username == "bob"
        assert data.password == "p4ssw0rd"


class TestRnetUpload:
    @pytest.mark.asyncio
    async def test_upload_with_description(self, rnet_upload):
        content = b"rnet file content"
        data = assert_ok(await rnet_upload.upload(file=io.BytesIO(content), description="rnet test"))
        assert data.size == len(content)
        assert data.description == "rnet test"

    @pytest.mark.asyncio
    async def test_upload_default_description(self, rnet_upload):
        content = b"bare minimum"
        data = assert_ok(await rnet_upload.upload(file=io.BytesIO(content)))
        assert data.size == len(content)

    @pytest.mark.asyncio
    async def test_upload_size_matches(self, rnet_upload):
        content = b"y" * 512
        data = assert_ok(await rnet_upload.upload(file=io.BytesIO(content)))
        assert data.size == 512


class TestRnetErrors:
    @pytest.mark.asyncio
    async def test_400_parsed_as_error_message(self, rnet_errors):
        err = assert_error(await rnet_errors.get_400())
        assert err.status == HTTPStatus.BAD_REQUEST
        assert err.status.is_client_error
        assert isinstance(err.error, ErrorMessage)

    @pytest.mark.asyncio
    async def test_404_parsed_as_error_message(self, rnet_errors):
        err = assert_error(await rnet_errors.get_404())
        assert err.status == HTTPStatus.NOT_FOUND
        assert err.status.is_client_error
        assert isinstance(err.error, ErrorMessage)

    @pytest.mark.asyncio
    async def test_422_parsed_as_error_detail(self, rnet_errors):
        err = assert_error(await rnet_errors.get_422())
        assert err.status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert isinstance(err.error, ErrorDetail)
        assert "field" in err.error.details

    @pytest.mark.asyncio
    async def test_500_is_server_error(self, rnet_errors):
        err = assert_error(await rnet_errors.get_500())
        assert err.status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert err.status.is_server_error

    @pytest.mark.asyncio
    async def test_502_status_error(self, aiohttp_errors):
        err = assert_error(await aiohttp_errors.get_502())
        assert err.status == HTTPStatus.BAD_GATEWAY
        assert err.status.is_server_error
        assert not err.status.is_client_error
        assert isinstance(err.error, BadGatewayError)

    @pytest.mark.asyncio
    async def test_empty_body_error_is_none(self, rnet_errors):
        err = assert_error(await rnet_errors.get_empty())
        assert err.status == HTTPStatus.NOT_FOUND
        assert isinstance(err.error, UnknownError)
        assert not err.error.payload

    @pytest.mark.asyncio
    async def test_error_carries_http_method(self, rnet_errors):
        err = assert_error(await rnet_errors.get_400())
        assert err.method == HTTPMethod.GET

    @pytest.mark.asyncio
    async def test_error_carries_path(self, rnet_errors):
        err = assert_error(await rnet_errors.get_404())
        assert err.path is not None
        assert "404" in err.path


class TestRnetMisc:
    @pytest.mark.asyncio
    async def test_ok_response_parsed(self, rnet_misc):
        data = assert_ok(await rnet_misc.get_with_request_id())
        assert data.ok is True


class TestAPIErrorUnit:
    def test_4xx_is_client_error(self):
        err = saronia.APIError(None, HTTPMethod.GET, HTTPStatus.NOT_FOUND, path="/test")
        assert err.status.is_client_error is True
        assert err.status.is_server_error is False

    def test_5xx_is_server_error(self):
        err = saronia.APIError(None, HTTPMethod.POST, HTTPStatus.INTERNAL_SERVER_ERROR)
        assert err.status.is_server_error is True
        assert err.status.is_client_error is False

    def test_2xx_is_neither(self):
        err = saronia.APIError(None, HTTPMethod.GET, HTTPStatus.OK)
        assert err.status.is_client_error is False
        assert err.status.is_server_error is False

    def test_repr_includes_status_path_request_id(self):
        err = saronia.APIError(None, HTTPMethod.GET, HTTPStatus.BAD_REQUEST, path="/bad", request_id="req-1")
        r = repr(err)
        assert "400" in r
        assert "/bad" in r
        assert "req-1" in r

    def test_request_id_defaults_to_none(self):
        err = saronia.APIError(None, HTTPMethod.GET, HTTPStatus.NOT_FOUND)
        assert err.request_id is None

    def test_stores_method(self):
        err = saronia.APIError(None, HTTPMethod.DELETE, HTTPStatus.NOT_FOUND)
        assert err.method == HTTPMethod.DELETE

    def test_stores_path(self):
        err = saronia.APIError(None, HTTPMethod.GET, HTTPStatus.NOT_FOUND, path="/items/99")
        assert err.path == "/items/99"


class TestRouteDecoratorValidation:
    def test_classmethod_not_allowed(self):
        with pytest.raises(TypeError, match="classmethods"):

            @saronia.get("/test")
            @classmethod
            async def bad_classmethod(cls) -> APIResult[None, None]: ...

    def test_non_async_not_allowed(self):
        with pytest.raises(TypeError, match="async"):

            @saronia.get("/test")  # type: ignore
            def sync_method(self) -> APIResult[None, None]:  # type: ignore
                ...

    def test_json_and_urlencoded_conflict_raises(self):
        with pytest.raises(LookupError):

            @saronia.post("/test")
            async def conflicting(
                self,
                a: JSON[str],
                b: URLencoded[str],
            ) -> APIResult[None, None]: ...

    def test_missing_path_param_raises(self):
        with pytest.raises(TypeError, match="misses path params"):

            @saronia.get("/{missing_param}")
            async def missing_path(self) -> APIResult[None, None]: ...


class TestAPIBuilder:
    def test_client_access_before_build_raises(self):
        api = API.endpoint("/test")

        @api("/things")
        class ThingsCtrl:
            pass

        with pytest.raises(ValueError, match="no client"):
            _ = api.client

    @pytest.mark.asyncio
    async def test_build_returns_self(self):
        import aiohttp

        async with aiohttp.ClientSession(base_url=BASE_URL) as session:
            api = API.endpoint("/v1")
            client = AiohttpClient(session)
            result = api.build(client)
            assert result is api

    @pytest.mark.asyncio
    async def test_build_sets_client_on_controller_class(self):
        import aiohttp

        async with aiohttp.ClientSession(base_url=BASE_URL) as session:
            api = API.endpoint("/v1")
            client = AiohttpClient(session)

            @api("/things")
            class ThingsCtrl:
                @get("")
                async def list_things(self) -> APIResult[None, None]: ...

            api.build(client)
            assert ThingsCtrl.client is client  # type: ignore

    def test_controller_path_set_by_decorator(self):
        api = API.endpoint("/v2")

        @api("/widgets")
        class WidgetsCtrl:
            pass

        assert WidgetsCtrl.path == "/widgets"  # type: ignore

    def test_controller_registered_in_api(self):
        api = API.endpoint("/v3")

        @api("/things")
        class MyCtrl:
            pass

        assert MyCtrl in api.controllers


class TestSecurity:
    def test_http_bearer(self):
        bearer = HTTPBearer("secret123")
        assert bearer.scheme == "Bearer"
        assert bearer.credentials == "secret123"
        assert bearer.header == {"Authorization": "Bearer secret123"}

    def test_http_basic(self):
        basic = HTTPBasic("user", "pass")
        assert basic.scheme == "Basic"
        assert basic.credentials == base64.b64encode(b"user:pass").decode()
        assert basic.header == {"Authorization": f"Basic {base64.b64encode(b'user:pass').decode()}"}

    def test_header_api_key(self):
        key = HeaderAPIKey["X-API-Key"]("secret")
        assert key.name == "X-API-Key"
        assert key.value == "secret"
        assert key.mapping == {"X-API-Key": "secret"}

    def test_query_api_key(self):
        key = QueryAPIKey["api_key"]("secret")
        assert key.name == "api_key"
        assert key.mapping == {"api_key": "secret"}

    def test_cookie_api_key(self):
        key = CookieAPIKey["session"]("token123")
        assert key.name == "session"
        assert key.mapping == {"session": "token123"}
