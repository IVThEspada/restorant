from pydantic import BaseModel
from enum import Enum


class TableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    CLOSED = "CLOSED"


class TableBase(BaseModel):
    number: int
    seats: int = 4
    status: TableStatus = TableStatus.AVAILABLE


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    seats: int | None = None
    status: TableStatus | None = None


class TableOut(TableBase):
    id: int

    class Config:
        from_attributes = True
