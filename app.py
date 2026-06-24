"""
InsightForge Streamlit Frontend

User-facing web interface for the multi-agent Business Intelligence system.
Provides file upload, chat interface, and agent trace visualization.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from agents.runner import InsightForgeRunner
from security.guardrails import validate_input
from agents.memory import memory_bank


# Page configuration
st.set_page_config(
    page_title="InsightForge",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = "streamlit_user_001"
    if "uploaded_file_path" not in st.session_state:
        st.session_state.uploaded_file_path = None
    if "runner" not in st.session_state:
        st.session_state.runner = InsightForgeRunner(
            session_id=st.session_state.session_id
        )


def render_sidebar():
    """Render the sidebar with file upload and settings."""
    with st.sidebar:
        st.title("InsightForge")
        st.markdown("---")
        
        # File upload
        st.subheader("Data Upload")
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Supported formats: .csv, .xlsx, .xls"
        )
        
        if uploaded_file is not None:
            # Save uploaded file to disk
            file_path = os.path.join(project_root, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            st.session_state.uploaded_file_path = file_path
            memory_bank.set(st.session_state.session_id, "last_file", file_path)
            st.success(f"Uploaded: {uploaded_file.name}")
        
        st.markdown("---")
        
        # Session info
        st.subheader("Session Info")
        st.text(f"Session: {st.session_state.session_id}")
        if st.session_state.uploaded_file_path:
            st.text(f"File: {os.path.basename(st.session_state.uploaded_file_path)}")
        else:
            st.text("No file uploaded")
        
        # Memory display
        mem = memory_bank.get(st.session_state.session_id)
        if mem:
            st.markdown("---")
            st.subheader("Session Memory")
            for k, v in mem.items():
                st.text(f"{k}: {v}")
        
        st.markdown("---")
        
        # Clear chat
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.uploaded_file_path = None
            memory_bank.clear(st.session_state.session_id)
            st.rerun()


def render_chat():
    """Render the main chat interface."""
    st.header("Chat with InsightForge")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your data..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Security validation
        is_valid, validation_msg = validate_input(
            prompt,
            st.session_state.session_id
        )
        
        if not is_valid:
            # Show security block
            with st.chat_message("assistant"):
                st.error(f"SECURITY_BLOCKED: {validation_msg}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"SECURITY_BLOCKED: {validation_msg}"
            })
            return
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("InsightForge is analyzing..."):
                try:
                    # Recover file path from memory if session state lost it
                    file_path = st.session_state.uploaded_file_path
                    if not file_path:
                        mem = memory_bank.get(st.session_state.session_id)
                        file_path = mem.get("last_file")
                    
                    if file_path:
                        full_prompt = f"{prompt} (File: {file_path})"
                    else:
                        full_prompt = prompt
                    
                    # Run through the ADK multi-agent pipeline
                    response = st.session_state.runner.run(full_prompt)
                    
                    # Display response
                    st.markdown(response)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Persist interaction summary
                    memory_bank.set(
                        st.session_state.session_id,
                        "last_interaction",
                        {"prompt": prompt, "response": response[:200]}
                    )
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


def main():
    """Main application entry point."""
    initialize_session()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()