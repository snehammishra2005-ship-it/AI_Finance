# AI in Finance Assistant

An AI-powered assistant for financial analysis: a conversational chat interface with
persona support, document upload with RAG-based Q&A, web-augmented research, and an
automated document scoring engine.

## Features

- **Conversational Interface**: Chat with an AI assistant using a selectable persona
  (Student, General User, etc.). Backed by cloud LLM providers — no local model
  download required.
- **Per-user Accounts**: Register/login with a username and password; the backend
  issues a JWT and scopes each user's chat history and uploaded documents to their own
  account. See `backend/services/auth_service.py` and `ui/auth_view.py`.
- **Multiple LLM Providers**: Switch between Groq (GPT-OSS 20B, default), OpenRouter
  (GPT-5.5), Google (Gemini 3 Flash), Anthropic (Claude 3 Haiku), Cerebras (GPT-OSS
  120B), and Mistral (Mistral Small). A fallback router transparently retries another
  configured provider if the selected one fails. Configured in `config/slm_config.py`.
- **File Processing**: Upload PDF, DOCX, PPTX, XLSX/XLS, CSV, text, or image files
  (PNG/JPG/… via OCR) for text extraction.
- **RAG / Deep Research**: Uploaded documents are indexed per-session and can be
  queried directly ("Answer using my uploaded documents"). Grounded answers are also
  **persona-aware** — worded for the selected reader (Student, MBA, …) while a hard
  guardrail keeps every figure exact. Chat can also be augmented with live web search
  (via Tavily) for cited, up-to-date answers, and plain chat replies **stream** token by
  token.
- **Scoring Engine**: Analyze document content and generate a CSV report with
  verification, validation, explainability, and persona-fit scores.

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Frontend**: Streamlit
- **LLM Providers**: Groq, OpenRouter, Google Gemini, Anthropic, Cerebras, Mistral (via their APIs)
- **RAG**: LightRAG-based document indexing and retrieval
- **Web Search**: Tavily API (for Deep Research / web-augmented chat)
- **Containerization**: Docker, Docker Compose

## Prerequisites

- Python 3.11+
- API keys for the providers you plan to use (see `.env` below)
- Docker & Docker Compose (optional, for containerized run)

## Setup & Installation

### Option 1: Local Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API keys:**
    Copy `.env` (or create it) and fill in the keys you need:
    ```
    GROQ_API_KEY=...
    OPENROUTER_API_KEY=...
    GEMINI_API_KEY=...
    ANTHROPIC_API_KEY=...
    CEREBRAS_API_KEY=...
    MISTRAL_API_KEY=...
    TAVILY_API_KEY=...   # optional, enables web search in chat
    ```
    Only `GROQ_API_KEY` is required for the default model; the others are only needed
    if you select the corresponding provider in the UI.

4.  **Run the project:**
    ```bash
    streamlit run ui/app.py
    ```
    This one command starts everything — see [Running the project](#running-the-project)
    below for details.

### Option 2: Docker Setup

**Local development:**

1.  Build and run the containers:
    ```bash
    docker compose up --build
    ```

2.  Access the application at `http://localhost:8501`.
    - The backend is **not published to the host** — it's reachable only on the
      internal Docker network (by the frontend), so there's no open,
      unauthenticated API port. The frontend is bound to `127.0.0.1` only.

**Production (HTTPS):** a Caddy reverse proxy (the `production` profile) is the
only public entry point. It terminates TLS and forwards to the frontend
internally; the backend stays private.

```bash
DOMAIN=app.example.com docker compose --profile production up -d --build
```

- Set `DOMAIN` to your real domain (DNS pointing at the host, ports 80+443 open)
  and Caddy obtains and renews a **Let's Encrypt certificate automatically**.
- With `DOMAIN=localhost` (default) Caddy serves HTTPS with its own internal CA
  for local testing. Configure the proxy in [`Caddyfile`](./Caddyfile).

## Running the project

`ui/app.py` is the single entry point for the whole project. There's no separate
backend process to start by hand:

```bash
streamlit run ui/app.py
```

What it does:
- Starts the Streamlit frontend on `http://localhost:8501`.
- On first load, checks whether the FastAPI backend is reachable; if not, it launches
  `uvicorn backend.main:app` itself as a background process on `http://127.0.0.1:8000`
  and waits for it to respond before rendering the UI (shown as a "Starting backend
  service..." spinner).
- Reruns of the app (from user interaction) reuse the already-running backend instead
  of starting another one, and a lock file (`data/.backend.lock`) prevents two browser
  tabs/sessions from racing to start duplicate backend processes.
- Stopping the Streamlit process (e.g. Ctrl+C in its terminal) also stops the backend,
  since it runs as a child process in the same console.

This local auto-start only kicks in when the backend is expected on `localhost` (the
default). In the Docker Compose setup, the backend runs in its own container and the
frontend container is pointed at it via the `BACKEND_HOST` / `BACKEND_API_URL`
environment variables (see `docker-compose.yml`) — in that case `ui/app.py` just waits
for that container's backend to become reachable instead of starting a redundant one.

## Project Structure

- `backend/`: FastAPI application code.
    - `main.py`: Entry point and API routes (`/auth/*`, `/chat`, `/chat/stream`,
      `/files`, `/metrics`, `/rag/ask`, `/rag/reprocess`, `/analysis`).
    - `services/`: LLM provider routing, file processing, scoring, web research, and
      per-user authentication (`auth_service.py`).
    - `services/rag/`: Per-session RAG indexing and retrieval (LightRAG-based).
- `ui/`: Streamlit frontend application.
    - `app.py`: Entry point — renders the UI and also starts/health-checks the backend.
    - `auth_view.py`, `chat.py`, `file_upload.py`, `analysis_view.py`, `sidebar.py`: page components.
- `config/`: App settings and the list of available LLM models/providers.
- `docker-compose.yml`: Container orchestration config.
- `Dockerfile`: Image definition.
- `requirements.txt`: Python dependencies.

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive
Swagger UI documentation.
