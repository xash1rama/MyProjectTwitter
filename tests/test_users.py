import pytest
from .conftest import client, test_db

@pytest.mark.asyncio
async def test_get_me(client, test_db):
    """Тест получения первого пользователя"""

    api_key = "test"
    response = await client.get("/api/users/me", headers={"api-key": api_key})

    assert response.json()["result"] == True
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_me_2(client, test_db):
    """Тест получения второго пользователя"""

    api_key = "test_2"
    response = await client.get("/api/users/me", headers={"api-key": api_key})
    print(response.json())
    assert response.json()["result"] == True
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_me_invalid_api_key(client, test_db):
    """Тест получения пользователя с невалидным api-key"""

    api_key = "test123"
    response = await client.get("/api/users/me", headers={"api-key": api_key})

    data = response.json()
    assert response.status_code == 403
    assert data["detail"] == "Invalid API key"

@pytest.mark.asyncio
async def test_get_another_user(client, test_db):
    """Тест получения пользователя"""

    response = await client.get("/api/users/2")

    assert response.json()["result"] == True
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_another_invalid_user(client, test_db):
    """Тест получения несущетсвующего пользователя"""
    response = await client.get("/api/users/11")
    assert response.json()["result"] == False
    assert response.json()["error_message"] == "'NoneType' object has no attribute 'id'"


@pytest.mark.asyncio
async def test_follow_on_user(client, test_db):
    """Тест подписки"""
    api_key = "test"
    response = await client.post("/api/users/2/follow", headers={"api-key": api_key})
    assert response.json()["result"] == True
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unfollow_to_user(client, test_db):
    """Тест отподписки"""

    api_key = "test"
    response = await client.delete("/api/users/2/follow", headers={"api-key": api_key})
    assert response.json()["result"] == True
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_follow_on_invalid_user(client, test_db):
    """Тест подписки на несущетсвующего пользователя"""

    api_key = "test"
    response =await client.post("/api/users/44/follow", headers={"api-key": api_key})
    assert response.json()["result"] == False
