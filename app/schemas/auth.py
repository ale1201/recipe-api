from pydantic import BaseModel, Field, field_validator
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # password: str = Field(..., min_length=6)
    # For security, increasing min_length for password to 8 (or more) is generally recommended. 
    # Add maximum length to prevent DoS attacks with extremely long passwords.
    password: str = Field(..., min_length=8, max_length=72)

    # We can use field_validator to validate fields, can reduce edge cases
    @field_validator("username")
    @classmethod
    def normalize_and_alphanumeric_username(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username may only contain letters, numbers, underscores, and hyphens")
        return v


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
