import pytest
from httpx import AsyncClient
import uuid


@pytest.fixture
async def recipe_for_meal_plan(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/recipes/",
        json={
            "title": "Spaghetti Carbonara",
            "cuisine": "Italian",
            "prep_time_minutes": 20,
            "servings": 4,
            "ingredients": [
                {"name": "spaghetti", "quantity": 400, "unit": "g"},
                {"name": "eggs", "quantity": 4, "unit": "pieces"},
                {"name": "bacon", "quantity": 200, "unit": "g"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture
async def recipe_for_shopping_list(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/recipes/",
        json={
            "title": "Banana Pancakes",
            "cuisine": "American",
            "prep_time_minutes": 15,
            "servings": 2,
            "ingredients": [
                {"name": "eggs", "quantity": 2, "unit": "pieces"},
                {"name": "banana", "quantity": 2, "unit": "pieces"},
                {"name": "flour", "quantity": 100, "unit": "g"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_meal_plan(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    response = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Weekly Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
                {"day_of_week": 0, "slot": "lunch", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Weekly Plan"
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_create_meal_plan_unauthenticated(client: AsyncClient, recipe_for_meal_plan: int):
    response = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Weekly Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_meal_plan_empty_items(client: AsyncClient, auth_headers: dict):
    """Test creating meal plan with no items."""
    response = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Empty Plan",
            "items": [],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Empty Plan"
    assert len(data["items"]) == 0

@pytest.mark.asyncio
async def test_create_meal_plan_duplicate_item_conflict(client, auth_headers, recipe_for_meal_plan):
    resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Dup Plan",
            "items": [
                {"day_of_week": 1, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
                {"day_of_week": 1, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert "UNIQUE constraint failed" in  resp.text
    assert resp.status_code == 400, resp.text

@pytest.mark.asyncio
async def test_get_meal_plan(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Fetchable Plan",
            "items": [
                {"day_of_week": 1, "slot": "dinner", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fetchable Plan"
    assert len(data["items"]) == 1
    assert data["items"][0]["slot"] == "dinner"


@pytest.mark.asyncio
async def test_get_meal_plan_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/v1/meal-plans/9999",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_meal_plan_not_owner(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    # Create a meal plan as testuser
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Private Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    meal_plan_id = create_resp.json()["id"]

    # Register and login as another user
    username = f"otheruser_{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_meal_plans(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    for i in range(3):
        await client.post(
            "/api/v1/meal-plans/",
            json={
                "name": f"Plan {i}",
                "items": [
                    {"day_of_week": i % 7, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
                ],
            },
            headers=auth_headers,
        )
    
    response = await client.get(
        "/api/v1/meal-plans/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_meal_plans_pagination(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    for i in range(5):
        await client.post(
            "/api/v1/meal-plans/",
            json={
                "name": f"Plan {i}",
                "items": [
                    {"day_of_week": i % 7, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
                ],
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/api/v1/meal-plans/?skip=0&limit=2",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_meal_plans_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/meal-plans/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_meal_plan(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Old Name",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/meal-plans/{meal_plan_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_meal_plan_items(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int, recipe_for_shopping_list: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Original Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/meal-plans/{meal_plan_id}",
        json={
            "items": [
                {"day_of_week": 1, "slot": "lunch", "recipe_id": recipe_for_shopping_list},
                {"day_of_week": 2, "slot": "dinner", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_meal_plan_not_owner(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Protected Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    meal_plan_id = create_resp.json()["id"]
    username = f"baduser_{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.put(
        f"/api/v1/meal-plans/{meal_plan_id}",
        json={"name": "Stolen Name"},
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_meal_plan(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Delete Me",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    get_resp = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_meal_plan_not_owner(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Protected Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    meal_plan_id = create_resp.json()["id"]
    username = f"badactor_{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.delete(
        f"/api/v1/meal-plans/{meal_plan_id}",
        headers=other_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_shopping_list(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int, recipe_for_shopping_list: int):
    
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Shopping Test",
            "items": [
                {"day_of_week": 0, "slot": "dinner", "recipe_id": recipe_for_meal_plan},
                {"day_of_week": 2, "slot": "lunch", "recipe_id": recipe_for_shopping_list},
            ],
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}/shopping-list",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meal_plan_id"] == meal_plan_id
    assert len(data["items"]) > 0

    eggs = next((item for item in data["items"] if item["name"] == "eggs"), None)
    assert eggs is not None and eggs["quantity"] == 6 and eggs["unit"] == "pieces"

    spaghetti = next((item for item in data["items"] if item["name"] == "spaghetti"), None)
    assert spaghetti is not None and spaghetti["quantity"] == 400 and spaghetti["unit"] == "g"

    bacon = next((i for i in data["items"] if i["name"] == "bacon"), None)
    assert bacon and bacon["quantity"] == 200 and bacon["unit"] == "g"

    flour = next((i for i in data["items"] if i["name"] == "flour"), None)
    assert flour and flour["quantity"] == 100 and flour["unit"] == "g"



@pytest.mark.asyncio
async def test_get_shopping_list_empty_meal_plan(client: AsyncClient, auth_headers: dict):
    """Test shopping list for empty meal plan."""
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={"name": "Empty Plan", "items": []},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    meal_plan_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}/shopping-list",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_shopping_list_not_owner(client: AsyncClient, auth_headers: dict, recipe_for_meal_plan: int):
    """Test that non-owner cannot access shopping list."""
    create_resp = await client.post(
        "/api/v1/meal-plans/",
        json={
            "name": "Private Plan",
            "items": [
                {"day_of_week": 0, "slot": "breakfast", "recipe_id": recipe_for_meal_plan},
            ],
        },
        headers=auth_headers,
    )
    meal_plan_id = create_resp.json()["id"]
    username = f"baduser_{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.get(
        f"/api/v1/meal-plans/{meal_plan_id}/shopping-list",
        headers=other_headers,
    )
    assert response.status_code == 403
