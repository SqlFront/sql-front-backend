# Build stage
FROM --platform=linux/amd64 python:3.11-alpine AS builder

# Install build dependencies
RUN apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    linux-headers

RUN mkdir /app

WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM --platform=linux/amd64 python:3.11-alpine

# Install runtime dependencies
RUN apk update && \
    apk add --no-cache \
    libpq \
    tzdata

# Create non-root user
RUN adduser -D appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Switch to non-root user
USER appuser

# Health check (adjust the port if needed)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/health || exit 1

# Run the application
CMD ["python3", "main.py"]
