import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# --- CRITICAL ENVIRONMENT VARIABLE FIXES ---
# Use an in-memory SQLite database for tests (shared across threads via StaticPool).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Prevent Celery trying to connect to real Redis during tests.
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"


# Import application AFTER environment variables are set.
from src.api.main import app
from src.api.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Use StaticPool so the same in-memory DB is accessible across threads used by TestClient.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Provide a transactional session for each test. Use a connection + transaction
    to isolate changes and then roll back after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create tables on this connection
    Base.metadata.create_all(bind=connection)
    db = TestingSessionLocal(bind=connection)
    
    try:
        yield db
    finally:
        transaction.rollback()
        Base.metadata.drop_all(bind=connection)
        db.close()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    Provide a TestClient that uses our db_session via dependency override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()