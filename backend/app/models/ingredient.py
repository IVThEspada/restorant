from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    stock_quantity = Column(Float, default=0.0)
    low_stock_threshold = Column(Float, default=10.0)  # kritik stok seviyesi
