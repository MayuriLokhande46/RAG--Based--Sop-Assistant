import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise-v2")
DEFAULT_GOOGLE_MODEL = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.0-flash")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _validate_config() -> None:
    google_api_key = _require_env("GOOGLE_API_KEY")
    pinecone_api_key = _require_env("PINECONE_API_KEY")

    if google_api_key == pinecone_api_key:
        raise ValueError(
            "GOOGLE_API_KEY and PINECONE_API_KEY must be different values. "
            "The current .env appears to reuse the same key for both services."
        )

def ingest_pdf(file_path: str):
    """
    Loads a PDF, chunks it, and returns the documents.
    Uses 'pypdf' for fast and lightweight parsing.
    """
    print(f"Loading document: {file_path}")
    loader = PyPDFLoader(file_path) 
    docs = loader.load()
    

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    
    final_docs = text_splitter.split_documents(docs)
    print(f"Split into {len(final_docs)} chunks.")
    return final_docs

def setup_vector_store(documents, index_name: str):
    """
    Initializes Pinecone and uploads documents.
    """
    _validate_config()
    pc = Pinecone(api_key=_require_env("PINECONE_API_KEY"))
    

    if index_name not in pc.list_indexes().names():
        print(f"Index {index_name} not found. Creating new index with dimension 384...")
        pc.create_index(
            name=index_name,
            dimension=384, # HuggingFace all-MiniLM-L6-v2 dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=index_name
    )
    print("Documents successfully indexed.")
    return vectorstore

def get_retrieval_chain(index_name: str = DEFAULT_INDEX_NAME):
    """
    Creates a retrieval chain that answers questions based on the vector store.
    Includes safety guardrails and citation instructions.
    """
    _validate_config()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    
    system_prompt = (
        "You are an expert Corporate SOP Assistant. "
        "Use the provided context to answer the user's question. "
        "If the answer is not in the context, strictly say: 'I am sorry, this information is not available in the corporate documents provided.' "
        "Do not invent any facts. "
        "Every claim must be cited with the Page Number if available in metadata. "
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    api_key = _require_env("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0
    )
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

if __name__ == "__main__":
    pass
