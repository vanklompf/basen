FROM python:3.11-slim

# Build arguments for UID and GID
ARG UID=1000
ARG GID=1000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create group and user with specified GID and UID
RUN if ! getent group ${GID} >/dev/null 2>&1; then groupadd -g ${GID} appuser; fi && \
    if ! getent passwd ${UID} >/dev/null 2>&1; then useradd -u ${UID} -g ${GID} -m -s /bin/bash appuser; fi

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for database with proper permissions
RUN mkdir -p instance && \
    chown -R ${UID}:${GID} instance && \
    chmod 755 instance

# Change ownership of app directory
RUN chown -R ${UID}:${GID} /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["python", "app.py"]
