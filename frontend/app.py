"""
FinSight AI - Intelligent Financial Guidance System
Streamlit Frontend (Connected to FastAPI Backend)
"""

import streamlit as st
import requests
import sys, os

# --- Add backend path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend.config as config

# --- Backend URLs ---
BACKEND_URL = "http://127.0.0.1:8000/query"
HEALTH_URL = "http://127.0.0.1:8000/health"


# ----------------------------------------------------
# 1. SESSION STATE
# ----------------------------------------------------
def initialize_session_state():
    """Initialize Streamlit session variables"""
    defaults = {
        "messages": [],
        "pending_query": None,
        "show_examples": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ----------------------------------------------------
# 2. DISPLAY MESSAGE
# ----------------------------------------------------
def display_message(role, content, sources=None):
    """Render chat messages"""
    with st.chat_message(role):
        # Better styling for assistant replies
        if role == "assistant":
            st.markdown(
                f"<div style='color:white; padding:10px; border-radius:10px;'>{content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(content)

        # Display sources if any
        if sources:
            with st.expander("📚 View Sources", expanded=False):
                for s in sources:
                    st.markdown(f"**Source {s['id']}:**")
                    st.text(s["content"])
                    st.divider()


# ----------------------------------------------------
# 3. PROCESS QUERY
# ----------------------------------------------------
def process_query(query):
    """Send query to backend and show AI response"""
    st.session_state.messages.append({"role": "user", "content": query})
    display_message("user", query)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                res = requests.post(BACKEND_URL, json={"question": query}, timeout=60) # query will send main.py with /query endpoint
                if res.status_code != 200:
                    st.error("❌ Server error — check backend logs.")
                    return
                data = res.json()
                answer = data.get("answer", "No response received.")
                sources = data.get("sources", [])

                st.markdown(
                    f"<div style='color:white; padding:10px; border-radius:10px;'>{answer}</div>",
                    unsafe_allow_html=True,
                )

                if sources:
                    with st.expander("📚 View Sources", expanded=False):
                        for s in sources:
                            st.markdown(f"**Source {s['id']}:**")
                            st.text(s["content"])
                            st.divider()

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )

            except Exception as e:
                st.error(f"⚠️ Error communicating with backend: {e}")


# ----------------------------------------------------
# 4. MAIN APP
# ----------------------------------------------------
def main():
    st.set_page_config(page_title=config.APP_TITLE, layout="wide")

    initialize_session_state()

    # ---- Header ----
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="color:white;">{config.APP_TITLE}</h1>
            <p style="font-size:16px; color:#94a3b8;">{config.APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Sidebar ----
    with st.sidebar:
        st.header("ℹ️ About FinSight AI")
        st.markdown(
            """
            **FinSight AI** uses advanced **RAG (Retrieval-Augmented Generation)**  
            and **Google Gemini** to deliver accurate financial insights.

            **Capabilities**
            - 🔍 Smart document retrieval  
            - 💬 Context-aware responses  
            - 🏦 Multi-bank data coverage  
            - 📚 Transparent source citations
            """
        )
        st.divider()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_examples = True
            st.rerun()

        st.divider()
        st.markdown("**⚙️ Tech Stack**")
        st.markdown(
            "- Streamlit (Frontend)\n"
            "- FastAPI (Backend)\n"
            "- LangChain + FAISS (RAG)\n"
            "- Google Gemini Pro (LLM)"
        )
        st.caption("© 2025 FinSight AI")

    # ---- Backend Health Check ----
    try:
        res = requests.get(HEALTH_URL, timeout=10)
        if res.status_code != 200:
            st.error("⚠️ Backend not reachable. Start FastAPI server first.")
            st.stop()
    except Exception:
        st.error("🚨 Backend not running. Run: `uvicorn backend.main:app --reload`")
        st.stop()

    # ---- Welcome Message ----
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            st.markdown(config.WELCOME_MESSAGE)

    # ---- Chat History ----
    for msg in st.session_state.messages:
        display_message(msg["role"], msg["content"], msg.get("sources"))

    # ---- Handle Pending Example Query ----
    if st.session_state.get("pending_query"):
        process_query(st.session_state.pending_query)
        st.session_state.pending_query = None

    # ---- Chat Input ----
    if prompt := st.chat_input("💬 Ask me about loans, banks, or interest rates..."):
        st.session_state.show_examples = False
        process_query(prompt)

    # ---- Example Queries ----
    if st.session_state.show_examples and len(st.session_state.messages) == 0:
        st.divider()
        st.markdown("### 💡 Try example queries:")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎓 Education Loan Rates", use_container_width=True):
                st.session_state.pending_query = "Which bank has the lowest education loan interest rate?"
                st.session_state.show_examples = False
                st.rerun()

        with col2:
            if st.button("🏠 Home Loan Guide", use_container_width=True):
                st.session_state.pending_query = "Explain home loan options available at SBI."
                st.session_state.show_examples = False
                st.rerun()

        with col3:
            if st.button("💰 Personal Loan Comparison", use_container_width=True):
                st.session_state.pending_query = "Compare personal loan interest rates across Indian banks."
                st.session_state.show_examples = False
                st.rerun()


# ----------------------------------------------------
# 5. RUN STREAMLIT APP
# ----------------------------------------------------
if __name__ == "__main__":
    main()
