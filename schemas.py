from pydantic import BaseModel
from typing import Optional
from uuid import UUID


# =========================
# USER
# =========================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str

    model_config = {
        "from_attributes": True
    }


# =========================
# POST
# =========================

class PostCreate(BaseModel):
    title: str
    body: str
    category: Optional[str] = None
    language: Optional[str] = None
    state: Optional[str] = None


class PostResponse(BaseModel):
    id: UUID
    title: str
    body: str
    category: Optional[str]
    language: Optional[str]
    state: Optional[str]
    user_id: UUID

    model_config = {
        "from_attributes": True
    }


# =========================
# RESET PASSWORD
# =========================

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
