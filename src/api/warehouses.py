from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Inventory, Warehouses

router = APIRouter(prefix="/warehouses")


class WarehouseCreate(BaseModel):
    warehouse_name: str = Field(..., min_length=1)
    warehouse_phone: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)


class WarehouseUpdate(BaseModel):
    warehouse_name: str | None = Field(None, min_length=1)
    warehouse_phone: str | None = Field(None, min_length=1)
    address: str | None = Field(None, min_length=1)


@router.post("/")
async def create_warehouse(payload: WarehouseCreate, session: AsyncSession = Depends(get_db)):
    warehouse = Warehouses(
        warehouse_name=payload.warehouse_name,
        warehouse_phone=payload.warehouse_phone,
        address=payload.address,
    )
    session.add(warehouse)
    await session.commit()
    await session.refresh(warehouse)
    return warehouse


@router.get("/")
async def get_all_warehouses(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Warehouses))
    return result.scalars().all()


@router.get("/{warehouse_id}")
async def get_warehouse_by_id(
    warehouse_id: int, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Warehouses).where(Warehouses.id == warehouse_id))
    warehouse = result.scalar()
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return warehouse


@router.patch("/{warehouse_id}")
async def update_warehouse_by_id(
    warehouse_id: int, payload: WarehouseUpdate, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Warehouses).where(Warehouses.id == warehouse_id))
    warehouse = result.scalar()
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Склад не найден")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in data.items():
        setattr(warehouse, key, value)

    await session.commit()
    await session.refresh(warehouse)
    return warehouse


@router.delete("/{warehouse_id}")
async def delete_warehouse_by_id(
    warehouse_id: int, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Warehouses).where(Warehouses.id == warehouse_id))
    warehouse = result.scalar()
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Склад не найден")

    inv_check = await session.execute(
        select(func.count())
        .select_from(Inventory)
        .where(Inventory.warehouse_id == warehouse_id, Inventory.quantity > 0)
    )
    has_stock = (inv_check.scalar() or 0) > 0
    if has_stock:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить склад, пока на нем есть товары",
        )

    await session.delete(warehouse)
    await session.commit()
    return {"detail": "Склад удалён", "warehouse_id": warehouse_id}

