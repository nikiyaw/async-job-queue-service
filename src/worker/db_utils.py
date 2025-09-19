from contextlib import contextmanager
from ..api.core.database import SessionLocal

@contextmanager
def get_db_session():
    """
    Provides a transactional scope around a series of operation.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally: 
        db.close()