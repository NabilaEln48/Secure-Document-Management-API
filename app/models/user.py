from pydantic import BaseModel, EmailStr
from enum import Enum
from app.core.state_machine import Role

class UserBase(BaseModel):
    email: EmailStr
    role: Role
    active: bool = True

class UserCreate(UserBase):
    password: str

class UserDB(UserBase):
    id: str
    hashed_password: str

class UserResponse(UserBase):
    id: str