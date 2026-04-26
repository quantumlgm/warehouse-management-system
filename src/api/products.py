from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.models import Inventory, Products, Warehouses

router = APIRouter(prefix="/products")


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1)
    articul: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    category: str = Field(..., min_length=1)


class ProductUpdate(BaseModel):
    product_name: str | None = Field(None, min_length=1)
    articul: str | None = Field(None, min_length=1)
    price: int | None = Field(None, ge=0)
    category: str | None = Field(None, min_length=1)


class StockAdd(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class StockAdjust(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=0)


@router.get("/")
async def get_all_products(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Products))
    return result.scalars().all()


@router.post("/")
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_db)):
    existing = await session.execute(
        select(Products.id).where(Products.articul == payload.articul)
    )
    existing_id = existing.scalar()
    if existing_id is not None:
        raise HTTPException(status_code=400, detail="Артикул уже существует")

    product = Products(
        product_name=payload.product_name,
        articul=payload.articul,
        price=payload.price,
        category=payload.category,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


@router.get("/search/{articul}")
async def get_product_by_articul(articul: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Products).where(Products.articul == articul))
    product = result.scalar()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар с таким артикулом не найден")
    return product


@router.patch("/{product_id}")
async def update_product_by_id(
    product_id: int, payload: ProductUpdate, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Products).where(Products.id == product_id))
    product = result.scalar()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "articul" in data:
        existing = await session.execute(
            select(Products.id).where(
                Products.articul == data["articul"], Products.id != product_id
            )
        )
        existing_id = existing.scalar()
        if existing_id is not None:
            raise HTTPException(status_code=400, detail="Артикул уже существует")

    for key, value in data.items():
        setattr(product, key, value)

    await session.commit()
    await session.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product_by_id(product_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Products).where(Products.id == product_id))
    product = result.scalar()
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    inv_check = await session.execute(
        select(func.count())
        .select_from(Inventory)
        .where(Inventory.product_id == product_id, Inventory.quantity > 0)
    )
    has_stock = (inv_check.scalar() or 0) > 0
    if has_stock:
        raise HTTPException(
            status_code=400, detail="Нельзя удалить товар: есть остатки на складах"
        )

    await session.delete(product)
    await session.commit()
    return {"detail": "Товар удалён", "product_id": product_id}


@router.get("/stock/{warehouse_id}")
async def get_stock_by_warehouse_id(
    warehouse_id: int, session: AsyncSession = Depends(get_db)
):
    query = (
        select(Inventory)
        .options(joinedload(Inventory.containing_product))
        .where(Inventory.warehouse_id == warehouse_id, Inventory.quantity > 0)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/stock/add")
async def add_stock_to_warehouse(payload: StockAdd, session: AsyncSession = Depends(get_db)):
    product_result = await session.execute(
        select(Products.id).where(Products.id == payload.product_id)
    )
    if product_result.scalar() is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    warehouse_result = await session.execute(
        select(Warehouses.id).where(Warehouses.id == payload.warehouse_id)
    )
    if warehouse_result.scalar() is None:
        raise HTTPException(status_code=404, detail="Склад не найден")

    inv_result = await session.execute(
        select(Inventory).where(
            Inventory.product_id == payload.product_id,
            Inventory.warehouse_id == payload.warehouse_id,
        )
    )
    inv = inv_result.scalar()

    if inv is None:
        inv = Inventory(
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
        )
        session.add(inv)
    else:
        inv.quantity += payload.quantity

    await session.commit()
    await session.refresh(inv)
    return inv


@router.patch("/stock/adjust")
async def adjust_stock_quantity(payload: StockAdjust, session: AsyncSession = Depends(get_db)):
    inv_result = await session.execute(
        select(Inventory).where(
            Inventory.product_id == payload.product_id,
            Inventory.warehouse_id == payload.warehouse_id,
        )
    )
    inv = inv_result.scalar()
    if inv is None:
        raise HTTPException(status_code=404, detail="Запись в остатках не найдена")

    inv.quantity = payload.quantity
    await session.commit()
    await session.refresh(inv)
    return inv


@router.get("/where-is/{product_id}")
async def get_where_is_product(product_id: int, session: AsyncSession = Depends(get_db)):
    query = (
        select(Inventory)
        .options(joinedload(Inventory.containing_warehouse))
        .where(Inventory.product_id == product_id)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/category/{category_name}")
async def get_inventory_by_category_name(
    category_name: str, session: AsyncSession = Depends(get_db)
):
    query = (
        select(Inventory)
        .join(Products)
        .options(joinedload(Inventory.containing_product))
        .where(Products.category == category_name, Inventory.quantity > 0)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/low-stock")
async def get_low_stock_inventory(session: AsyncSession = Depends(get_db)):
    query = (
        select(Inventory)
        .options(
            joinedload(Inventory.containing_product),
            joinedload(Inventory.containing_warehouse),
        )
        .where(Inventory.quantity <= 5)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/total-count/{product_id}")
async def get_total_count_by_product_id(
    product_id: int, session: AsyncSession = Depends(get_db)
):
    query = select(func.sum(Inventory.quantity)).where(Inventory.product_id == product_id)
    result = await session.execute(query)
    total = result.scalar() or 0
    return {"product_id": product_id, "total_count": int(total)}


@router.get("/value/{warehouse_id}")
async def get_warehouse_value_by_id(
    warehouse_id: int, session: AsyncSession = Depends(get_db)
):
    query = (
        select(func.sum(Inventory.quantity * Products.price))
        .join(Products)
        .where(Inventory.warehouse_id == warehouse_id)
    )
    result = await session.execute(query)
    total_value = result.scalar() or 0
    return {"warehouse_id": warehouse_id, "total_value": int(total_value)}