from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.v1.dependencies import get_current_user
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeResponse, RecipeSummary
from app.services.recipe import RecipeService
from app.repositories.recipe import RecipeRepository

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=dict)
async def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all recipes with pagination."""
    recipe_service = RecipeService(db)
    recipes, total = await recipe_service.list_recipes(skip=skip, limit=limit)

    recipe_repo = RecipeRepository(db)
    result = []
    for recipe in recipes:
        ingredients = await recipe_repo.get_ingredients(recipe.id)
        result.append(
            RecipeResponse(
                id=recipe.id,
                title=recipe.title,
                description=recipe.description,
                cuisine=recipe.cuisine,
                prep_time_minutes=recipe.prep_time_minutes,
                servings=recipe.servings,
                user_id=recipe.user_id,
                created_at=recipe.created_at,
                updated_at=recipe.updated_at,
                ingredients=[
                    {"id": ing.id, "name": ing.name, "quantity": ing.quantity, "unit": ing.unit}
                    for ing in ingredients
                ],
            )
        )

    return {"items": result, "total": total, "skip": skip, "limit": limit}


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single recipe with ingredients."""
    recipe_service = RecipeService(db)
    return await recipe_service.get_recipe(recipe_id)


@router.post("/", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new recipe."""
    recipe_service = RecipeService(db)
    return await recipe_service.create_recipe(data, current_user)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing recipe."""
    recipe_service = RecipeService(db)
    return await recipe_service.update_recipe(recipe_id, data, current_user)


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recipe."""
    recipe_service = RecipeService(db)
    await recipe_service.delete_recipe(recipe_id, current_user)
