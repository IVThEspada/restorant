from pydantic import BaseModel
from typing import Optional

class LowStockItem(BaseModel):
    name: str
    stock_quantity: float
    low_stock_threshold: float

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    stock_quantity: Optional[float] = None
    low_stock_threshold: Optional[float] = None

class IngredientOut(BaseModel):
    id: int
    name: str
    stock_quantity: float
    low_stock_threshold: float

    class Config:
        from_attributes = True
