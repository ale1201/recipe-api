from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.v1.dependencies import get_current_user
from app.schemas.meal_plan import MealPlanCreate, MealPlanPaginatedResponse, MealPlanUpdate, MealPlanResponse, MealPlanShoppingList
from app.services.meal_plan import MealPlanService

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


@router.get("/{meal_plan_id}/shopping-list", response_model=MealPlanShoppingList)
async def get_shopping_list(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate an aggregated shopping list for the meal plan."""
    meal_plan_service = MealPlanService(db)
    return await meal_plan_service.get_shopping_list(meal_plan_id, current_user)


@router.get("/", response_model=MealPlanPaginatedResponse)
async def list_meal_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal_plan_service = MealPlanService(db)
    meal_plans, total = await meal_plan_service.list_meal_plans(current_user, skip=skip, limit=limit)

    return MealPlanPaginatedResponse(items=meal_plans, total=total, skip=skip, limit=limit)


@router.get("/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal_plan_service = MealPlanService(db)
    return await meal_plan_service.get_meal_plan(meal_plan_id, current_user)


@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    data: MealPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal_plan_service = MealPlanService(db)
    return await meal_plan_service.create_meal_plan(data, current_user)


@router.put("/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    meal_plan_id: int,
    data: MealPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal_plan_service = MealPlanService(db)
    return await meal_plan_service.update_meal_plan(meal_plan_id, data, current_user)


@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    meal_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a meal plan."""
    meal_plan_service = MealPlanService(db)
    await meal_plan_service.delete_meal_plan(meal_plan_id, current_user)
    