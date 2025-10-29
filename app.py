"""
FinSight AI - Intelligent Financial Guidance System
Enhanced ChatGPT-style Streamlit Interface
"""

import streamlit as st
from datetime import datetime
import config
from rag_pipeline import get_rag_pipeline


# -------------------- 1. SESSION STATE --------------------
def initialize_session_state():
    """Initialize Streamlit session state variables"""
    defaults = {
        "messages": [],
        "rag_initialized": False,
        "rag_pipeline": None,
        "pending_query": None,
        "show_examples": True
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# -------------------- 2. RAG INITIALIZATION --------------------
def initialize_rag():
    """Initialize RAG pipeline once"""
    if not st.session_state.rag_initialized:
        with st.spinner("🚀 Initializing FinSight AI... Please wait..."):
            rag = get_rag_pipeline()
            success = rag.initialize()
            if success:
                st.session_state.rag_pipeline = rag
                st.session_state.rag_initialized = True
                return True
            else:
                st.error(config.ERROR_NO_API_KEY)
                st.info("""
                💡 **Setup Guide:**
                1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Create a `.env` file in your project root
                3. Add: `GOOGLE_API_KEY=your_api_key_here`
                """)
                return False
    return True


# -------------------- 3. DISPLAY MESSAGE --------------------
def display_message(role: str, content: str, sources=None):
    """Render chat messages"""
    with st.chat_message(role):
        st.markdown(content)
        if sources:
            with st.expander("📚 View Sources"):
                for s in sources:
                    st.markdown(f"**Source {s['id']}:**")
                    st.text(s['content'])
                    st.divider()


# -------------------- 4. PROCESS QUERY --------------------
def process_query(query: str):
    """Handles query submission & RAG response"""
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    display_message("user", query)

    # Get RAG response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.rag_pipeline.query(query)
            answer = response["answer"]
            sources = response["sources"]
            st.markdown(answer)
            if sources:
                with st.expander("📚 View Sources", expanded=False):
                    for source in sources:
                        st.markdown(f"**Source {source['id']}:**")
                        st.text(source["content"])
                        st.divider()

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# -------------------- 5. MAIN APP --------------------
def main():
    st.set_page_config(page_title=config.APP_TITLE, layout="wide")

    initialize_session_state()

    # ---- Header ----
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="color:white;"> {config.APP_TITLE}</h1>
            <p style="font-size:16px; color:#475569;">{config.APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---- Sidebar ----
    with st.sidebar:
        st.header("ℹ️ About FinSight AI")
        st.markdown("""
        **FinSight AI** uses advanced **RAG (Retrieval-Augmented Generation)**  
        and **Google Gemini** to deliver accurate financial insights.

        **Capabilities**
        - 🔍 Smart document retrieval  
        - 💬 Context-aware responses  
        - 🏦 Multi-bank data coverage  
        - 📚 Transparent source citations
        """)
        st.divider()

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_examples = True
            st.rerun()

        st.divider()
        st.markdown("**⚙️ Tech Stack**")
        st.markdown("- LangChain\n- Google Gemini Pro\n- FAISS Vector DB\n- Streamlit")
        st.caption("© 2025 FinSight AI")

    # ---- RAG INIT ----
    if not initialize_rag():
        st.stop()

    # ---- Welcome Message ----
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            st.markdown(config.WELCOME_MESSAGE)

    # ---- Display Chat History ----
    for msg in st.session_state.messages:
        display_message(msg["role"], msg["content"], msg.get("sources"))

    # ---- Handle Pending Query ----
    if st.session_state.pending_query:
        process_query(st.session_state.pending_query)
        st.session_state.pending_query = None
        st.session_state.show_examples = False

    # ---- Chat Input ----
    if prompt := st.chat_input("💬 Ask me anything about loans, banks, or rates..."):
        st.session_state.show_examples = False
        process_query(prompt)

    # ---- Example Queries (Only visible before first query) ----
    if st.session_state.show_examples and len(st.session_state.messages) == 0:
        st.divider()
        st.markdown("### 💡 Try These Example Queries:")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎓 Best Education Loan Rates", use_container_width=True):
                st.session_state.pending_query = "Which bank has the lowest education loan interest rate?"
                st.session_state.show_examples = False
                st.rerun()
        with col2:
            if st.button("🏠 Home Loan Guide", use_container_width=True):
                st.session_state.pending_query = "How do I apply for an home loan at SBI?"
                st.session_state.show_examples = False
                st.rerun()
        with col3:
            if st.button("💰 Compare Personal Loans", use_container_width=True):
                st.session_state.pending_query = "Compare personal loan interest rates across all banks."
                st.session_state.show_examples = False
                st.rerun()


# -------------------- 6. RUN APP --------------------
if __name__ == "__main__":
    main()
