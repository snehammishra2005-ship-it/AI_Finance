
import streamlit as st
import os
import requests
from config.settings import BACKEND_BASE_URL

def render_file_upload():
    """
    Renders the file upload component.
    Supported: PDF, DOCX, PPTX, XLSX/XLS, CSV, TXT
    Uploads file to backend for text extraction.
    """

    uploaded_file = st.file_uploader(
        "Upload Financial File (PDF, DOCX, PPTX, XLSX, CSV, TXT)",
        type=["pdf", "docx", "pptx", "xlsx", "xls", "csv", "txt"]
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
                    with open(file_path, "rb") as f:
                        files = {"file": (uploaded_file.name, f, uploaded_file.type)}
                        response = requests.post(
                            f"{BACKEND_BASE_URL}/files",
                            files=files,
                            data={"session_id": st.session_state.get("session_id", "default")},
                            timeout=120
                        )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.processed_text = data.get("full_text", "")
                        st.session_state.current_file_name = uploaded_file.name

                        extraction_warning = data.get("extraction_warning")
                        if extraction_warning:
                            # Very little text came out (e.g. a scanned/image PDF
                            # with no OCR available, or an empty file).
                            st.warning(extraction_warning)
                        elif data.get("rag_indexed", True):
                            st.success(f"File processed! Text length: {len(st.session_state.processed_text)} chars")
                        else:
                            st.warning(data.get("message", "RAG indexing failed for this document."))
                    else:
                        st.error(f"Backend processing failed: {response.text}")
                except requests.exceptions.Timeout:
                    st.error(
                        "⚠️ File processing timed out after 120s. The document "
                        "may be too large, or RAG indexing is stuck retrying "
                        "(e.g. hitting a provider rate limit). Try again shortly."
                    )
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Could not connect to backend. Make sure the FastAPI server is running.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

        # 3. Trigger Analysis
        if st.button("Run SLM Analysis"):
            if "processed_text" in st.session_state and st.session_state.processed_text:
                with st.spinner("Running Analysis..."):
                    try:
                        payload = {
                            "filename": uploaded_file.name,
                            "text_content": st.session_state.processed_text,
                            "model_name": st.session_state.get("slm", "Llama 3.1 8B Instant (Groq)")
                        }
                        res = requests.post(
                            f"{BACKEND_BASE_URL}/analysis",
                            json=payload,
                            timeout=120
                        )

                        if res.status_code == 200:
                            st.success("Analysis Complete! check 'Analysis' tab.")
                        else:
                            st.error(f"Analysis failed: {res.text}")
                    except requests.exceptions.Timeout:
                        st.error("⚠️ Analysis timed out after 120s. Try again, or pick a faster model.")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Could not connect to backend. Make sure the FastAPI server is running.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")
            else:
                st.warning("No processed text found. Please upload a valid file.")

    # 4. Retry any documents whose RAG indexing previously failed
    st.divider()
    if st.button("🔄 Retry failed document indexing"):
        with st.spinner("Retrying failed documents..."):
            try:
                res = requests.post(
                    f"{BACKEND_BASE_URL}/rag/reprocess",
                    json={"session_id": st.session_state.get("session_id", "default")},
                    timeout=120
                )

                if res.status_code == 200:
                    data = res.json()

                    if data["attempted"] == 0:
                        st.info("No failed documents to retry.")
                    elif data["fixed"] == data["attempted"]:
                        st.success(f"Fixed {data['fixed']} document(s) - they're now fully searchable.")
                    else:
                        st.warning(
                            f"Fixed {data['fixed']} of {data['attempted']} document(s). "
                            f"{data['still_failed']} still failing."
                        )
                else:
                    st.error(f"Retry failed: {res.text}")
            except requests.exceptions.Timeout:
                st.error("⚠️ Retry timed out after 120s.")
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Could not connect to backend. Make sure the FastAPI server is running.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
