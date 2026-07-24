
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

# Install dependencies.
#   --extra-index-url .../whl/cpu : pull the CPU-only torch build (~200MB
#       instead of the ~2.5GB CUDA wheel). The container has no GPU and torch
#       is only needed for CPU sentence-transformers embeddings.
#   --timeout/--retries : the ML wheels are large; be tolerant of slow or
#       flaky connections instead of failing the whole build.
#   cache mount : keep pip's download cache between builds so a retry doesn't
#       re-download gigabytes (replaces --no-cache-dir).
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      --timeout 120 \
      --retries 10 \
      -r requirements.txt

# Copy project code
COPY . .

# Expose ports (8000 for FastAPI, 8501 for Streamlit)
EXPOSE 8000
EXPOSE 8501

# Default command: run the FastAPI backend. docker-compose overrides this
# per service (backend runs uvicorn, frontend runs streamlit).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
