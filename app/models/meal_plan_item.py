from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"
    __table_args__ = (
        UniqueConstraint('meal_plan_id', 'day_of_week', 'slot', name='uq_meal_plan_slot'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meal_plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    slot: Mapped[str] = mapped_column(String(32), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)

    meal_plan: Mapped["MealPlan"] = relationship(back_populates="items")  # noqa: F821
    recipe: Mapped["Recipe"] = relationship()  # noqa: F821