from sqlalchemy import Column, Integer, Enum
from enum import Enum as PyEnum
from app.core.database import Base

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
