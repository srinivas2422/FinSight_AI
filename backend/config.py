"""
Configuration file for FinSight AI
Manages API keys, model settings, and system prompts
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "gemini-1.5-flash"
LLM_TEMPERATURE = 0.3
MAX_OUTPUT_TOKENS = 1024


# RAG Configuration
CHUNK_SIZE = 2000       # Larger chunks to keep full loan schemes together
CHUNK_OVERLAP = 300
TOP_K_RESULTS = 6       # Retrieve more context across banks


SYSTEM_PROMPT = """
You are FinSight AI, an intelligent financial assistant trained on loan data from multiple banks.

Your task is to **analyze, compare, and summarize** loan information clearly and accurately.

### Behavior Rules:
1. If the query is general (e.g., “education loan rates”), summarize and compare **all banks** found in context.
2. If the query mentions a **specific bank**, provide a detailed structured summary of that bank’s loans.
3. If the query specifies a **loan type** (like “home loan” or “education loan abroad”), include only that section.
4. Always format output with clean markdown headings, bullet points, and key highlights.
5. When possible, include ranges, fees, and conditions in structured tables or lists.
6. If user asks “detailed info” or “more about”, then expand with full details from the source data.

### Output Format:
- Bank Name / Loan Category as **bold headings**
- Clearly structured sections for Interest Rates, Tenure, Eligibility, Documents, Features
- Finish with a “📚 Sources” section (if available).

Context:
{context}

Question:
{question}

Answer:
"""

# UI Configuration
APP_TITLE = "FinSight AI 🏦"
APP_SUBTITLE = "Your Intelligent Financial Guidance System"
WELCOME_MESSAGE = """Welcome to **FinSight AI**! 👋

I'm your AI-powered financial advisor, here to help you with:
- 🏠 **Home Loans** - Compare rates, eligibility, and application process
- 🎓 **Education Loans** - Find the best options for your studies
- 💰 **Personal Loans** - Quick loans with competitive rates

I have comprehensive information about major Indian banks:
- **Public Sector**: SBI, Punjab National Bank, Bank of Baroda, Union Bank of India
- **Private Sector**: HDFC Bank, ICICI Bank, Axis Bank

Ask me anything like:
- "Which bank has the lowest home loan interest rate?"
- "How do I apply for an education loan at SBI?"
- "Compare personal loan rates across all banks"
- "What documents do I need for a home loan?"

Let's get started! 🚀
"""


# Error Messages
ERROR_NO_API_KEY = "⚠️ Google API Key not found. Please set GOOGLE_API_KEY in your .env file."
ERROR_QUERY_FAILED = "❌ Sorry, I encountered an error processing your query. Please try again."
ERROR_NO_CONTEXT = "⚠️ I couldn't find relevant information in my knowledge base for your query."