from fastapi import FastAPI
from .routers import jobs
from .core.database import Base, engine
from .models.sql_models import job


app = FastAPI(
    title="Job Queue Service",
    description="A service for handling asynchronous tasks"
)

# This startup event handler is the correct way to ensure the database
# tables are created only once when the application starts.
@app.on_event("startup")
async def startup_event():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Queue Service!"}

# Include the routers
app.include_router(jobs.router)