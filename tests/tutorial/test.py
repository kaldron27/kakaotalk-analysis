import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from src.tutorial import api
from src.tutorial.models import TestUsers


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with LifespanManager(api):
        async with AsyncClient(app=api, base_url="http://test") as c:
            yield c


@pytest.mark.anyio
async def test_create_user(client: AsyncClient):  # nosec
    response = await client.post("/users", json={"username": "admin"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "admin"
    assert "id" in data
    user_id = data["id"]

    user_obj = await TestUsers.get(id=user_id)
    assert user_obj.id == user_id