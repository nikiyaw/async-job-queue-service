import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routers import jobs
from .core.database import Base, engine
from .core.logging_config import setup_logging, get_logger
from .models.sql_models import job

templates = Jinja2Templates(directory="src/api/templates")

# Setup global logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)
logger = get_logger(__name__)

app = FastAPI(
    title="Job Queue Service",
    description="A service for handling asynchronous tasks"
)

# --- NEW: Static File Mount ---
# This reserves the '/static' path for serving CSS, JS, images, etc.
# We map it to a directory named 'static' (which we will create soon)
app.mount("/static", StaticFiles(directory="src/api/static"), name="static")

# This startup event handler is the correct way to ensure the database
# tables are created only once when the application starts.
@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created or already exist.")

@app.get("/")
def serve_dashboard(request: Request):
    """
    This new root endpoint serves the main dashboard HTML page.
    It locates 'index.html' inside the 'templates' folder.
    """
    # os.path.dirname(__file__) gets the current directory (src/api)
    # Then we append 'templates/index.html'
    return templates.TemplateResponse("index.html", {"request": request})


# Include the routers
app.include_router(jobs.router)