from pydantic import BaseModel
from typing import List, Optional


class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int
    note: Optional[str] = None


class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemIn]


class OrderItemOut(BaseModel):
    name: str
    quantity: int

    class Config:
        orm_mode = True


class OrderOut(BaseModel):
    id: int
    table_id: int
    status: str
    items: List[OrderItemOut]

    class Config:
        orm_mode = True

from typing import Optional

class OrderItemUpdate(BaseModel):
    menu_item_id: int
    quantity: int
    note: Optional[str] = None

class OrderUpdate(BaseModel):
    items: list[OrderItemUpdate]

class OrderItemSummary(BaseModel):
    name: str
    quantity: int

class OrderSummary(BaseModel):
    id: int
    table_id: int
    status: str
    items: list[OrderItemSummary]

    class Config:
        from_attributes = True

class OrderPaymentUpdate(BaseModel):
    payment_method: str  # örnek: "cash", "credit", "online"


