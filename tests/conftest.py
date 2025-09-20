import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.core.database import Base, get_db
from src.api.main import app
from src.api.routers import jobs
# We need to import the Job model to ensure the Enum for its status
# is loaded by SQLAlchemy before we create the tables.
from src.api.models.sql_models.job import Job as JobModel

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# Use a custom database URL to match the project's logic
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This is the crucial fix: create the database tables before running the tests.
# The `jobs.py` router needs to be imported to ensure the models are loaded.
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Use the test client for the FastAPI application
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def teardown():
    # A fixture to ensure a clean database state for each test
    # This will be run automatically for every test function
    yield
    # We remove the table after each test to ensure tests are isolated
    Base.metadata.drop_all(bind=engine)
    # We then re-create the table to ensure the next test has a clean slate
    Base.metadata.create_all(bind=engine)