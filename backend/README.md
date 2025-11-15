# Zapcut Ad Generation API - Backend

AI-powered ad generation backend built with FastAPI, PostgreSQL, and Redis.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Development](#development)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Database Migrations](#database-migrations)
- [Adding New Routes](#adding-new-routes)
- [Troubleshooting](#troubleshooting)

## Overview

This is the backend API for the Zapcut Ad Generation platform. It provides:

- RESTful API endpoints for brand management, ad projects, and script generation
- PostgreSQL database with SQLAlchemy ORM
- Redis integration for job queuing and caching
- JWT-based authentication (to be implemented)
- Comprehensive error handling and logging
- Swagger/OpenAPI documentation

**Technology Stack:**
- Python 3.11+
- FastAPI (web framework)
- SQLAlchemy 2.0+ (ORM)
- PostgreSQL 14+ (database)
- Redis (cache and queue)
- Alembic (migrations)
- Pydantic (validation)
- pytest (testing)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher**
- **PostgreSQL 14 or higher**
- **Redis** (for queue and caching)
- **pip** (Python package manager)

### Installing Prerequisites

**macOS (using Homebrew):**
```bash
brew install python@3.11 postgresql@14 redis
brew services start postgresql
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql-14 redis-server
sudo systemctl start postgresql
sudo systemctl start redis
```

## Installation

### 1. Clone the repository (if not already done)

```bash
git clone <repository-url>
cd backend
```

### 2. Create and activate virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

This will install all required packages including development dependencies.

### 4. Set up PostgreSQL database

Create the development database:

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE zapcut_db_dev;

# Create test database (for running tests)
CREATE DATABASE test_zapcut_db;

# Exit psql
\q
```

### 5. Configure environment variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` and update the following critical variables:

```env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/zapcut_db_dev
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run database migrations

```bash
alembic upgrade head
```

## Configuration

### Environment Variables

All configuration is managed through environment variables. Here are the key variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Application environment (development/staging/production) | development | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | DEBUG | No |
| `DATABASE_URL` | PostgreSQL connection URL | postgresql://postgres:postgres@localhost:5432/zapcut_db_dev | Yes |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 | Yes |
| `SECRET_KEY` | JWT signing secret key | Auto-generated | Yes (prod) |
| `FRONTEND_URL` | Frontend URL for CORS | http://localhost:3000 | No |

See `.env.example` for a complete list of available configuration options.

### Generating a Secret Key

For production, generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Running the Application

### Using uvicorn directly

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using Makefile

```bash
make run
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## Development

### Makefile Commands

The project includes a Makefile with common development tasks:

```bash
make help              # Show all available commands
make install           # Install dependencies
make run              # Run development server
make test             # Run tests
make coverage         # Run tests with coverage report
make migrate          # Apply database migrations
make migrate-create   # Create a new migration
make lint             # Run linting
make format           # Format code with black
make clean            # Clean up temporary files
```

### Code Formatting

This project uses **black** for code formatting:

```bash
make format
# or
black app tests
```

### Linting

Run linting with **flake8** and **mypy**:

```bash
make lint
# or
flake8 app tests
mypy app
```

## Testing

### Running Tests

Run all tests:

```bash
pytest
# or
make test
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
# or
make coverage
```

Run specific tests:

```bash
pytest tests/test_health.py
pytest tests/test_health.py::test_health_check_endpoint
```

### Test Markers

Tests are organized with markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.db` - Tests requiring database

Run specific marker:

```bash
pytest -m unit
pytest -m integration
```

## API Documentation

### Interactive Documentation

When the server is running, access interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

#### Health & System

- `GET /` - Root endpoint with API info
- `GET /api/health` - Comprehensive health check
- `GET /api/health/ready` - Readiness probe
- `GET /api/health/live` - Liveness probe

#### Authentication (Stub - To be implemented)

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - User logout

#### Brands (Stub - To be implemented)

- `GET /api/brands/` - List all brands
- `POST /api/brands/` - Create a brand
- `GET /api/brands/{brand_id}` - Get brand details
- `PUT /api/brands/{brand_id}` - Update brand
- `DELETE /api/brands/{brand_id}` - Delete brand

#### Projects (Stub - To be implemented)

- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create a project
- `GET /api/projects/{project_id}` - Get project details
- `PUT /api/projects/{project_id}` - Update project
- `DELETE /api/projects/{project_id}` - Delete project

## Project Structure

```
backend/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Configuration management
│   ├── database.py              # Database connection & session
│   ├── exceptions.py            # Custom exception classes
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── brand.py
│   │   ├── ad_project.py
│   │   ├── chat_message.py
│   │   ├── script.py
│   │   ├── generation_job.py
│   │   └── lora_model.py
│   ├── schemas/                 # Pydantic schemas (request/response)
│   │   ├── user.py
│   │   ├── brand.py
│   │   └── project.py
│   ├── routes/                  # API routes
│   │   ├── health.py           # Health check endpoints
│   │   ├── auth.py             # Authentication (stub)
│   │   ├── brands.py           # Brand management (stub)
│   │   ├── projects.py         # Project management (stub)
│   │   ├── chat.py             # Chat interface (stub)
│   │   └── scripts.py          # Script generation (stub)
│   ├── services/                # Business logic (to be added)
│   ├── middleware/              # Custom middleware
│   │   ├── logging.py          # Request/response logging
│   │   └── error_handler.py    # Global error handling
│   └── utils/                   # Utility functions (to be added)
├── migrations/                   # Alembic migrations
│   ├── versions/                # Migration scripts
│   │   └── 001_initial_migration.py
│   ├── env.py                  # Alembic environment
│   └── script.py.mako          # Migration template
├── tests/                       # Test files
│   ├── conftest.py             # pytest fixtures
│   ├── test_health.py          # Health endpoint tests
│   └── unit/                   # Unit tests (to be added)
├── .env                        # Environment variables (git-ignored)
├── .env.example                # Example environment file
├── .gitignore                  # Git ignore rules
├── alembic.ini                 # Alembic configuration
├── pytest.ini                  # pytest configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Makefile                    # Common development tasks
└── README.md                   # This file
```

## Database Migrations

### Creating a New Migration

After modifying models in `app/models/`, create a migration:

```bash
alembic revision --autogenerate -m "Description of changes"
# or
make migrate-create
```

### Reviewing Migrations

**IMPORTANT**: Always review auto-generated migrations before applying:

```bash
cat migrations/versions/<latest_migration>.py
```

### Applying Migrations

Apply all pending migrations:

```bash
alembic upgrade head
# or
make migrate
```

### Rolling Back Migrations

Rollback the last migration:

```bash
alembic downgrade -1
# or
make migrate-downgrade
```

### Migration Best Practices

1. Always review auto-generated migrations
2. Test migrations on a development database first
3. Never modify migrations that have been applied in production
4. Create separate migrations for data changes vs schema changes

## Adding New Routes

### 1. Create the Route File

Create a new file in `app/routes/`:

```python
# app/routes/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/")
async def list_items(db: Session = Depends(get_db)):
    return {"items": []}
```

### 2. Register the Router

Add to `app/main.py`:

```python
from app.routes.example import router as example_router

# In create_app():
app.include_router(example_router, prefix="/api/example", tags=["Example"])
```

### 3. Add Tests

Create tests in `tests/`:

```python
# tests/test_example.py
def test_list_items(client):
    response = client.get("/api/example/")
    assert response.status_code == 200
```

## Troubleshooting

### Database Connection Issues

**Problem**: `could not connect to server: Connection refused`

**Solution**:
- Ensure PostgreSQL is running: `brew services start postgresql` (macOS) or `sudo systemctl start postgresql` (Linux)
- Verify DATABASE_URL in `.env` is correct
- Check PostgreSQL logs

### Redis Connection Issues

**Problem**: `Error connecting to Redis`

**Solution**:
- Ensure Redis is running: `brew services start redis` (macOS) or `sudo systemctl start redis` (Linux)
- Verify REDIS_URL in `.env` is correct

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements-dev.txt`
- Check that you're running commands from the `backend/` directory

### Migration Errors

**Problem**: `Target database is not up to date`

**Solution**:
- Run migrations: `alembic upgrade head`
- If issues persist, check migration files in `migrations/versions/`

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
- Find and kill the process: `lsof -ti:8000 | xargs kill -9`
- Or use a different port: `uvicorn app.main:app --port 8001`

## Support

For issues or questions:
1. Check this README
2. Review the inline code documentation
3. Check the API documentation at `/docs`
4. Consult the project's issue tracker
