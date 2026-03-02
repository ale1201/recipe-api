from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.recipe import RecipeSummary


class SlotType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"

class MealPlanItemCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    slot: SlotType
    recipe_id: int = Field(..., gt=0)


class MealPlanItemResponse(BaseModel):
    id: int
    day_of_week: int
    slot: SlotType
    recipe_id: int
    recipe: RecipeSummary | None = None

    model_config = {"from_attributes": True}


class MealPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    items: list[MealPlanItemCreate] = Field(default_factory=list)


class MealPlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    items: list[MealPlanItemCreate] | None = None


class MealPlanResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: list[MealPlanItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ShoppingListItem(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None


class MealPlanShoppingList(BaseModel):
    meal_plan_id: int
    meal_plan_name: str
    items: list[ShoppingListItem] = Field(default_factory=list)
