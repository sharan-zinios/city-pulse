FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
