from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

# ✅ Yeni menü öğesi oluştururken kullanılacak
class MenuItemCreate(BaseModel):
    name: str
    price: Decimal
    img_url: Optional[str] = None
    is_available: bool = True
    allergens: Optional[str] = None
    tags: Optional[str] = None

# ✅ Mevcut menü öğesini güncellerken kullanılacak
class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    img_url: Optional[str] = None
    is_available: Optional[bool] = None
    allergens: Optional[str] = None
    tags: Optional[str] = None

# ✅ Menü öğesi geri dönerken kullanılacak
class MenuItemOut(BaseModel):
    id: int
    name: str
    price: Decimal
    img_url: Optional[str] = None
    is_available: bool
    allergens: Optional[str] = None
    tags: Optional[str] = None

    class Config:
        from_attributes = True
