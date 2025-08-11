# # Use official Python runtime as the base image
# FROM python:3.12-slim

# # Set environment variables
# ENV FLASK_APP=run.py \
#     FLASK_ENV=production \
#     PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1

# # Set working directory
# WORKDIR /myapp

# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     gcc \
#     default-libmysqlclient-dev \
#     pkg-config \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Copy and install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application code
# COPY . .

# # Create a non-root user
# RUN adduser --disabled-password --gecos '' appuser && \
#     chown -R appuser:appuser /myapp
# USER appuser

# # Expose app port
# EXPOSE 5000

# # Command to run app
# CMD ["python", "run.py"]

# # Health check
# HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
#     CMD curl -f http://localhost:5000/ || exit 1

# ---------- Stage 1: Build ----------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install/packages --no-cache-dir -r requirements.txt


# ---------- Stage 2: Final ----------
FROM python:3.12-slim

# Set environment variables
ENV FLASK_APP=run.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /myapp

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install/packages /usr/local

# Copy application code
COPY . .

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /myapp

# USER appuser

# Expose application port
EXPOSE 443

ENV PYTHONPATH=/myapp

# Run the app
CMD ["python", "run.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:443/ || exit 1
