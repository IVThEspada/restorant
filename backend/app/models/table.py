# app/models/table.py

from app.core.database import Base
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship

class TableStatus(PyEnum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    CLOSED = "CLOSED"

class DiningTable(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)
    seats = Column(Integer, default=4)
    status = Column(Enum(TableStatus), default=TableStatus.AVAILABLE)

    current_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_user = relationship("User")

