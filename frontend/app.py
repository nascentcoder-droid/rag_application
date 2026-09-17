import os
import requests
import streamlit as st

# Application Configuration
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Layout and Metadata
st.set_page_config(
    page_title="Company Policy Assistant",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="expanded",
)


def check_backend_health(base_url: str) -> dict | None:
    """Checks the health and readiness of the FastAPI backend."""
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def query_policy_api(base_url: str, question: str) -> dict:
    """Sends a question to the FastAPI /api/chat endpoint."""
    endpoint = f"{base_url.rstrip('/')}/api/chat"
    payload = {"question": question}

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45,
        )
        if response.status_code == 200:
            return response.json()

        try:
            err_data = response.json()
            detail = err_data.get("detail", response.text)
        except Exception:
            detail = response.text

        return {"error": True, "status_code": response.status_code, "message": detail}

    except requests.exceptions.ConnectionError:
        return {
            "error": True,
            "status_code": 503,
            "message": (
                f"Could not connect to FastAPI backend at {base_url}. "
                "Ensure the backend server is running via `run.bat` or "
                "`uvicorn backend.main:app --reload --port 8000`."
            ),
        }
    except requests.exceptions.Timeout:
        return {
            "error": True,
            "status_code": 504,
            "message": "The request timed out while awaiting response from the backend service.",
        }
    except Exception as e:
        return {"error": True, "status_code": 500, "message": str(e)}


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings & Status")
    backend_url = st.text_input(
        "Backend URL",
        value=DEFAULT_BACKEND_URL,
        help="FastAPI server address",
    )

    # Health check indicator
    health_data = check_backend_health(backend_url)
    if health_data and health_data.get("status") == "healthy":
        st.success("🟢 Backend Connected", icon="✅")
        st.caption(f"Knowledge Base Files: {health_data.get('knowledge_base_files', 0)}")
        if health_data.get("vector_store_ready"):
            st.caption("Vector Store: Ready")
        else:
            st.warning("⚠️ Vector Store unindexed. Run `python scripts/ingest.py`")

        if not health_data.get("azure_configured"):
            st.info("ℹ️ Azure credentials missing in `.env`")
    else:
        st.error("🔴 Backend Offline", icon="⚠️")
        st.caption(f"Unable to reach `{backend_url}`")

    st.divider()

    st.subheader("💡 Example Questions")
    example_prompts = [
        "How many annual leave days do employees receive?",
        "What is the remote work policy and core working hours?",
        "What is the meal per diem rate for business travel?",
        "What are the password security requirements?",
        "How much 401(k) matching does the company provide?",
    ]

    selected_example = None
    for example in example_prompts:
        if st.button(example, use_container_width=True):
            selected_example = example

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- Main Chat UI ---
st.title("📋 Company Policy Assistant")
st.markdown("Ask a question about company policies, benefits, travel, and guidelines.")

# Initialize session chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📄 Sources", expanded=False):
                for src in message["sources"]:
                    doc_name = src.get("document", "Unknown")
                    page_num = src.get("page", "N/A")
                    st.markdown(f"- 📄 **{doc_name}** — Page {page_num}")

# Capture user input either from chat_input or clicked example
user_prompt = st.chat_input("Ask your question here...")
if selected_example and not user_prompt:
    user_prompt = selected_example

if user_prompt:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Query Backend API
    with st.chat_message("assistant"):
        with st.spinner("Searching policies and consulting Azure OpenAI..."):
            api_result = query_policy_api(backend_url, user_prompt)

        if api_result.get("error"):
            status_code = api_result.get("status_code", 500)
            err_msg = api_result.get("message", "An unexpected error occurred.")
            st.error(f"**Error ({status_code}):** {err_msg}")
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️ *Error ({status_code}):* {err_msg}",
                    "sources": [],
                }
            )
        else:
            answer = api_result.get("answer", "No answer was returned.")
            sources = api_result.get("sources", [])

            st.markdown(answer)

            if sources:
                with st.expander("📄 Sources", expanded=True):
                    for src in sources:
                        doc_name = src.get("document", "Unknown")
                        page_num = src.get("page", "N/A")
                        st.markdown(f"- 📄 **{doc_name}** — Page {page_num}")

            # Store in session state
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                }
            )
