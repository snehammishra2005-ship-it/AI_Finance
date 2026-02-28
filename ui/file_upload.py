
import streamlit as st
import os
import requests
from config.settings import BACKEND_BASE_URL

def render_file_upload():
    """
    Renders the file upload component.
    Supported: CSV, PDF, TXT, DOCX, PPTX
    Uploads file to backend for text extraction.
    """

    uploaded_file = st.file_uploader(
        "Upload Financial File (PDF, DOCX, PPTX, CSV, TXT)",
        type=["csv", "pdf", "txt", "docx", "pptx"]
    )

    if uploaded_file is not None:
        # 1. Save locally (optional, but good for caching)
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.uploaded_file = {
            "name": uploaded_file.name,
            "path": file_path
        }
        
        # 2. Process with Backend (Text Extraction)
        # Avoid re-processing if already done
        if "current_file_name" not in st.session_state or st.session_state.current_file_name != uploaded_file.name:
            with st.spinner("Processing file..."):
                try:
                    files = {"file": (uploaded_file.name, open(file_path, "rb"), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_BASE_URL}/files", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.processed_text = data.get("full_text", "")
                        st.session_state.current_file_name = uploaded_file.name
                        st.success(f"File processed! Text length: {len(st.session_state.processed_text)} chars")
                    else:
                        st.error(f"Backend processing failed: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

        # 3. Trigger Analysis
        if st.button("Run SLM Analysis"):
            if "processed_text" in st.session_state and st.session_state.processed_text:
                with st.spinner("Running Analysis..."):
                    try:
                        payload = {
                            "filename": uploaded_file.name,
                            "text_content": st.session_state.processed_text,
                            "model_name": st.session_state.get("slm", "Phi-3 Mini")
                        }
                        res = requests.post(f"{BACKEND_BASE_URL}/analysis", json=payload)
                        
                        if res.status_code == 200:
                            st.success("Analysis Complete! check 'Analysis' tab.")
                        else:
                            st.error(f"Analysis failed: {res.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
            else:
                st.warning("No processed text found. Please upload a valid file.")
