from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .settings import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# SQLAlchemy database engine
engine = create_engine(settings.database_url, pool_pre_ping=True)
logger.info(f"Database engine initialized with URL: {settings.database_url}")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """ 
    Dependency for FastAPI routes. Provides a database session and ensures it is properly closed after use. 
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.exception(f"Error during DB session lifecycle: {e}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")