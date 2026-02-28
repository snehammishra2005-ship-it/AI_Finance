# AI in Finance Assistant

This project provides an AI-powered assistant for financial analysis, featuring a conversational interface and document processing capabilities using a Small Language Model (SLM).

## Features

- **Conversational Interface**: Chat with an AI assistant powered by TinyLlama-1.1B. Supports different personas.
- **File Processing**: Upload PDF or text files for extraction and analysis.
- **Scoring Engine**: Analyze document content and generate a CSV report with scores and remarks.

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Frontend**: Streamlit
- **ML/AI**: Hugging Face Transformers, PyTorch, LangChain
- **Containerization**: Docker, Docker Compose

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized run)

## Setup & Installation

### Option 1: Local Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ai_finance
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The first run will download the SLM model (~600MB+).*

4.  **Run the Backend:**
    ```bash
    uvicorn backend.main:app --reload
    ```
    Backend will be available at `http://localhost:8000`.

5.  **Run the Frontend:**
    Open a new terminal, activate the environment, and run:
    ```bash
    streamlit run ui/app.py
    ```
    Frontend will be available at `http://localhost:8501`.

### Option 2: Docker Setup

1.  Build and run the containers:
    ```bash
    docker-compose up --build
    ```

2.  Access the application:
    - Frontend: `http://localhost:8501`
    - Backend API: `http://localhost:8000`

## Project Structure

- `backend/`: FastAPI application code.
    - `main.py`: Entry point.
    - `services/`: Logic for LLM, file processing, scoring.
- `ui/`: Streamlit frontend application.
- `docker-compose.yml`: Container orchestration config.
- `Dockerfile`: Image definition.
- `requirements.txt`: Python dependencies.

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive Swagger UI documentation.
