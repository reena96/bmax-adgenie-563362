# ZapCut AdGenie - Backend API

Backend API server for ZapCut AdGenie, an AI-powered video ad generation platform.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Cache/Queue**: Redis with RQ (Redis Queue)
- **Storage**: AWS S3
- **Migrations**: Alembic
- **Testing**: pytest
- **Containerization**: Docker & Docker Compose

## Quick Start with Docker Compose

The fastest way to get the entire stack running:

```bash
# 1. Copy environment variables template
cp .env.example .env

# 2. Edit .env and add your AWS credentials
nano .env  # or use your preferred editor

# 3. Start all services (PostgreSQL, Redis, FastAPI, RQ Worker)
docker-compose up

# 4. In another terminal, run database migrations
docker-compose exec backend alembic upgrade head

# 5. Access the API
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/api/health
```

That's it! The entire backend stack is now running.

## Manual Local Setup (without Docker)

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+
- AWS Account with S3 access

### Installation Steps

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 4. Start PostgreSQL and Redis
# (Make sure they're running on localhost:5432 and localhost:6379)

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --reload

# 7. (Optional) Start RQ worker in another terminal
rq worker default
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback last migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

## Database Schema

The database includes 8 tables:

1. **users** - User accounts and subscription management
2. **brands** - Brand information and guidelines
3. **lora_models** - LoRA fine-tuned model tracking
4. **ad_projects** - Individual ad generation projects
5. **chat_messages** - AI chat conversation history
6. **scripts** - Approved video scripts
7. **generation_jobs** - Async video generation job tracking
8. **sessions** - User session/token management

All tables use UUID primary keys and include proper foreign key constraints with CASCADE delete.

## API Endpoints

### Health Check
- `GET /api/health` - Returns API health status and dependency connectivity

### Authentication (Story 1.2 - Coming Soon)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Brands (Story 1.3 - Coming Soon)
- `POST /api/brands` - Create brand
- `GET /api/brands` - List user's brands
- `GET /api/brands/{id}` - Get brand details
- `PUT /api/brands/{id}` - Update brand
- `DELETE /api/brands/{id}` - Delete brand

### Projects (Story 1.4 - Coming Soon)
- `POST /api/projects` - Create ad project
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/zapcut_adgen` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key | Your AWS key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | Your AWS secret |
| `AWS_S3_BUCKET` | S3 bucket name | `zapcut-adgen-dev` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `SECRET_KEY` | JWT token secret | Random secure string |
| `DEBUG` | Debug mode | `True` or `False` |

## AWS S3 Setup

The application uses S3 for file storage with the following folder structure:

```
s3://your-bucket-name/
├── generated-videos/    # Final composite video outputs
├── product-images/      # User-uploaded product images
├── brand-assets/        # Brand guidelines and assets
├── scene-videos/        # Individual scene videos from Sora
└── audio/              # Voiceovers, music, sound effects
```

### Required IAM Permissions

Your AWS IAM user needs the following S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

## Testing

### Run all tests

```bash
pytest
```

### Run with coverage report

```bash
pytest --cov=app --cov-report=html
```

### Run specific test file

```bash
pytest tests/test_health.py
```

### Run tests in Docker

```bash
docker-compose exec backend pytest
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database connection setup
│   ├── redis_client.py      # Redis and RQ setup
│   ├── s3_client.py         # S3 utilities
│   ├── routes/              # API route modules
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── brands.py
│   │   └── projects.py
│   ├── jobs/                # Background job workers
│   │   └── video_generation.py
│   └── utils/
│       └── logger.py        # Logging configuration
├── migrations/              # Alembic database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_database.py
│   └── test_s3.py
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── requirements.txt         # Python dependencies
├── alembic.ini             # Alembic configuration
├── .env.example            # Environment variables template
├── .gitignore
└── README.md
```

## Background Jobs with RQ

The application uses RQ (Redis Queue) for asynchronous job processing.

### Starting a worker

```bash
# Local
rq worker default

# Docker
docker-compose up worker
```

### Monitoring jobs

```bash
# Install RQ dashboard
pip install rq-dashboard

# Run dashboard
rq-dashboard

# Access at http://localhost:9181
```

## Troubleshooting

### Connection Refused Error (Database)

**Problem**: `ConnectionRefusedError` when connecting to PostgreSQL

**Solutions**:
1. Ensure PostgreSQL is running: `docker-compose ps` or `pg_isready`
2. Check DATABASE_URL in `.env` matches your configuration
3. Verify PostgreSQL is listening on port 5432
4. If using Docker, ensure services are on the same network

### S3 Upload Fails

**Problem**: `InvalidAccessKeyId` or `AccessDenied` errors

**Solutions**:
1. Verify AWS credentials in `.env` are correct
2. Check IAM user has S3 permissions (see AWS S3 Setup section)
3. Ensure bucket name and region are correct
4. Test credentials with AWS CLI: `aws s3 ls`

### Redis Connection Failed

**Problem**: Cannot connect to Redis

**Solutions**:
1. Ensure Redis is running: `redis-cli ping`
2. Check REDIS_URL in `.env`
3. Verify Redis is listening on port 6379
4. If using Docker, check service health: `docker-compose ps`

### Migration Errors

**Problem**: `alembic upgrade head` fails

**Solutions**:
1. Ensure database exists and is accessible
2. Check DATABASE_URL is correct
3. Drop and recreate database if needed (development only!)
4. Review migration file for syntax errors

### Port Already in Use

**Problem**: Port 8000, 5432, or 6379 already in use

**Solutions**:
1. Find process using port: `lsof -i :8000` (macOS/Linux)
2. Kill process or change port in configuration
3. If using Docker, stop conflicting containers

## Development Workflow

1. Create a new branch for your feature
2. Make changes to code
3. Write tests for new functionality
4. Run tests: `pytest`
5. Update database schema if needed: `alembic revision --autogenerate -m "description"`
6. Apply migrations: `alembic upgrade head`
7. Test locally with Docker Compose
8. Commit changes and create pull request

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Use a strong, random `SECRET_KEY`
3. Use managed PostgreSQL (AWS RDS, etc.)
4. Use managed Redis (AWS ElastiCache, etc.)
5. Enable HTTPS/TLS
6. Set up proper logging and monitoring
7. Use environment-specific S3 buckets
8. Configure rate limiting and security headers
9. Run migrations before deploying new code
10. Use a process manager (systemd, supervisord) or container orchestration (Kubernetes)

## Contributing

1. Follow PEP 8 style guide
2. Write docstrings for all functions
3. Add type hints
4. Write tests for new features
5. Update this README if adding new functionality

## License

Proprietary - ZapCut AdGenie

## Support

For issues or questions, contact the development team.
