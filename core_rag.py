import os
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

def ingest_pdf(file_path: str):
    
    Loads a PDF, chunks it, and returns the documents.
    Uses 'unstructured' for robust parsing.
    
    print(f"Loading document: {file_path}")
    loader = UnstructuredPDFLoader(file_path, mode="elements") # 'elements' gives us metadata like page numbers
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
    
    Initializes Pinecone and uploads documents.
    
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    

    if index_name not in pc.list_indexes().names():
        print(f"Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536, # OpenAI embedding dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    embeddings = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=index_name
    )
    print("Documents successfully indexed.")
    return vectorstore

from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ... (previous code remains same)

def get_retrieval_chain(index_name: str):
    """
    Creates a retrieval chain that answers questions based on the vector store.
    Includes safety guardrails and citation instructions.
    """
    embeddings = OpenAIEmbeddings()
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

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    
    # Retrieval logic
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

if __name__ == "__main__":
    pass
