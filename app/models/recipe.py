from datetime import datetime

from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    #PKs are indexed by default, explicit index is redundant (extra indexes in migrations)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    cuisine: Mapped[str] = mapped_column(String(100), nullable=True)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    servings: Mapped[int] = mapped_column(Integer, nullable=True)
    # Search by user are frequent, index can improve performance
    # I also added ondelete cascade, so if a user is deleted, their recipes are also deleted.
    #user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="recipes")  # noqa: F821
    ingredients: Mapped[list["Ingredient"]] = relationship(  # noqa: F821
        back_populates="recipe", cascade="all, delete-orphan"
    )
