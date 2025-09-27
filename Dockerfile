FROM python:3.10-slim-bullseye

# Set environment variable for Python and our source code path
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Create the working directory inside the container
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# Install dependencies FIRST to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire source code into the working directory
COPY src/ src/

# Expose the default Uvicorn/FastAPI port
EXPOSE 8000

# Default command to run the FastAPI application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]