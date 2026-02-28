# AI Finance Project Summary

## Overview
The application is a locally-hosted AI-powered financial assistant that allows users to chat with a Small Language Model (SLM) and process financial documents. The system follows a client-server architecture with a Streamlit frontend and a FastAPI backend.

## Architecture

### Backend (FastAPI)
The backend service (`backend/main.py`) acts as the core engine, exposing RESTful API endpoints:
- **`/chat`**: Processes incoming chat queries using an integrated SLM (`TinyLlama-1.1B`). Supports persona-based conversational models tailored for users like Students, Retirees, and General Users.
- **`/files`**: Handles document uploads (CSV, PDF, TXT, DOCX, PPTX), parsing the files to extract text content which is returned to the frontend.
- **`/analysis`**: Triggers a scoring engine to analyze extracted text using the SLM and generate a scored CSV report containing financial remarks.

### Frontend (Streamlit)
The frontend (`ui/app.py`) provides an interactive interface to interact with the backend services:
- **Chat Interface (`ui/chat.py`)**: A chat window to converse with the AI assistant. Includes a file upload component.
- **Sidebar (`ui/sidebar.py`)**: Allows users to select the SLM model, configure the assistant's persona, and manage conversational history (save/load previous chat sessions).
- **Document Processing (`ui/file_upload.py`)**: A dedicated widget to upload financial documents. It uploads the file to the backend, caches the extracted text, and offers a button to run the "SLM Analysis".
- **Analysis View**: Displays the results of the document analysis (scoring and remarks).

## Key Features Implemented
1. **Persona-driven AI Chat**: The assistant can adapt its tone and complexity based on predefined user personas.
2. **Chat History Management**: State persistence for chats, enabling users to switch between or resume older conversations.
3. **Multi-format Document Extraction**: Extract text from a variety of document formats.
4. **Document Analysis & Scoring**: Generating automated scores and remarks on uploaded financial text.

## Next Steps
To further improve the application, consider the following potential features:
- **Authentication & User Accounts**: Implement proper user logins to secure the endpoint and provide individualized chat histories.
- **Advanced RAG (Retrieval-Augmented Generation)**: Implement vector embeddings for document queries, allowing users to "chat" directly with their uploaded files instead of a generic backend scoring system.
- **Data Visualization**: Enhance the `Analysis` tab to render charts or graphs based on the generated CSV data.
- **Model Flexibility**: Allow dynamic loading/unloading of various HuggingFace models to compare results between different SLMs.
