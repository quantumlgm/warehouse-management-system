from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
class Warehouses(Base):
    warehouse_name: Mapped[str] = mapped_column(server_default='Склад неуказан')
    warehouse_phone: Mapped[str] = mapped_column(server_default='Номер неуказан')
    address: Mapped[str]

    incoming_shipments: Mapped[list['Movements']] = relationship(
        back_populates='to_warehouse',
        foreign_keys='[Movements.to_warehouse_id]'
    )
    outgoing_shipments: Mapped[list['Movements']] = relationship(
        back_populates='from_warehouse',
        foreign_keys='[Movements.from_warehouse_id]' 
    )
    relevant_product: Mapped[list['Inventory']] = relationship(back_populates='containing_warehouse')
    
class Products(Base):
    product_name: Mapped[str] = mapped_column(server_default='Название неуказано')
    articul: Mapped[str] = mapped_column(unique=True)
    price: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(server_default='Категория неуказана')
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    all_movements: Mapped[list['Movements']] = relationship(back_populates='product')
    relevant_warehouse: Mapped[list['Inventory']] = relationship(back_populates='containing_product')
    
class Inventory(Base):
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouses.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] 

    containing_warehouse: Mapped['Warehouses'] = relationship(back_populates='relevant_product')
    containing_product: Mapped['Products'] = relationship(back_populates='relevant_warehouse')

class Employee(Base):
    name: Mapped[str] = mapped_column(nullable=False)
    initials: Mapped[str] = mapped_column(server_default='Инициалы неуказаны')
    phone_number: Mapped[str] = mapped_column(nullable=False) 
    
    movements: Mapped[list['Movements']] = relationship(back_populates='responsibl_person')

class Movements(Base):
    from_warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouses.id'))
    to_warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouses.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    responsibl_id: Mapped[int] = mapped_column(ForeignKey('employee.id'))

    product: Mapped['Products'] = relationship(back_populates='all_movements')
    responsibl_person: Mapped['Employee'] = relationship(back_populates='movements')
    to_warehouse: Mapped['Warehouses'] = relationship(
        back_populates='incoming_shipments', 
        foreign_keys=[to_warehouse_id]
    )
    from_warehouse: Mapped['Warehouses'] = relationship(
        back_populates='outgoing_shipments', 
        foreign_keys=[from_warehouse_id]
    )