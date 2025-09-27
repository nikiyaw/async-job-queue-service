import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# --- CRITICAL ENVIRONMENT VARIABLE FIXES ---
# 1. Database Fix: Use an in-memory SQLite database for testing.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# 2. Celery/Redis Fix: Set broker and backend to use a mock location. 
# This prevents Kombu/Celery from trying to connect to a real Redis server 
# (which causes the 'Connection refused' error 10061).
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://" 


# --- Import Application Components ---
# NOTE: The imports below must come AFTER the environment variables are set.
from src.api.main import app
# Corrected import path based on the structure (src.api.core.database)
from src.api.core.database import Base, engine, get_db

# Create a test database engine that uses an in-memory SQLite database.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # This connect_args is necessary for SQLite to work with FastAPI's TestClient multithreading
    connect_args={"check_same_thread": False},
    # Removed StaticPool to resolve multithreading/cleanup errors
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- TRANSACTIONAL FIXTURE ---
@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Provides an isolated database session using a transaction that is rolled back
    after the test runs, ensuring a clean state for every test (Fixes 'no such table' errors).
    """
    # 1. Establish a single connection for the duration of the test
    connection = engine.connect()
    # 2. Begin a transaction. This keeps the in-memory database alive and tables visible.
    transaction = connection.begin()
    
    # 3. Create all tables on this specific connection.
    Base.metadata.create_all(bind=connection)
    
    # 4. Bind a session to this connection
    db = TestingSessionLocal(bind=connection)
    
    try:
        # Yield the session to the test function.
        yield db
    finally:
        # 5. Rollback the transaction. This quickly cleans up all data changes.
        transaction.rollback()
        # 6. Drop all tables created for this test (cleans up metadata from the connection)
        Base.metadata.drop_all(bind=connection)
        # 7. Close the session and the connection
        db.close()
        connection.close()


# This fixture provides a FastAPI TestClient that uses our test database.
@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    # This dependency override function returns our test database session.
    def override_get_db():
        try:
            yield db_session
        finally:
            # Session closure is handled by the db_session fixture's finally block
            pass

    # Override the application's database dependency to use our test session.
    app.dependency_overrides[get_db] = override_get_db
    # Create the test client for making requests.
    with TestClient(app) as test_client:
        yield test_client
    # Clear the override after the test is finished.
    app.dependency_overrides.clear()