FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY services/portfolio-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/portfolio-service/app ./app
COPY shared /app/shared

# Expose port
EXPOSE 8016

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8016"]
