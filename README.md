# Warehouse Managment System

## Features
1. Comprehensive API Endpoints: Provides a wide range of endpoints for flexible tool management.
2. Item Status Tracking: Robust capabilities for managing and monitoring item statuses in real-time.
3. Optimized Data Models: Logical database schema with well-defined relationships using SQLAlchemy.

## Tech stack
* Language: Python 3.12.10
* Framework: FastApi 0.136.1
* ORM: SQLAlchemy 2.0.49
* Migrations: Alembic 1.18.4
* Database: PostgreSQL 17.9
* Environment: Docker & Docker Compose

# How to Run
### 1. Initial Setup (Required for both methods)
```bash
git clone https://github.com/quantumlgm/warehouse-management-system
cd warehouse-management-system
```
### 2. Environment Setup
```bash
DB_USER_NAME=your_db_username
DB_HOST=db  # Use 'db' for Docker or 'localhost' for local run
DB_DATABASE=WarehouseManagementServer
DB_PASSWORD=your_db_password
DB_PORT=5432
```
# 2. Choose your way to run
## A: Run with Docker (Recommended)
### 3. Launch containers:
```bash
docker-compose up --build
```
### 4. Apply migrations:
```bash
docker-compose exec app alembic upgrade head
```
## B: Local Installation
### 3. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```
### 4. Install Dependencies:
```bash
pip install -r requirements.txt
```
### 5. Create tables:
```bash
alembic upgrade head
```
### 6. Run the server:
```bash
uvicorn src.main:app --reload
```
## Use the interface
1. http://127.0.0.1:8000/scalar - Scalar (RECOMENDED)
2. http://127.0.0.1:8000/docs - Swagger
3. http://127.0.0.1:8000/redoc - Redoc
