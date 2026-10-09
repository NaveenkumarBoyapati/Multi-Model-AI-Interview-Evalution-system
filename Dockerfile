# Dockerfile for AI Interview Evaluation System
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (FFmpeg for Whisper audio processing, curl, gnupg, and ODBC tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ffmpeg \
    unixodbc \
    unixodbc-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server (Debian 12 Bookworm)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure upload directory exists with full permissions for any user (Hugging Face non-root UID 1000)
RUN mkdir -p /app/backend/uploads && chmod -R 777 /app/backend/uploads

# Default port 7860 for Hugging Face Spaces, dynamically configurable via PORT env var
ENV PORT=7860
EXPOSE 7860 8000

# Set working directory to backend where main.py resides
WORKDIR /app/backend

# Run FastAPI backend with Uvicorn on dynamic port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
