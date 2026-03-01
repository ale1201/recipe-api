# Recipe Sharing API

A recipe sharing platform API built with FastAPI, SQLAlchemy, and PostgreSQL.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (for PostgreSQL)

## Quick Start

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (includes dev dependencies for testing)
pip install -e ".[dev]"

# Start the PostgreSQL database
docker compose up -d db

# Run the API server (auto-seeds sample data on first start)
uvicorn app.main:app --reload

# API docs: http://localhost:8000/docs
```

## Running Tests

Tests use SQLite in-memory, so no database setup is needed:

```bash
pytest
```

## Project Structure

```
app/
├── api/v1/          # API endpoints and routing
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
├── repositories/    # Data access layer
└── seed/            # Sample data for development
```

## API Endpoints

### Auth
- `POST /api/v1/auth/register` — Create a new account
- `POST /api/v1/auth/login` — Get an access token

### Recipes
- `GET /api/v1/recipes/` — List all recipes (paginated)
- `GET /api/v1/recipes/{id}` — Get a recipe with ingredients
- `POST /api/v1/recipes/` — Create a recipe (auth required)
- `PUT /api/v1/recipes/{id}` — Update a recipe (owner only)
- `DELETE /api/v1/recipes/{id}` — Delete a recipe (owner only)

## Seed Data

On first startup, the API seeds 12 sample recipes across various cuisines with two demo accounts:

| Username | Password |
|----------|----------|
| `chef_maria` | `password123` |
| `home_cook_bob` | `password123` |

## Docker

To run the full stack with Docker:

```bash
docker compose up --build
```

This starts both PostgreSQL and the API server.
