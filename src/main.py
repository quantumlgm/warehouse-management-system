from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from src.api.products import router as products_route

app = FastAPI()
app.include_router(products_route)

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        scalar_proxy_url="https://proxy.scalar.com",
    )

@app.get('/')
async def home_page():
    return {'Status:': '200'}