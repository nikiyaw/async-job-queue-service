from fastapi import FastAPI
from .routers import jobs
from .core.database import Base, engine
from .models.sql_models.job import Job


app = FastAPI(
    title="Job Queue Service",
    description="A service for handling asynchronous tasks"
)

# This line ensures the tables are created when the app starts
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Queue Service!"}

# Include the routers
app.include_router(jobs.router)