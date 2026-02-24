import os
import json
import hashlib
from typing import Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_core.runnables import RunnablePassthrough

from . import config


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for multi-bank, multi-loan knowledge."""

    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.chain = None
        self.is_initialized = False
        self.cache_file = os.path.join(os.path.dirname(__file__), "../data/embedding_index.json")

    # ------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------
    def _file_hash(self, path: str) -> str:
        """Generate MD5 hash for detecting file changes."""
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self, data):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------
    def initialize(self) -> bool:
        try:
            if not config.GOOGLE_API_KEY:
                print("❌ GOOGLE_API_KEY missing.")
                return False

            print("🔹 Loading embeddings...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            data_dir = os.path.join(os.path.dirname(__file__), "../data")
            if not os.path.exists(data_dir):
                print("❌ Data directory missing.")
                return False

            old_cache = self._load_cache()
            new_cache, changed_files = {}, []

            # Detect modified or new files
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(".txt"):
                        path = os.path.join(root, file)
                        file_hash = self._file_hash(path)
                        rel_path = os.path.relpath(path, data_dir)

                        if rel_path not in old_cache or old_cache[rel_path]["hash"] != file_hash:
                            changed_files.append(path)

                        new_cache[rel_path] = {
                            "hash": file_hash,
                            "mtime": os.path.getmtime(path)
                        }

            # Create or update FAISS index
            if not changed_files and os.path.exists("faiss_index"):
                print("✅ Using existing FAISS index.")
                self.vectorstore = FAISS.load_local(
                    "faiss_index",
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                print(f"📄 Updating index with {len(changed_files)} changed files...")
                docs = []
                for path in changed_files:
                    docs.extend(TextLoader(path, encoding="utf-8").load())

                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=config.CHUNK_SIZE,
                    chunk_overlap=config.CHUNK_OVERLAP
                )
                chunks = splitter.split_documents(docs)

                if os.path.exists("faiss_index"):
                    existing = FAISS.load_local(
                        "faiss_index",
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    new_vs = FAISS.from_documents(chunks, self.embeddings)
                    existing.merge_from(new_vs)
                    self.vectorstore = existing
                else:
                    self.vectorstore = FAISS.from_documents(chunks, self.embeddings)

                self.vectorstore.save_local("faiss_index")
                self._save_cache(new_cache)
                print("✅ Index updated successfully.")

            # Load Google Gemini model
            print("🔹 Initializing Gemini model...")
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=config.LLM_TEMPERATURE,
                max_output_tokens=config.MAX_OUTPUT_TOKENS
            )

            # Prompt template
            prompt = PromptTemplate(
                template=config.SYSTEM_PROMPT,
                input_variables=["context", "question"]
            )

            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": config.TOP_K_RESULTS,
                    "fetch_k": config.TOP_K_RESULTS * 3  # widen initial pool
                }
            )

            # Build LCEL chain
            self.chain = (
                {
                    "context": retriever,
                    "question": RunnablePassthrough()
                }
                | prompt
                | llm
            )

            self.is_initialized = True
            print("✅ RAG pipeline initialized successfully.")
            return True

        except Exception as e:
            print(f"❌ Error initializing RAG: {e}")
            return False

    # ------------------------------------------------------------
    # Query Logic
    # ------------------------------------------------------------
    def query(self, question: str) -> Dict[str, Any]:
        if not self.is_initialized:
            return {"answer": "❌ Pipeline not initialized.", "sources": []}

        try:
            result = self.chain.invoke(question)

            # Retrieve source docs from FAISS
            docs = self.vectorstore.similarity_search(question, k=3)
            sources = [
                {"id": idx + 1, "content": doc.page_content[:400] + "..."}
                for idx, doc in enumerate(docs)
            ]

            return {"answer": result.content, "sources": sources}

        except Exception as e:
            return {"answer": f"Error: {e}", "sources": []}


# ------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
