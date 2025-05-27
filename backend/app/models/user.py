from sqlalchemy import Column, Integer, String, Enum
from enum import Enum as PyEnum
from app.core.database import Base

class UserRole(PyEnum):
    CUSTOMER = "CUSTOMER"
    KITCHEN = "KITCHEN"
    WAITER = "WAITER"
    MANAGER = "MANAGER"

class User(Base):
    __tablename__ = "users"


    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
