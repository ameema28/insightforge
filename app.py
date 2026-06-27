"""
InsightForge Streamlit Frontend

User-facing web interface for the multi-agent Business Intelligence system.
Provides file upload, chat interface, agent trace visualization, and chat export.
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
from security.guardrails import validate_input, sanitize_output
from agents.memory import memory_bank


# Page configuration
st.set_page_config(
    page_title="InsightForge",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session() -> None:
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
    if "show_trace" not in st.session_state:
        st.session_state.show_trace = False


def render_sidebar() -> None:
    """Render the sidebar with file upload, API status, and settings."""
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

        # API Status
        st.subheader("API Status")
        groq_key = os.getenv("GROQ_API_KEY", "")
        groq_ok = bool(groq_key) and "your" not in groq_key.lower() and len(groq_key) >= 20
        google_ok = bool(os.getenv("GOOGLE_API_KEY"))

        if groq_ok:
            st.success("Groq: Ready")
        else:
            st.error("Groq: Missing/Invalid Key")

        if google_ok:
            st.success("Gemini: Ready")
        else:
            st.warning("Gemini: Missing Key")

        st.markdown("---")

        # Trace toggle
        st.subheader("Agent Trace")
        st.session_state.show_trace = st.toggle(
            "Show execution trace",
            value=st.session_state.show_trace,
            help="Visualize the multi-agent delegation chain"
        )

        st.markdown("---")

        # Export chat
        if st.session_state.messages:
            chat_md = "# InsightForge Chat Export\n\n"
            for msg in st.session_state.messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"]
                if content.startswith("data:image/png;base64,"):
                    content = "[Chart Image Generated]"
                chat_md += f"## {role}\n\n{content}\n\n"
            st.download_button(
                label="Export Chat",
                data=chat_md,
                file_name="insightforge_chat.md",
                mime="text/markdown"
            )
            st.markdown("---")

        # Clear chat
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.uploaded_file_path = None
            memory_bank.clear(st.session_state.session_id)
            st.rerun()


def display_message(content: str) -> None:
    """
    Display message content. If it contains a base64 image, render it.
    Otherwise display as markdown text.
    """
    if content.startswith("data:image/png;base64,"):
        img_data = content.split("data:image/png;base64,")[1]
        st.image(f"data:image/png;base64,{img_data}")
    else:
        st.markdown(content)


def render_trace() -> None:
    """Render the agent execution trace panel."""
    if not st.session_state.show_trace:
        return

    st.markdown("---")
    st.subheader("Agent Execution Trace")

    trace = st.session_state.runner.get_trace()
    if trace:
        st.code(trace, language=None)
    else:
        st.info("No trace available yet. Send a message to see the agent delegation chain.")


def render_chat() -> None:
    """Render the main chat interface."""
    st.header("Chat with InsightForge")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            display_message(message["content"])

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
                        if mem:
                            file_path = mem.get("last_file")

                    if file_path:
                        full_prompt = f"{prompt} (File: {file_path})"
                    else:
                        full_prompt = prompt

                    # Run through the multi-agent pipeline
                    response = st.session_state.runner.run(full_prompt)

                    # Sanitize output before displaying
                    sanitized_response, was_flagged = sanitize_output(response)

                    if was_flagged:
                        st.warning("Output contained potentially unsafe content and was sanitized.")

                    display_message(sanitized_response)

                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": sanitized_response
                    })

                    # Persist interaction summary
                    summary = (
                        "Chart generated"
                        if sanitized_response.startswith("data:image/png;base64,")
                        else sanitized_response[:200]
                    )
                    memory_bank.set(
                        st.session_state.session_id,
                        "last_interaction",
                        {"prompt": prompt, "response": summary}
                    )

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Render trace panel below chat
    render_trace()


def main() -> None:
    """Main application entry point."""
    initialize_session()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()