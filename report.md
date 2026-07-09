**Project Report: AI in Finance Assistant**

**Project Overview**
- Brief: An AI-powered assistant for financial analysis offering a conversational interface (chat), file upload and processing, and automated scoring/analysis that outputs CSV reports.

**1. File-by-file summary**
- `README.md`: Project overview, setup instructions, architecture summary, and run instructions.
- `requirements.txt`: Python dependencies required to run the app (Streamlit, FastAPI, Transformers, PyTorch, LangChain, PDF and docx parsers, etc.).
- `Dockerfile`: Container image definition to build the application environment.
- `docker-compose.yml`: Compose configuration to run backend and frontend containers together.
- `start_app.cmd`: Windows convenience script to start services (if present).
- `verify_backend.py`: Script to run basic checks against the backend (health endpoints, basic responses).
- `verify_llm.py`: Script to validate that the small language model (SLM) integration is functional.
- `verify_slm.py`: Additional SLM checks or environment validation for the LLM runtime.
- `test_persona.py`: Test or example to verify persona configurations and chat behavior.
- `test_upload.txt`: Sample upload used for testing file processing.

- `backend/__init__.py`: Package marker for backend module.
- `backend/main.py`: FastAPI application entrypoint. Handles lifespan events (loads SLM on startup), CORS, and defines endpoints: `/` (health), `/chat` (chat), `/files` (file upload & text extraction), `/analysis` (run scoring engine to produce CSV).

- `backend/services/__init__.py`: Package marker for services.
- `backend/services/api_providers.py`: Abstraction layer to interact with external APIs and third-party LLM providers (likely contains adapter logic for OpenAI, Anthropic, Google, etc.).
- `backend/services/file_processor.py`: Responsible for extracting text from uploaded files (PDF, DOCX, PPTX, plain text) using `pdfplumber`, `PyMuPDF`, or other libs.
- `backend/services/llm_service.py`: Wraps model loading and inference for the local SLM (TinyLlama) and/or remote models; exposes `llm_engine` used by `main.py`.
- `backend/services/scoring_engine.py`: Implements document scoring, uses LLM for remarks/interpretation, and invokes `utils/csv_generator.py` to produce CSV reports placed under `data/analysis_outputs/`.

- `config/__init__.py`: Package marker for config.
- `config/settings.py`: Application settings (APP_NAME, APP_VERSION, environment variables, paths).
- `config/slm_config.py`: Configuration for the Small Language Model (model name, local path, tokenizer and generation settings).

- `ui/__init__.py`: Package marker for the UI.
- `ui/app.py`: Streamlit entrypoint that configures the page, session state, and renders UI tabs: Chat, Analysis, Architecture. Adds project root to `sys.path` for imports.
- `ui/sidebar.py`: Streamlit sidebar rendering: model selection, persona selection, file upload controls and UI navigation.
- `ui/chat.py`: Chat view UI; handles user messages, displays conversation, and calls backend `/chat` endpoint.
- `ui/analysis_view.py`: Analysis tab UI to trigger file analysis and display results and CSV outputs.
- `ui/file_upload.py`: Helper UI for file uploads and previews (if present), handling `st.file_uploader` logic.
- `ui/architecture.py`: Visual or textual overview of system architecture shown in the App.

- `utils/__init__.py`: Package marker for utilities.
- `utils/csv_generator.py`: Utility to convert scoring results into CSV files and save them to `data/analysis_outputs/` with timestamped names.
- `utils/history_manager.py`: Manages chat history files under `data/history/` (save/load, pruning, metadata).
- `utils/persona_manager.py`: Manages persona definitions and templates used to prime the SLM for different conversational styles.

- `data/analysis_outputs/`: Directory containing generated CSV reports (example files found in the repository).
- `data/history/`: Directory storing chat history JSON files.
- `data/uploads/`: Directory for storing uploaded files (runtime).

**2. Project Architecture (brief)**
- Frontend: Streamlit app (`ui/app.py`) providing a web UI with tabs for Chat, Analysis, and Architecture.
- Backend: FastAPI (`backend/main.py`) exposing REST endpoints for chat, file upload, and analysis. The backend loads an SLM at startup and orchestrates services.
- Services: Modular services under `backend/services/` for LLM access, file parsing, scoring/analysis, and external API integrations.
- Persistence: File-based persistence for analysis outputs and chat history in `data/` directories; no dedicated DB observed in repository.
- Integration: The UI communicates with the backend via HTTP; the backend calls internal service modules and writes CSV outputs to `data/analysis_outputs/`.

**3. Tools & Technologies (brief)**
- Python 3.11: Primary language.
- FastAPI + Uvicorn: Backend framework and ASGI server.
- Streamlit: Frontend UI framework.
- Transformers, PyTorch, Accelerate: Model loading and inference for local SLMs.
- LangChain: (Used for prompt & chain management; present in `requirements.txt`.)
- PDF/Office parsers: `pdfplumber`, `PyMuPDF`, `python-docx`, `python-pptx` for file extraction.
- CSV and data libs: `pandas`, `numpy` for tabular outputs and processing.
- Dev & Ops: `Docker`, `docker-compose` for containerized runs.
- Optional cloud LLMs: `openai`, `google-generativeai`, `anthropic`, `groq` present in deps for external providers.

**4. Project Workflow (brief)**
- Local Setup: create venv, `pip install -r requirements.txt`, run backend and Streamlit frontend.

- Typical user flow:
  1. User opens the Streamlit UI (`ui/app.py`).
  2. User selects persona and SLM (or default) in the sidebar.
  3. User uploads a document via the Analysis tab (or drag-and-drop).
  4. Frontend POSTs the file to `/files` on the backend.
  5. `FileProcessor` extracts text and returns it to the UI.
  6. User triggers analysis; frontend calls `/analysis` with the extracted text.
  7. `ScoringEngine` analyzes the text, possibly calling `llm_service` to generate remarks, then `csv_generator` writes a timestamped CSV to `data/analysis_outputs/`.
  8. Results and CSV are shown in the UI; user can download the CSV.
  9. Chat: In the Chat tab the user sends messages; `llm_service`/`llm_engine` generates responses using the selected persona templates.
  10. Chat histories are persisted to `data/history/` by `history_manager`.

**Run & Verification**
- Quick commands (PowerShell):
```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
streamlit run ui/app.py
```
- Verification scripts:
```powershell
python verify_backend.py
python verify_llm.py
python verify_slm.py
python test_persona.py
```

**Notes & Recommendations**
- Model downloads and inference require significant disk and RAM; consider using a GPU or hosted LLM for better performance.
- If you plan to scale or run multiple users, add a persistent DB for history and job tracking instead of file-based storage.
- Consider adding a lightweight `report.md` or documentation index (this file) to the repo (already created).

---
Generated report by tooling on May 08, 2026.
