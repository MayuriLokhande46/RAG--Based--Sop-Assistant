import os
import shutil
import tempfile
import traceback
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from core_rag import ingest_pdf, setup_vector_store
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DocuMind Enterprise SOP Assistant")

# Avoid writing uploads inside the repo when using `uvicorn --reload`:
# file changes inside the watched tree can trigger a reload mid-request,
# which looks like a client-side "connection error".
UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    os.path.join(tempfile.gettempdir(), "documind_uploads"),
)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise-v2")

class QueryRequest(BaseModel):
    question: str

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    
    
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    safe_name = os.path.basename(file.filename or "upload.pdf")
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{safe_name}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        
        documents = ingest_pdf(file_path)
        
        
        setup_vector_store(documents, INDEX_NAME)
        
        return {"status": "Success", "message": f"Document '{file.filename}' indexed successfully."}
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
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
        rag_chain = get_retrieval_chain(INDEX_NAME)
        
        # Invoke the chain
        response = rag_chain.invoke({"input": request.question})
        
        return {
            "question": request.question,
            "answer": response["answer"]
        }
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
