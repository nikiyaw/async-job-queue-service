from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@db:5432/jobs_db"

    # Celery/Redis
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Redis (if you use it directly, not just as broker)
    redis_url: str = "redis://redis:6379/0"

    class Config: 
        env_file = ".env" # optional, supports overrides
        env_file_encoding = 'utf-8'

# Singleton settings instance
settings = Settings()

if __name__ == "__main__":
    print("Database URL:", settings.database_url)
    print("Redis URL:", settings.redis_url)
    print("Celery Broker URL:", settings.celery_broker_url)