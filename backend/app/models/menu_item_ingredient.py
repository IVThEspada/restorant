from sqlalchemy import Column, Integer, Float, ForeignKey
from app.core.database import Base

class MenuItemIngredient(Base):
    __tablename__ = "menu_item_ingredients"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    amount_used = Column(Float)  # bir ürün için gereken miktar
