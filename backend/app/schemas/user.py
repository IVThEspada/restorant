from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    KITCHEN = "KITCHEN"
    WAITER = "WAITER"
    MANAGER = "MANAGER"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
