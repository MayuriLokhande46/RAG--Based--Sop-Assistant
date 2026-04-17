import os
import time
from typing import List, Optional
from dotenv import load_dotenv

# Document is a light metadata class, safe to import at top level
from langchain_core.documents import Document

load_dotenv()

print("--- CORE_RAG: Version 3.6 (Stable History) Initialized ---")

EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"
DEFAULT_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise-v2")
# Use GOOGLE_MODEL_NAME from .env
DEFAULT_GOOGLE_MODEL = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-flash")

# Global singletons to avoid re-loading on every request
_embeddings_cache = None
_chain_cache = {}  # Cache chains per namespace

def invalidate_chain_cache(index_name: Optional[str] = None, namespace: Optional[str] = None) -> None:
    """Invalidates the chain cache."""
    global _chain_cache
    if index_name and namespace:
        key = f"{index_name}:{namespace}"
        _chain_cache.pop(key, None)
        print(f"Chain cache invalidated for key: {key}")
    else:
        _chain_cache.clear()
        print("All chain caches cleared.")

def _get_embeddings():
    global _embeddings_cache
    if _embeddings_cache is None:
        print(f"Initializing Google Generative AI Embeddings ({EMBEDDING_MODEL_NAME})...")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        api_key = _require_env("GOOGLE_API_KEY")
        _embeddings_cache = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            google_api_key=api_key,
            output_dimensionality=768
        )
    return _embeddings_cache

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

def _validate_config() -> None:
    google_api_key = _require_env("GOOGLE_API_KEY")
    pinecone_api_key = _require_env("PINECONE_API_KEY")
    if google_api_key == pinecone_api_key:
        raise ValueError("GOOGLE_API_KEY and PINECONE_API_KEY must be different.")

def ingest_pdf(file_path: str) -> List[Document]:
    """Loads a file (PDF or TXT), chunks it, and returns the documents."""
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    print(f"Loading document: {file_path}")
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    elif file_path.lower().endswith(".txt"):
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
    else:
        raise ValueError("Unsupported file type")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    final_docs = text_splitter.split_documents(docs)
    for doc in final_docs:
        if "page" not in doc.metadata: doc.metadata["page"] = 1
    print(f"Split into {len(final_docs)} chunks.")
    return final_docs

def setup_vector_store(documents: List[Optional['Document']], index_name: str, namespace: Optional[str] = None):
    """Initializes Pinecone and uploads documents."""
    from pinecone import Pinecone, ServerlessSpec
    from langchain_pinecone import PineconeVectorStore
    _validate_config()
    pc = Pinecone(api_key=_require_env("PINECONE_API_KEY"))
    
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    
    vectorstore = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=_get_embeddings(),
        index_name=index_name,
        namespace=namespace
    )
    print("Documents successfully indexed.")
    return vectorstore

def get_retrieval_chain(index_name: str = DEFAULT_INDEX_NAME, namespace: Optional[str] = None):
    """Creates a cached retrieval chain with conversational history support."""
    global _chain_cache
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_pinecone import PineconeVectorStore
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    
    cache_key = f"{index_name}:{namespace}"
    if cache_key in _chain_cache:
        return _chain_cache[cache_key]

    _validate_config()
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=_get_embeddings(), namespace=namespace)
    google_api_key = _require_env("GOOGLE_API_KEY")
    
    # Typos handling for Gemini
    model_name = DEFAULT_GOOGLE_MODEL.strip()
    if model_name.startswith("models/"):
        model_name = model_name.replace("models/", "")
    
    # Check for Groq API Key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            from langchain_groq import ChatGroq
            print("--- LLM: Using Groq (Llama-3.3-70B) for High Speed ---")
            primary_llm = ChatGroq(
                model=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
                groq_api_key=groq_api_key,
                temperature=0,
                max_retries=5
            )
            # Gemini as solid fallback
            fallback_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key, temperature=0, max_retries=5)
            llm = primary_llm.with_fallbacks([fallback_llm])
        except Exception as e:
            print(f"!!! Groq Initialization Error, falling back to Gemini: {e}")
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key, temperature=0, max_retries=5)
    else:
        print("--- LLM: Using Google Gemini (Default) ---")
        primary_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=google_api_key, temperature=0, max_retries=5)
        fallback_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=google_api_key, temperature=0, max_retries=5)
        llm = primary_llm.with_fallbacks([fallback_llm])
    
    # Manual History Prompt (Compatible with all versions)
    system_prompt = (
        "You are an expert Corporate SOP Assistant. "
        "Use the provided context and history to answer the question. "
        "If context is missing, say it's not in the documents. "
        "\n\n"
        "CONVERSATION HISTORY:\n{chat_history}\n\n"
        "CONTEXT:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    _chain_cache[cache_key] = rag_chain
    return rag_chain

if __name__ == "__main__":
    pass
