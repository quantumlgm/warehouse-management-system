from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from src.api.products import router as products_route
from src.api.warehouses import router as warehouses_route
from src.api.employees import router as employees_route
from src.api.movements import router as movements_route

app = FastAPI()
app.include_router(products_route)
app.include_router(warehouses_route)
app.include_router(employees_route)
app.include_router(movements_route)

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        scalar_proxy_url="https://proxy.scalar.com",
    )

@app.get('/')
async def home_page():
    return {'Status:': '200'}