
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

# Default command: run the FastAPI backend. docker-compose overrides this
# per service (backend runs uvicorn, frontend runs streamlit).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
