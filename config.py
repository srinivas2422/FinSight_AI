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
MAX_OUTPUT_TOKENS = 2048

# RAG Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 4

# System Prompt
SYSTEM_PROMPT = """You are FinSight AI, an expert financial advisor specializing in Indian banking and loan products. 

Your role is to provide accurate, helpful, and personalized guidance on:
- Home loans, education loans, gold loans, vehicle loans and personal loans
- Interest rates, eligibility criteria, and documents requirements
- Loan application processes and approval timelines
- Bank comparisons and recommendations

Guidelines:
1. Always base your answers on the provided context from the knowledge base
2. If information is not available in the context, clearly state that you don't have that specific information
3. Provide specific numbers (interest rates, loan amounts, tenure) when available
4. Compare banks when asked and highlight key differences
5. Be concise but comprehensive in your responses
6. Always mention the source bank(s) for the information provided
7. Use clear formatting with bullet points for better readability
8. If asked about application process, provide step-by-step guidance

Context from knowledge base:
{context}

User Question: {question}

Provide a detailed, accurate response based on the context above:"""

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