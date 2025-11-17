from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.rag_pipeline import get_rag_pipeline

app = FastAPI(title="FinSight AI Backend", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag = get_rag_pipeline()
initialized = rag.initialize()


@app.get("/health")
async def health():
    return {
        "status": "Backend running",
        "rag_initialized": initialized
    }


@app.post("/query")
async def query_endpoint(request: Request):
    try:
        data = await request.json()
        question = data.get("question")

        if not question:
            return {"error": "Missing 'question' field"}

        response = rag.query(question)
        return response

    except Exception as e:
        return {"error": f"Backend error: {str(e)}"}
