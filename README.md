# Asynchronous Job Queue Service

## Overview
The Asynchronous Job Queue Service is a backend system for handling long-running or resource-intensive tasks outside the request/response cycle.
It allows users to submit jobs via an API or dashboard, process them asynchronously with Celery workers, and monitor their progress in real time.

This project demonstrates key backend concepts:
- Database persistence with PostgreSQL & SQLAlchemy
- Asynchronous task processing using Celery & Redis
- Real-time monitoring through a clean dashboard UI
- Containerized, production-ready setup with Docker Compose and tests

### Features
- 📦 Submit jobs through a RESTful API or dashboard form
- ⚡ Process tasks asynchronously with Celery and Redis
- 🗄️ Persistent storage in PostgreSQL with SQLAlchemy ORM
- 📊 Real-time job status dashboard (Tailwind + Vanilla JS)
- 🐳 Containerized with Docker Compose (API, Worker, DB, Redis)
- 🧪 Pytest-based test suite with SQLite in-memory support
- 📝 Structured logging with optional JSON logs

### Tech Stack
- API framework: **FastAPI**
- Distributed task queue: **Celery**
- Message broker and result backend: **Redis**
- Relational database: **PostgreSQL**
- ORM: **SQLAlchemy**
- Frontend dashboard: **TailwindCSS + JS**
- Local orchestration: **Docker Compose**
- Testing: **Pytest**

### Project Structure
- src/
  - api/
    - core/
      - settings.py
      - database.py
      - celery_app.py
      - logging_config.py
    - models/
      - job.py
      - sql_models/
        - job.py
    - routers/
      - jobs.py
    - static/
      - js/
        - app.js
    - templates/
      - index.html
    - main.py
  - worker/
    - celery_worker.py
    - db_utils.py
- tests/
  - conftest.py
  - test_api.py
- docker-compose.yml
- Dockerfile
- requirements.txt
- README.md

### Getting Started
1. Clone the repository
   ```
   git clone https://github.com/your-username/async-job-queue-service.git
   cd async-job-queue-service
   ```
   
2. Configuration
   The project uses pydantic-settings for configuration. Default values are defined in src/api/core/settings.py.
   By default, the app will connect to:
   - postgresql://user:password@db:5432/jobs_db
   - redis://redis:6379/0
   You can override any of these by creating a .env file in the project root:
   ```
   DATABASE_URL=postgresql://your_user:your_pass@localhost:5432/your_db
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/1
   ```

3. Run with Docker Compose
   ```
   docker-compose up --build
   ```
   This starts:
   - FastAPI app (http://localhost:8000)
   - Celery worker
   - PostgreSQL database
   - Redis broker
   
4. Access the dashboard
   - Open your browser at:
   (http://localhost:8000/)

5. API Documentation
   - Interactive Swagger UI:
   (http://localhost:8000/docs)
   
### Development
1. Run test
   ```
   pytest
   ```
