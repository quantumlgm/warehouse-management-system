# Warehouse Managment System

## Features
1. Comprehensive API Endpoints: Provides a wide range of endpoints for flexible tool management.
2. Item Status Tracking: Robust capabilities for managing and monitoring item statuses in real-time.
3. Optimized Data Models: Logical database schema with well-defined relationships using SQLAlchemy.

## Tech stack
* Language: Python 3.12.10
* Framework: FastApi 0.136.1
* ORM: SQLAlchemy 2.0.49
* Database: PostgresSQL 17.9

## How to Run

### 1. Installation
```bash
git clone https://github.com/quantumlgm/warehouse-management-system)
cd warehouse-management-system
```
### 2. Environment Setup
Create a .env file in the root directory and configure your database credentials:
```bash
DB_USER_NAME=your_db_username
DB_HOST=localhost
DB_DATABASE=WarehouseManagementServer
DB_PASSWORD=your_db_password
DB_PORT=5432
```
### 3. Create a virtual environment
```bash
python -m venv .venv
# For Windows:
.venv\Scripts\activate
# For Linux/macOS:
source .venv/bin/activate
```
### 4. Installation Dependenses
```bash
pip install -r requirements.txt
```
### 5. Start a server
```bash
uvicorn main:app --reload
```
and click on link
```bash
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
### 6. Use the interface
1. http://127.0.0.1:8000/scalar - Scalar (RECOMENDED)
2. http://127.0.0.1:8000/docs - Swagger
3. http://127.0.0.1:8000/redoc - Redoc
