# RemindGrid Dockerfile
# Same image is used for web, celery worker, and celery beat —
# only the command differs, set in docker-compose.yml per service.

FROM python:3.13-slim

# Prevents Python from buffering stdout/stderr - logs show up immediately
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# System dependencies needed to build psycopg2 and other C-extension packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (separate layer - only rebuilds
# when requirements.txt changes, not on every code change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Default command (overridden per-service in docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]