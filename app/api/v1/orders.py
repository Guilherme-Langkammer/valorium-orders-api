from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.order import Order, OrderItem
from app.schemas.order import (
    OrderCreate, OrderRead, OrderStatusUpdate
)

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
)

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": set(),
    "cancelled": set(),
}


@router.post("", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    total = sum(
        item.quantity * item.unit_price_cents
        for item in payload.items
    )

    order = Order(
        customer_name=payload.customer_name,
        status="pending",
        total_cents=total,
        items=[
            OrderItem(**item.model_dump())
            for item in payload.items
        ],
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(
        select(Order).order_by(Order.id.desc())
    ).all()


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.status not in ALLOWED_TRANSITIONS[order.status]:
        raise HTTPException(
            status_code=409,
            detail="Invalid order status transition",
        )

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
