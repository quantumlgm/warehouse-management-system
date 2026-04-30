from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.models import Employee, Inventory, Movements, Products, Warehouses

router = APIRouter(prefix="/movements")


class MovementCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    from_warehouse_id: int = Field(..., gt=0)
    to_warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    responsibl_id: int = Field(..., gt=0)


@router.post("/transfer")
async def transfer_product(payload: MovementCreate, session: AsyncSession = Depends(get_db)):
    if payload.from_warehouse_id == payload.to_warehouse_id:
        raise HTTPException(
            status_code=400, detail="Склад отправления и склад получения не должны совпадать"
        )

    # Existence checks (404)
    product_id_res = await session.execute(
        select(Products.id).where(Products.id == payload.product_id)
    )
    if product_id_res.scalar() is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    from_wh_res = await session.execute(
        select(Warehouses.id).where(Warehouses.id == payload.from_warehouse_id)
    )
    if from_wh_res.scalar() is None:
        raise HTTPException(status_code=404, detail="Склад отправления не найден")

    to_wh_res = await session.execute(
        select(Warehouses.id).where(Warehouses.id == payload.to_warehouse_id)
    )
    if to_wh_res.scalar() is None:
        raise HTTPException(status_code=404, detail="Склад получения не найден")

    emp_res = await session.execute(
        select(Employee.id).where(Employee.id == payload.responsibl_id)
    )
    if emp_res.scalar() is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    try:
        # Check and decrement from-warehouse stock
        from_inv_res = await session.execute(
            select(Inventory)
            .where(
                Inventory.product_id == payload.product_id,
                Inventory.warehouse_id == payload.from_warehouse_id,
            )
            .with_for_update()
        )
        from_inv = from_inv_res.scalar()
        if from_inv is None or from_inv.quantity < payload.quantity:
            raise HTTPException(
                status_code=400,
                detail="Недостаточно товара на складе отправления",
            )

        from_inv.quantity -= payload.quantity

        # Increment/create to-warehouse stock
        to_inv_res = await session.execute(
            select(Inventory)
            .where(
                Inventory.product_id == payload.product_id,
                Inventory.warehouse_id == payload.to_warehouse_id,
            )
            .with_for_update()
        )
        to_inv = to_inv_res.scalar()
        if to_inv is None:
            to_inv = Inventory(
                product_id=payload.product_id,
                warehouse_id=payload.to_warehouse_id,
                quantity=payload.quantity,
            )
            session.add(to_inv)
        else:
            to_inv.quantity += payload.quantity

        movement = Movements(
            from_warehouse_id=payload.from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            product_id=payload.product_id,
            responsibl_id=payload.responsibl_id,
        )
        session.add(movement)

        await session.commit()
    except HTTPException:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise

    # Return movement with full related info
    movement_res = await session.execute(
        select(Movements)
        .options(
            joinedload(Movements.product),
            joinedload(Movements.from_warehouse),
            joinedload(Movements.to_warehouse),
            joinedload(Movements.responsibl_person),
        )
        .where(Movements.id == movement.id)
    )
    return movement_res.scalar()


@router.get("/history")
async def get_movements_history(session: AsyncSession = Depends(get_db)):
    query = (
        select(Movements)
        .options(
            joinedload(Movements.product),
            joinedload(Movements.from_warehouse),
            joinedload(Movements.to_warehouse),
            joinedload(Movements.responsibl_person),
        )
        .order_by(Movements.id.desc())
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/history/product/{product_id}")
async def get_movements_history_by_product_id(
    product_id: int, session: AsyncSession = Depends(get_db)
):
    exists = await session.execute(select(Products.id).where(Products.id == product_id))
    if exists.scalar() is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    query = (
        select(Movements)
        .options(
            joinedload(Movements.product),
            joinedload(Movements.from_warehouse),
            joinedload(Movements.to_warehouse),
            joinedload(Movements.responsibl_person),
        )
        .where(Movements.product_id == product_id)
        .order_by(Movements.id.desc())
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/history/warehouse/{warehouse_id}")
async def get_movements_history_by_warehouse_id(
    warehouse_id: int, session: AsyncSession = Depends(get_db)
):
    exists = await session.execute(
        select(Warehouses.id).where(Warehouses.id == warehouse_id)
    )
    if exists.scalar() is None:
        raise HTTPException(status_code=404, detail="Склад не найден")

    query = (
        select(Movements)
        .options(
            joinedload(Movements.product),
            joinedload(Movements.from_warehouse),
            joinedload(Movements.to_warehouse),
            joinedload(Movements.responsibl_person),
        )
        .where(
            or_(
                Movements.from_warehouse_id == warehouse_id,
                Movements.to_warehouse_id == warehouse_id,
            )
        )
        .order_by(Movements.id.desc())
    )
    result = await session.execute(query)
    return result.scalars().all()

