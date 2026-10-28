# Valorium Orders API

[![Backend CI](https://github.com/Guilherme-Langkammer/valorium-orders-api/actions/workflows/tests.yml/badge.svg)](https://github.com/Guilherme-Langkammer/valorium-orders-api/actions/workflows/tests.yml)
[![Docker CI](https://github.com/Guilherme-Langkammer/valorium-orders-api/actions/workflows/docker.yml/badge.svg)](https://github.com/Guilherme-Langkammer/valorium-orders-api/actions/workflows/docker.yml)

A RESTful order management API built with Python, FastAPI, SQLAlchemy, and Alembic.

This is an independent, public backend engineering portfolio project demonstrating API design, relational data modeling, request validation, database migrations, business rules, and automated testing.

## Features

- Create orders containing one or more items
- Automatically calculate order totals using integer cents
- List orders and retrieve individual orders
- Manage order status transitions
- Validate requests using Pydantic
- Persist orders and items using SQLAlchemy
- Manage database schema changes with Alembic
- Run automated tests with pytest
- Explore the API using interactive OpenAPI documentation

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite
- pytest
- Uvicorn

## Project Structure

```text
valorium-orders-api/
|-- alembic/
|   |-- versions/
|   `-- env.py
|-- app/
|   |-- api/
|   |   `-- v1/
|   |       |-- health.py
|   |       `-- orders.py
|   |-- core/
|   |-- db/
|   |   `-- database.py
|   |-- models/
|   |   `-- order.py
|   |-- schemas/
|   |   `-- order.py
|   |-- services/
|   `-- main.py
|-- tests/
|   |-- test_health.py
|   `-- test_orders.py
|-- alembic.ini
|-- main.py
|-- pytest.ini
`-- requirements.txt
```

The `core` and `services` directories are reserved for future extensions.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Check API health |
| POST | `/api/v1/orders` | Create an order |
| GET | `/api/v1/orders` | List orders |
| GET | `/api/v1/orders/{order_id}` | Retrieve an order |
| PATCH | `/api/v1/orders/{order_id}/status` | Update order status |

Interactive documentation is available at `/docs`.

## Order Creation Example

Request:

```http
POST /api/v1/orders
Content-Type: application/json
```

```json
{
  "customer_name": "Demo Customer",
  "items": [
    {
      "product_name": "Coffee",
      "quantity": 2,
      "unit_price_cents": 1250
    }
  ]
}
```

The API creates an order with:

- Initial status: `pending`
- Calculated total: `2500` cents
- One associated order item

A successful creation returns HTTP `201`.

Monetary values use integer cents to avoid floating-point rounding issues.

## Order Status Rules

Supported statuses:

- `pending`
- `confirmed`
- `cancelled`

Allowed transitions:

```text
pending
  |-- confirmed
  `-- cancelled
```

Orders in `confirmed` or `cancelled` status cannot transition to another status in the current implementation.

Invalid status transitions return HTTP `409 Conflict`.

Example:

```http
PATCH /api/v1/orders/1/status
Content-Type: application/json
```

```json
{
  "status": "confirmed"
}
```

## Validation and Error Handling

The API uses Pydantic to enforce input constraints.

Examples:

- Customer names must contain at least one character
- Orders must contain at least one item
- Product names must contain at least one character
- Item quantities must be greater than zero
- Unit prices cannot be negative

Invalid request data returns HTTP `422`.

Requests for nonexistent orders return HTTP `404`.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Guilherme-Langkammer/valorium-orders-api.git
cd valorium-orders-api
```

This repository is publicly available on GitHub.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python -m alembic upgrade head
```

The default configuration uses a local SQLite database named `orders.db`.

You can override the database connection through the `DATABASE_URL` environment variable.

### 5. Start the API

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Database Migrations

Database schema changes are managed through Alembic.

Apply migrations:

```bash
python -m alembic upgrade head
```

Show the current revision:

```bash
python -m alembic current
```

The application does not automatically create database tables at startup. Run the migrations before using the order endpoints.

## Automated Tests

Run the test suite:

```bash
python -m pytest -q
```

The current test suite covers:

- Health endpoint
- OpenAPI schema availability
- Order creation and total calculation
- Order listing and retrieval
- Empty item list validation
- Negative price validation
- Valid and invalid status transitions
- Missing order handling

Order tests use an isolated in-memory SQLite database.

## Architecture Overview

```mermaid
flowchart TD
    A[HTTP Client] --> B[FastAPI Application]
    B --> C[API Routes]
    C --> D[Pydantic Schemas]
    C --> E[SQLAlchemy ORM]
    E --> F[(SQLite Database)]
    G[Alembic Migrations] --> F
    H[Docker Compose] --> B
    H --> I[Persistent Docker Volume]
    F -. Docker deployment .-> I
```

The API separates HTTP routing, data validation, ORM models, and database configuration. Docker Compose runs database migrations before starting the application and stores SQLite data in a named volume.

## Architecture Notes

The project separates:

- HTTP routes in `app/api`
- Request and response contracts in `app/schemas`
- ORM entities in `app/models`
- Database configuration in `app/db`
- Application initialization in `app/main.py`
- Automated tests in `tests`

This structure supports future improvements without coupling HTTP handling directly to database configuration.

## Project Status

This is a portfolio project under active development.

Current functionality focuses on order management, database migrations, and automated testing.

Authentication, authorization, and production deployment are not implemented in the current version.

Docker and Docker Compose are validated automatically on GitHub-hosted Ubuntu runners through the Docker CI workflow.

GitHub Actions CI is implemented and has successfully completed its initial run.


## Docker

The project includes a Dockerfile and Docker Compose configuration.

The container runs the API as a non-root user. Docker Compose applies Alembic migrations before starting Uvicorn and uses a named volume to persist the SQLite database.

Start the application:

```bash
docker compose up --build -d
```

Open the API documentation at http://127.0.0.1:8000/docs.

Stop the containers:

```bash
docker compose down
```

The named database volume is retained by default. Avoid using `docker compose down -v` if you want to preserve the database.

**Validation status:** Docker CI successfully builds the image, starts the API, verifies the health endpoint and Alembic migrations, and confirms SQLite persistence after a container restart.

## Continuous Integration

GitHub Actions runs two independent workflows on pushes and pull requests targeting `main`.

### Backend CI

- Sets up Python 3.14 on Ubuntu
- Installs project dependencies
- Validates Python syntax
- Applies Alembic migrations
- Runs automated pytest tests

### Docker CI

- Builds the application Docker image
- Starts the API through Docker Compose
- Checks the `/health` endpoint
- Verifies the Alembic migration in SQLite
- Writes a persistence marker to the database
- Restarts the API container
- Confirms that the marker survives the restart
- Collects logs on failure and cleans up test resources

Both workflows passed on commit `7c21cb8`.

These checks run on GitHub-hosted Ubuntu runners; Docker does not need to be installed on the developer's Windows machine.

## Author

Guilherme Langkammer

GitHub: https://github.com/Guilherme-Langkammer

## Disclaimer

This repository is an independent demonstration project. It does not contain proprietary customer systems, production credentials, or commercial application source code.