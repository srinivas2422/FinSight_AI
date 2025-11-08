from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.rag_pipeline import get_rag_pipeline
import backend.config as config

app = FastAPI(title="FinSight AI Backend", version="1.0")

# Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag = get_rag_pipeline()
initialized = rag.initialize()


@app.get("/health")
async def health():
    """Health check endpoint"""
    if initialized:
        return {"status": "Backend running successfully"}
    else:
        return {"status": "RAG pipeline not initialized"}


@app.post("/query")
async def query_endpoint(request: Request):
    """Accept user question and return AI response"""
    try:
        data = await request.json()
        question = data.get("question")  # frontend sends 'question'
        if not question:
            return {"error": "No question provided"}

        # 🔹 LangChain expects the key 'query' internally — handled in rag.query()
        response = rag.query(question)
        return response

    except Exception as e:
        return {"error": f"Error processing query: {str(e)}"}
