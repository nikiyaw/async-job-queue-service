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
- Submit jobs through a RESTful API or dashboard form
- Asynchronous job execution with Celery and Redis
- Persistent storage in PostgreSQL with SQLAlchemy ORM
- Real-time job status dashboard (Tailwind + JS)
- Containerized with Docker Compose (API, Worker, DB, Redis)
- Automated tests with Pytest (SQLite in-memory support)
- Structured logging with optional JSON logs

### Tech Stack
- API framework: FastAPI
- Distributed task queue: Celery
- Message broker and result backend: Redis
- Relational database: PostgreSQL
- ORM: SQLAlchemy
- Frontend dashboard: TailwindCSS + JS
- Local orchestration: Docker Compose
- Testing: Pytest

### Project Structure
src/
├── api/
│   ├── main.py               # FastAPI entrypoint
│   ├── routers/              # API routes
│   ├── models/               # SQLAlchemy models
│   ├── core/                 # Config (DB, logging, celery, redis, settings)
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS/JS assets
├── worker/
│   └── tasks.py              # Celery tasks
tests/                        # Pytest test suite
docker-compose.yml

### Getting Started
1. Clone the repository
   ```
   git clone https://github.com/your-username/async-job-queue-service.git
   cd async-job-queue-service
   ```
   
