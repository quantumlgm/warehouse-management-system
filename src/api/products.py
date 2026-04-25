from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, and_, func
from src.database import get_db
from src.models import Products, Inventory, Warehouses
from typing import Annotated


router = APIRouter(prefix='/products')

@router.get('/')
async def home_page(session: AsyncSession = Depends(get_db)):
    query = select(Products)
    result = await session.execute(query)
    products = result.scalars().all()
    return products

@router.get('/where')
async def get_product_location(
    product_id: Annotated[int, Query(gt=0)],
    warehouse_id: Annotated[int, Query(gt=0)],
    session: AsyncSession = Depends(get_db)
):
    query = (
        select(Inventory)
        .options(
            joinedload(Inventory.containing_product),
            joinedload(Inventory.containing_warehouse) 
        )
        .where(
            and_(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id
            )
        )
    )   
    result = await session.execute(query)
    return result
    
@router.get('/warehouse')
async def get_products_by_warehouse(
    warehouse_id: Annotated[int, Query(gt=0)],
    session: AsyncSession = Depends(get_db)
):
    query = (
        select(Inventory)
        .options(
            joinedload(Inventory.containing_product)
        )
        .where(
            and_(
                Inventory.warehouse_id == warehouse_id,
                Inventory.quantity > 0
            )
        )
    )
    result = await session.execute(query)
    return result

@router.get('/warehouse')
async def get_products_by_warehouse(
    warehouse_id: Annotated[int, Query(gt=0)],
    session: AsyncSession = Depends(get_db)
):
    query = (
        select(func.sum(Inventory.quantity * Products.price))
        .join(Products)
        .where(Inventory.warehouse_id == warehouse_id)
    )
    result = await session.execute(query)
    return result


