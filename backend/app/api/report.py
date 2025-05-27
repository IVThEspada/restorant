from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.report import PopularItem
from app.dependencies.auth import role_required
from sqlalchemy import func
from app.schemas.report import ReportSummary
from app.models.order import Order, OrderItem
from app.models.menu_item import MenuItem


router = APIRouter(prefix="/reports", tags=["reports"])

from datetime import datetime
from fastapi import Query

@router.get("/summary", response_model=ReportSummary, dependencies=[Depends(role_required(["MANAGER"]))])
async def get_report_summary(
    db: AsyncSession = Depends(get_db),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None)
):
    # Sipariş sorgusuna tarih aralığı filtresi uygula
    order_query = select(Order)
    item_query = (
        select(
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.quantity * MenuItem.price)
        ).join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
    )

    if start_date and end_date:
        order_query = order_query.where(Order.created_at >= start_date, Order.created_at <= end_date)
        item_query = item_query.where(OrderItem.created_at >= start_date, OrderItem.created_at <= end_date)

    # Sipariş sayısı
    order_count_result = await db.execute(order_query.with_only_columns(func.count()))
    total_orders = order_count_result.scalar()

    # Ürün sayısı ve ciro
    revenue_result = await db.execute(item_query)
    total_items_sold, total_revenue = revenue_result.one()

    return ReportSummary(
        total_orders=total_orders or 0,
        total_items_sold=total_items_sold or 0,
        total_revenue=round(total_revenue or 0.0, 2)
    )

@router.get("/popular-items", response_model=list[PopularItem], dependencies=[Depends(role_required(["MANAGER"]))])
async def get_popular_items(
    db: AsyncSession = Depends(get_db),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None)
):
    query = (
        select(MenuItem.name, func.sum(OrderItem.quantity).label("total_quantity"))
        .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
        .join(Order, Order.id == OrderItem.order_id)
        .group_by(MenuItem.name)
        .order_by(func.sum(OrderItem.quantity).desc())
    )

    if start_date and end_date:
        query = query.where(Order.created_at >= start_date, Order.created_at <= end_date)

    result = await db.execute(query)
    rows = result.all()

    return [
        PopularItem(name=name, total_quantity=qty)
        for name, qty in rows
    ]

from app.schemas.report import PaymentSummary
from app.models.order import Order
from sqlalchemy import func

@router.get("/payment-summary", response_model=PaymentSummary, dependencies=[Depends(role_required(["MANAGER"]))])
async def get_payment_summary(db: AsyncSession = Depends(get_db)):
    # Toplam ödenmiş sipariş
    paid_orders_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.is_paid == True)
    )
    total_paid_orders = paid_orders_result.scalar()

    # Toplam gelir
    revenue_result = await db.execute(
        select(func.sum(OrderItem.quantity * MenuItem.price))
        .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.is_paid == True)
    )
    total_revenue = revenue_result.scalar() or 0.0

    # Ödeme yöntemine göre dağılım
    method_result = await db.execute(
        select(Order.payment_method, func.count())
        .where(Order.is_paid == True)
        .group_by(Order.payment_method)
    )
    breakdown = {method: count for method, count in method_result.all()}

    return PaymentSummary(
        total_paid_orders=total_paid_orders or 0,
        total_revenue=round(total_revenue, 2),
        payment_method_breakdown=breakdown
    )

from app.schemas.report import DailySummary
from sqlalchemy import cast, Date

@router.get("/daily-summary", response_model=list[DailySummary], dependencies=[Depends(role_required(["MANAGER"]))])
async def get_daily_summary(
    db: AsyncSession = Depends(get_db),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...)
):
    result = await db.execute(
        select(
            cast(Order.created_at, Date).label("order_date"),
            func.count(Order.id),
            func.sum(OrderItem.quantity * MenuItem.price)
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .where(
            Order.is_paid == True,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
        .group_by("order_date")
        .order_by("order_date")
    )

    rows = result.all()

    return [
        DailySummary(
            date=str(r[0]),
            total_orders=r[1],
            total_revenue=round(r[2] or 0.0, 2)
        )
        for r in rows
    ]
