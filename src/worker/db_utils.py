from contextlib import contextmanager 
from sqlalchemy.orm import Session 
from src.api.core.database import SessionLocal 
from src.api.core.logging_config import get_logger 

logger = get_logger(__name__)

@contextmanager
def get_db_session():
    """ 
    Provides a database session inside a context manager. Ensures the session is committed if successful, or rolled back on error, and always closed at the end. 
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
        logger.debug("Database session committed successfully.")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error during DB session, rolled back: {e}")
        raise e
    finally: 
        db.close()
        logger.debug("Database session closed.")