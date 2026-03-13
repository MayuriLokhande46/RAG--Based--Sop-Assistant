import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from core_rag import ingest_pdf, setup_vector_store
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DocuMind Enterprise SOP Assistant")

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
async def root():
    return {"message": "Welcome to DocuMind Enterprise API"}

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        
        documents = ingest_pdf(file_path)
        
        
        index_name = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise")
        setup_vector_store(documents, index_name)
        
        return {"status": "Success", "message": f"Document '{file.filename}' indexed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
    
        if os.path.exists(file_path):
            os.remove(file_path)

from core_rag import ingest_pdf, setup_vector_store, get_retrieval_chain

@app.post("/query")
async def query_ai(request: QueryRequest):
    """
    Endpoint to ask questions based on indexed documents.
    """
    try:
        index_name = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise")
        rag_chain = get_retrieval_chain(index_name)
        
        # Invoke the chain
        response = rag_chain.invoke({"input": request.question})
        
        return {
            "question": request.question,
            "answer": response["answer"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
