# Backend Dockerfile for PDF Extraction HITL System
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-ind \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production WSGI server
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data experiments/results models uploads logs templates previews feedback

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=8071
ENV GUNICORN_WORKERS=1

# Expose port (will be overridden by docker-compose)
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8071} --timeout 240 --graceful-timeout 600 -w ${GUNICORN_WORKERS:-1} app:app"]
