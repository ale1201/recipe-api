from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ingredient import IngredientCreate, IngredientResponse
from app.schemas.pagination import PaginatedResponse


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    cuisine: str | None = Field(None, max_length=100)
    prep_time_minutes: int | None = Field(None, ge=1)
    servings: int | None = Field(None, ge=1)
    # ingredients: list[IngredientCreate] = []
    # Eventhough Pydantic can hanlde mutable default values like lists, it's generally safer to 
    # use default_factory 
    ingredients: list[IngredientCreate] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    cuisine: str | None = Field(None, max_length=100)
    prep_time_minutes: int | None = Field(None, ge=1)
    servings: int | None = Field(None, ge=1)
    ingredients: list[IngredientCreate] | None = None


class RecipeResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cuisine: str | None
    prep_time_minutes: int | None
    servings: int | None
    user_id: int
    created_at: datetime
    updated_at: datetime
    # ingredients: list[IngredientResponse] = []
    # Eventhough Pydantic can hanlde mutable default values like lists, it's generally safer to 
    # use default_factory 
    ingredients: list[IngredientResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class RecipePaginatedResponse(PaginatedResponse):
    items: list[RecipeResponse]


class RecipeSummary(BaseModel):
    id: int
    title: str
    cuisine: str | None
    prep_time_minutes: int | None
    servings: int | None
    # Not need to include user_id, created_at in summary response, leak internal details, and not useful for listing
    # user_id: int
    # created_at: datetime

    model_config = {"from_attributes": True}
