# Dockerfile for Raindrop to Bluesky Bot
# Multi-stage build for efficient image size

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY raindrop_to_bluesky.py .
COPY src/ ./src/

# Create logs directory
RUN mkdir -p /app/logs

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set timezone (adjust as needed)
ENV TZ=America/New_York

# Create non-root user for running the Python script
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD test -f /app/logs/bluesky_raindrops.log || exit 1

# Note: Cron needs to run as root, but the Python script runs as appuser
# This is handled in entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
