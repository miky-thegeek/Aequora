# Dockerfile for Aequora transaction importer

# Use official Python base image
FROM python:3.11-slim

# Set environment variable to allow insecure transport for OAuth2 (for local/private IPs)
ENV OAUTHLIB_INSECURE_TRANSPORT=1

# Set work directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and source
COPY requirements.txt .

# Create a virtual environment (optional) and install python packages
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port if needed
#EXPOSE ${APP_PORT:-8443}

# Default command
# Usiamo Gunicorn per eseguire l'app Flask in produzione
#CMD ["gunicorn", "--workers", "4", "--bind", "${APP_HOST}:${APP_PORT}", "--keyfile", "certs/server.key", "--certfile", "certs/server.crt", "app:app"]

CMD gunicorn --workers 4 --bind 0.0.0.0:${APP_PORT} --keyfile certs/server.key --certfile certs/server.crt app:app
