from pydantic import BaseModel
from typing import Dict

class PopularItem(BaseModel):
    name: str
    total_quantity: int

class ReportSummary(BaseModel):
    total_orders: int
    total_items_sold: int
    total_revenue: float


class PaymentSummary(BaseModel):
    total_paid_orders: int
    total_revenue: float
    payment_method_breakdown: Dict[str, int]

class DailySummary(BaseModel):
    date: str  # yyyy-mm-dd
    total_orders: int
    total_revenue: float
