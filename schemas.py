from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class PostCreate(BaseModel):
    title: str
    body: str
    category: str
    language: str
    state: str


class PostResponse(BaseModel):
    id: UUID
    title: str
    body: str
    category: str
    language: str
    state: str
    user_id: UUID

    model_config = {
        "from_attributes": True
    }
