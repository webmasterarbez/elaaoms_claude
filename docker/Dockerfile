FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Create data directories
RUN mkdir -p /app/data/payloads /app/data/logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
