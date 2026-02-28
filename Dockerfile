
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for building some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose ports (8000 for FastAPI, 8501 for Streamlit)
EXPOSE 8000
EXPOSE 8501

# Default command (will be overridden by docker-compose)
CMD ["python", "backend/main.py"]
