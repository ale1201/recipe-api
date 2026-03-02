from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal_plan import MealPlan
from app.models.meal_plan_item import MealPlanItem
from app.models.recipe import Recipe


class MealPlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> list[MealPlan]:
        """
        List meal plans owned by a user.
        """
        result = await self.db.execute(
            select(MealPlan)
            .where(MealPlan.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(select(func.count(MealPlan.id)).where(MealPlan.user_id == user_id))
        return result.scalar_one()

    async def get_by_id(self, meal_plan_id: int) -> MealPlan | None:
        """Fetch by ID only, service check ownership"""
        result = await self.db.execute(
            select(MealPlan)
            .options(selectinload(MealPlan.items).selectinload(MealPlanItem.recipe))
            .where(MealPlan.id == meal_plan_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, meal_plan: MealPlan) -> MealPlan:
        self.db.add(meal_plan)
        await self.db.flush()
        await self.db.refresh(meal_plan, attribute_names=["items"])
        return meal_plan

    async def update(self, meal_plan: MealPlan) -> MealPlan:
        await self.db.flush()
        await self.db.refresh(meal_plan, attribute_names=["items"])
        return meal_plan

    async def delete(self, meal_plan: MealPlan) -> None:
        await self.db.delete(meal_plan)
        await self.db.flush()

    async def get_for_shopping_list_by_id(self, meal_plan_id: int) -> MealPlan | None:
        """
        Fetch a meal plan for shopping-list generation, by ID only. Service checks ownership and loads all related data (recipes and ingredients).
        """
        result = await self.db.execute(
            select(MealPlan)
            .options(
                selectinload(MealPlan.items)
                .selectinload(MealPlanItem.recipe)
                .selectinload(Recipe.ingredients)
            )
            .where(MealPlan.id == meal_plan_id)
        )
        return result.scalar_one_or_none()
