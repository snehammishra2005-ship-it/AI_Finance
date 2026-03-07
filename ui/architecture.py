import streamlit as st

def render_architecture_view():
    st.header("🏗️ Project Architecture")
    
    st.markdown("""
    ## Overview
    The application is a locally-hosted AI-powered financial assistant that allows users to chat with a Small Language Model (SLM) and process financial documents. The system follows a client-server architecture with a Streamlit frontend and a FastAPI backend.
    
    ---

    ## Component Breakdown
    
    ### 1. Frontend (Streamlit)
    The frontend provides an interactive interface to interact with the backend services:
    - **Chat Interface:** A dialog window to converse with the AI assistant. Includes a file upload component.
    - **Sidebar:** Allows users to select the SLM model, configure the assistant's persona, and manage conversational history.
    - **Document Processing:** A dedicated widget to upload financial documents (PDF, DOCX, PPTX, CSV, TXT).
    - **Analysis View:** Displays the results of the document analysis (scoring and remarks).
    
    ### 2. Backend (FastAPI)
    The backend service acts as the core engine, exposing RESTful API endpoints:
    - **`/chat`**: Processes incoming chat queries using an integrated SLM (`TinyLlama-1.1B`). Supports persona-based conversational models.
    - **`/files`**: Handles document uploads, parsing the files to extract text content which is returned to the frontend.
    - **`/analysis`**: Triggers a scoring engine to analyze extracted text using the SLM and generate a scored CSV report containing financial remarks.
    
    ### 3. Core AI Engine (`TinyLlama-1.1B`)
    Handles language generation for chat interactions and snippet analysis during document processing. It runs completely locally for privacy.
    
    ### 4. File Processing Engine
    Uses specialized libraries (`pdfplumber`, `python-docx`, `python-pptx`) to extract text from a variety of document formats before analysis.
    
    ---
    
    ## Workflow Example: File Upload & Analysis
    1. **Upload:** User uploads a file via the Streamlit frontend.
    2. **Transfer:** Streamlit sends the file to the FastAPI `/files` endpoint.
    3. **Extraction:** The backend `FileProcessor` extracts text from the document.
    4. **Analysis Request:** Streamlit triggers the `/analysis` endpoint with the extracted text.
    5. **Scoring:** The backend `ScoringEngine` asks the `LLMEngine` to summarize/evaluate the text, generates a series of validation scores, and saves a CSV report.
    """)
