FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY services/integration-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared /app/shared

# Copy application code
COPY services/integration-service/app ./app

# Set Python path
ENV PYTHONPATH=/app:/app/shared

# Expose port
EXPOSE 8019

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8019"]
