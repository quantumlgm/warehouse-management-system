from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.models import Employee, Movements

router = APIRouter(prefix="/employees")


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    initials: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=1)


class EmployeeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    initials: str | None = Field(None, min_length=1)
    phone_number: str | None = Field(None, min_length=1)


@router.post("/")
async def create_employee(payload: EmployeeCreate, session: AsyncSession = Depends(get_db)):
    employee = Employee(
        name=payload.name,
        initials=payload.initials,
        phone_number=payload.phone_number,
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee


@router.get("/")
async def get_all_employees(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Employee))
    return result.scalars().all()


@router.get("/{employee_id}")
async def get_employee_by_id(employee_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar()
    if employee is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return employee


@router.patch("/{employee_id}")
async def update_employee_by_id(
    employee_id: int, payload: EmployeeUpdate, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar()
    if employee is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in data.items():
        setattr(employee, key, value)

    await session.commit()
    await session.refresh(employee)
    return employee


@router.delete("/{employee_id}")
async def delete_employee_by_id(employee_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar()
    if employee is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    movements_check = await session.execute(
        select(func.count())
        .select_from(Movements)
        .where(Movements.responsibl_id == employee_id)
    )
    has_history = (movements_check.scalar() or 0) > 0
    if has_history:
        raise HTTPException(
            status_code=400,
            detail=(
                "Нельзя удалить сотрудника с историей операций. "
                "Лучше пометьте его как неактивного (в будущем)"
            ),
        )

    await session.delete(employee)
    await session.commit()
    return {"detail": "Сотрудник удалён", "employee_id": employee_id}


@router.get("/{employee_id}/history")
async def get_employee_history(employee_id: int, session: AsyncSession = Depends(get_db)):
    exists = await session.execute(select(Employee.id).where(Employee.id == employee_id))
    if exists.scalar() is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    query = (
        select(Movements)
        .options(
            joinedload(Movements.product),
            joinedload(Movements.to_warehouse),
            joinedload(Movements.from_warehouse),
        )
        .where(Movements.responsibl_id == employee_id)
    )
    result = await session.execute(query)
    return result.scalars().all()

