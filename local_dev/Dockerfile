# City Pulse Local Simulator
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy local requirements and install Python dependencies
COPY local_dev/requirements.txt ./local_requirements.txt
RUN pip install --no-cache-dir -r local_requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port (if needed for health checks)
EXPOSE 8000

# Health check using Python directly
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/local_dev') else 1)" || exit 1

# Default command
CMD ["python", "local_dev/realtime_simulator.py"]
