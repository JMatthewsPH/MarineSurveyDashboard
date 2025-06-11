# Lightweight Dockerfile for Marine Conservation Platform
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["streamlit", "run", "Home.py", "--server.port=5000", "--server.address=0.0.0.0", "--server.headless=true"]