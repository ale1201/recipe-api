from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from asyncpg.exceptions import UniqueViolationError

from app.models.meal_plan import MealPlan
from app.models.meal_plan_item import MealPlanItem
from app.models.user import User
from app.repositories.meal_plan import MealPlanRepository
from app.schemas.meal_plan import MealPlanCreate, MealPlanUpdate, MealPlanShoppingList, ShoppingListItem

try:
    from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
except Exception:  # pragma: no cover
    UniqueViolationError = None  # type: ignore
    ForeignKeyViolationError = None  # type: ignore


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = getattr(exc, "orig", None)
    print("here")
    print(orig)
    print(isinstance(orig, UniqueViolationError))
    print("orig type:", type(orig))
    print("sqlstate:", getattr(orig, "sqlstate", None))
    print("pgcode:", getattr(orig, "pgcode", None))
    print("message:", str(orig))
    return bool(UniqueViolationError and isinstance(orig, UniqueViolationError))


def _is_fk_violation(exc: IntegrityError) -> bool:
    orig = getattr(exc, "orig", None)
    return bool(ForeignKeyViolationError and isinstance(orig, ForeignKeyViolationError))

class MealPlanService:
    def __init__(self, db: AsyncSession):
        self.meal_plan_repo = MealPlanRepository(db)
        self.db = db

    async def list_meal_plans(self, user: User, skip: int = 0, limit: int = 20) -> tuple[list[MealPlan], int]:
        """List all meal plans for the authenticated user."""
        meal_plans = await self.meal_plan_repo.list_by_user(user.id, skip=skip, limit=limit)
        total = await self.meal_plan_repo.count_by_user(user.id)
        return meal_plans, total

    async def get_meal_plan(self, meal_plan_id: int, user: User) -> MealPlan:
        """Get a meal plan and verify ownership."""
        meal_plan = await self.meal_plan_repo.get_by_id(meal_plan_id)
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found",
            )
        if meal_plan.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own meal plans",
            )
        return meal_plan

    async def create_meal_plan(self, data: MealPlanCreate, user: User) -> MealPlan:
        """Create a new meal plan with items."""
        meal_plan = MealPlan(
            name=data.name,
            user_id=user.id,
        )
        
        for item_data in data.items:
            meal_plan.items.append(
                MealPlanItem(
                    day_of_week=item_data.day_of_week,
                    slot=item_data.slot,
                    recipe_id=item_data.recipe_id,
                )
            )
        try:
            created = await self.meal_plan_repo.create(meal_plan)
        except IntegrityError as e:
            # Roll back the session so it can be used again in this request
            await self.db.rollback()

            # Detect unique constraint violation (postgres/asyncpg)
            if _is_unique_violation(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate meal plan item: the same recipe is already assigned to this day and slot.",
                ) from e

            if _is_fk_violation(e):
                # recipe_id does not exist (or other FK issue)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid recipe_id: referenced recipe does not exist.",
                ) from e

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error while creating meal plan: {e.orig if hasattr(e, 'orig') else str(e)}",
            ) from e
        # Re-fetch with eager loading to avoid async lazy-load during response serialization
        full = await self.meal_plan_repo.get_by_id(created.id)
        return full if full is not None else created

    async def update_meal_plan(self, meal_plan_id: int, data: MealPlanUpdate, user: User) -> MealPlan:
        """Update a meal plan and verify ownership."""
        meal_plan = await self.get_meal_plan(meal_plan_id, user)

        if data.name is not None:
            meal_plan.name = data.name

        if data.items is not None:
            for item in list(meal_plan.items):
                await self.db.delete(item)
            await self.db.flush()

            meal_plan.items = []
            for item_data in data.items:
                meal_plan.items.append(
                    MealPlanItem(
                        day_of_week=item_data.day_of_week,
                        slot=item_data.slot,
                        recipe_id=item_data.recipe_id,
                        meal_plan_id=meal_plan.id,
                    )
                )
        try:
            updated = await self.meal_plan_repo.update(meal_plan)
        except IntegrityError as e:
            await self.db.rollback()

            if _is_unique_violation(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate meal plan item: the same recipe is already assigned to this day and slot.",
                ) from e

            if _is_fk_violation(e):
                # recipe_id does not exist (or other FK issue)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid recipe_id: referenced recipe does not exist.",
                ) from e

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error while updating meal plan: {e.orig if hasattr(e, 'orig') else str(e)}",
            ) from e
        # Re-fetch with eager loading for response
        full = await self.meal_plan_repo.get_by_id(updated.id)
        return full if full is not None else updated

    async def delete_meal_plan(self, meal_plan_id: int, user: User) -> None:
        """Delete a meal plan and verify ownership."""
        meal_plan = await self.get_meal_plan(meal_plan_id, user)
        await self.meal_plan_repo.delete(meal_plan)

    async def get_shopping_list(self, meal_plan_id: int, user: User) -> MealPlanShoppingList:
        """
        Generate shopping list for a meal plan.        
        """
        
        full_meal_plan = await self.meal_plan_repo.get_for_shopping_list_by_id(meal_plan_id)

        if not full_meal_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
        if full_meal_plan.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own meal plans")
        
        aggregated: dict[tuple[str, str | None], float | None] = {}
        
        for item in full_meal_plan.items:
            if item.recipe and item.recipe.ingredients:
                for ingredient in item.recipe.ingredients:
                    key = (ingredient.name.strip().lower(), ingredient.unit.strip().lower() if ingredient.unit else None)
                    if ingredient.quantity is not None:
                        aggregated[key] = aggregated.get(key, 0.0) + float(ingredient.quantity)
                    else:
                        aggregated.setdefault(key, None)  # If any quantity is None, include but dont sum
        
        shopping_items = [
            ShoppingListItem(
                name=key[0],
                quantity=qty,
                unit=(key[1] if key[1] is not None else None),
            )
            for key, qty in aggregated.items()
        ]

        shopping_items.sort(key=lambda x: (x.name.lower(), (x.unit or "")))
        
        return MealPlanShoppingList(meal_plan_id=meal_plan_id, meal_plan_name=full_meal_plan.name, items=shopping_items)
