"""
Optimized RAG Pipeline with Incremental Embedding
Only processes new or modified documents to save time
"""

import os
import json
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
import config


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline with caching for embeddings.
    """

    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.qa_chain = None
        self.is_initialized = False
        self.cache_file = os.path.join(os.path.dirname(__file__), "data", "embedding_index.json")

    # ------------------------------------------------------------
    # 🔹 Helper Functions
    # ------------------------------------------------------------
    @staticmethod
    def _file_hash(path: str) -> str:
        """Compute MD5 hash of file content for change detection."""
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _load_cache(self) -> Dict[str, Dict]:
        """Load file hash & mtime cache."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self, data: Dict[str, Dict]):
        """Save updated file metadata cache."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------
    # 🔹 Initialization
    # ------------------------------------------------------------
    def initialize(self) -> bool:
        """Initialize pipeline & process only new/modified docs."""
        try:
            if not config.GOOGLE_API_KEY:
                print("❌ GOOGLE_API_KEY not found.")
                return False

            print("🔹 Loading embedding model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )

            data_dir = os.path.join(os.path.dirname(__file__), "data")
            if not os.path.exists(data_dir):
                print(f"❌ Data folder not found: {data_dir}")
                return False

            # Load existing metadata cache
            old_cache = self._load_cache()
            new_cache = {}
            changed_files = []

            # Identify new or modified files
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(".txt"):
                        path = os.path.join(root, file)
                        mtime = os.path.getmtime(path)
                        file_hash = self._file_hash(path)
                        rel_path = os.path.relpath(path, data_dir)

                        cached = old_cache.get(rel_path)
                        if not cached or cached["hash"] != file_hash:
                            changed_files.append(path)

                        # Update new cache entry
                        new_cache[rel_path] = {
                            "hash": file_hash,
                            "mtime": mtime,
                            "last_processed": datetime.now().isoformat()
                        }

            if not changed_files and os.path.exists("faiss_index"):
                print("✅ No new or modified documents detected — using existing FAISS index.")
                self.vectorstore = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
            else:
                print(f"📄 Found {len(changed_files)} new/modified files to process.")
                documents = []
                for path in changed_files:
                    print(f"🔹 Loading: {path}")
                    loader = TextLoader(path, encoding="utf-8")
                    documents.extend(loader.load())

                if not documents:
                    print("❌ No documents to process.")
                    return False

                print("🔹 Splitting documents into chunks...")
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=config.CHUNK_SIZE,
                    chunk_overlap=config.CHUNK_OVERLAP,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                chunks = splitter.split_documents(documents)
                print(f"✅ Created {len(chunks)} chunks")

                # Create / update FAISS index
                if os.path.exists("faiss_index"):
                    print("🔹 Loading existing FAISS index and merging...")
                    existing_vs = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
                    new_vs = FAISS.from_documents(chunks, self.embeddings)
                    existing_vs.merge_from(new_vs)
                    self.vectorstore = existing_vs
                else:
                    print("🔹 Creating new FAISS index...")
                    self.vectorstore = FAISS.from_documents(chunks, self.embeddings)

                self.vectorstore.save_local("faiss_index")
                self._save_cache(new_cache)
                print("✅ Cache and FAISS index updated successfully.")

            # Initialize Gemini LLM
            print("🔹 Initializing Gemini LLM...")
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=config.LLM_TEMPERATURE,
                max_output_tokens=config.MAX_OUTPUT_TOKENS
            )

            # Prompt + Chain
            prompt = PromptTemplate(template=config.SYSTEM_PROMPT, input_variables=["context", "question"])
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )

            self.is_initialized = True
            print("✅ RAG pipeline ready!")
            return True

        except Exception as e:
            print(f"❌ Error initializing RAG pipeline: {str(e)}")
            return False

    # ------------------------------------------------------------
    # 🔹 Query
    # ------------------------------------------------------------
    def query(self, question: str) -> Dict[str, Any]:
        if not self.is_initialized:
            return {"answer": "RAG not initialized.", "sources": []}
        try:
            response = self.qa_chain.invoke({"query": question})
            answer = response.get("result", "")
            sources = [{
                "id": i + 1,
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            } for i, doc in enumerate(response.get("source_documents", []))]
            return {"answer": answer, "sources": sources}
        except Exception as e:
            print(f"❌ Error during query: {e}")
            return {"answer": str(e), "sources": []}

    # ------------------------------------------------------------
    # 🔹 Similar Documents
    # ------------------------------------------------------------
    def get_similar_documents(self, query: str, k: int = 4) -> List[str]:
        if not self.is_initialized or not self.vectorstore:
            return []
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            print(f"❌ Similarity search error: {e}")
            return []


# ✅ Singleton
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
