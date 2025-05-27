from sqlalchemy import Column, Integer, String, Numeric, Boolean
from app.core.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    img_url = Column(String)
    is_available = Column(Boolean, default=True)
    allergens = Column(String, nullable=True)  # Örn: "gluten, dairy"
    tags = Column(String, nullable=True)  # Örn: "vegan, spicy"



