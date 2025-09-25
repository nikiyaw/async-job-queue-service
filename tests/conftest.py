import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.main import app
from src.api.core.database import Base, get_db
from src.api.models.sql_models.job import Job as JobModel
from fastapi.testclient import TestClient

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()

    # Dependency override to use the test database session
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Drop all tables after the test function has completed
    Base.metadata.drop_all(bind=engine)
