from fastapi import FastAPI
from .routers import jobs


app = FastAPI(
    title="Job Queue Service",
    description="A service for handling asynchronous tasks"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Queue Service!"}

# Include the routers
app.include_router(jobs.router)