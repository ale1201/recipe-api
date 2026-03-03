from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    #PKs are indexed by default, explicit index is redundant (extra indexes in migrations)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")  # noqa: F821
