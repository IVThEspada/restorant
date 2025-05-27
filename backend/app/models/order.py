from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.core.database import Base


class OrderStatus(PyEnum):
    RECEIVED = "RECEIVED"
    PREPARING = "PREPARING"
    READY = "READY"
    PAID = "PAID"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.RECEIVED)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, nullable=False)
    note = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")

from sqlalchemy import Boolean, String

payment_method = Column(String, nullable=True)       # "cash", "credit", "online"
is_paid = Column(Boolean, default=False)

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
processed_by = relationship("User")  # opsiyonel: personel detayını çekmek için
