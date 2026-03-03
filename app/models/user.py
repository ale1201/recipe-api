from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    #PKs are indexed by default, explicit index is redundant (extra indexes in migrations)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # I increased column size for hashed_password to accommodate longer hashes (like bcrypt)
    #hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="owner", cascade="all, delete-orphan")  # noqa: F821
    meal_plans: Mapped[list["MealPlan"]] = relationship(back_populates="owner", cascade="all, delete-orphan")  # noqa: F821
