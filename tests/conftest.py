import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import the necessary components from your application
# NOTE: You may need to adjust these import paths to match your project structure.
from src.api.main import app
from src.api.core.database import Base, get_db

# Create a test database engine that uses an in-memory SQLite database.
# StaticPool is used to ensure the same connection is used for the entire test session.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This fixture creates the database tables before each test and drops them afterwards.
@pytest.fixture(scope="function")
def db_session() -> Session:
    # Create all tables in the test database.
    Base.metadata.create_all(bind=engine)
    # Start a new database session for the test.
    db = TestingSessionLocal()
    try:
        # Yield the session to the test function.
        yield db
    finally:
        # Close the session and drop all tables to clean up.
        db.close()
        Base.metadata.drop_all(bind=engine)

# This fixture provides a FastAPI TestClient that uses our test database.
@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    # This dependency override function returns our test database session.
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the application's database dependency to use our test session.
    app.dependency_overrides[get_db] = override_get_db
    # Create the test client for making requests.
    with TestClient(app) as test_client:
        yield test_client
    # Clear the override after the test is finished.
    app.dependency_overrides.clear()
