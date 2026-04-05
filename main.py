import os
import shutil
import tempfile
import traceback
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, Field
import re
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager

import models
import auth
from database import engine, get_db
from core_rag import ingest_pdf, setup_vector_store, get_retrieval_chain, invalidate_chain_cache

load_dotenv()
print("--- MAIN: Environment Loaded ---")

# --- LIFESPAN (STABLE STARTUP) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs once on startup
    print("--- SYSTEM INITIALIZING (LIFESPAN START) ---")
    try:
        models.Base.metadata.create_all(bind=engine)
        print("--- DATABASE SCHEMA VERIFIED ---")
    except Exception as e:
        print(f"!!! STARTUP DATABASE ERROR: {e}")
    yield
    # This runs once on shutdown
    print("--- SYSTEM SHUTTING DOWN ---")

app = FastAPI(title="DocuMind Enterprise SOP Assistant", lifespan=lifespan)

UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    os.path.join(tempfile.gettempdir(), "documind_uploads"),
)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "documind-enterprise-v2")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class QueryRequest(BaseModel):
    question: str
    chat_history: list[dict] = []  # List of {"role": "user/assistant", "content": "..."}

class BatchQueryRequest(BaseModel):
    questions: list[str] = Field(..., min_items=1, max_items=20)
    chat_history: list[dict] = []

class ShareChatRequest(BaseModel):
    question: str
    answer: str
    sources: str = ""
    document_name: str = "SOP"

class ShareSessionRequest(BaseModel):
    session_messages: list = []  # List of {role: 'user'|'assistant', content: str}
    document_name: str = "SOP"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str):
        if not re.match(r'^[a-zA-Z]+$', v):
            raise ValueError('Username must contain only letters (A-Z, a-z).')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str):
        if not re.search(r'[a-zA-Z]', v) or not re.search(r'[0-9]', v) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must include letters, numbers, and at least one special character (e.g., @, #, $).')
        return v

# -----------------
# AUTHENTICATION
# -----------------
@app.post("/signup")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# -----------------
# MAIN APP
# -----------------
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/shared/{share_id}")
async def view_shared_chat(share_id: str):
    """Serve shared chat view page"""
    return FileResponse("static/shared.html")

@app.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    filename = (file.filename or "upload.pdf").lower()
    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
    
    safe_name = os.path.basename(file.filename or "upload.pdf")
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{safe_name}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    namespace = f"user_{current_user.id}"
    
    try:
        documents = ingest_pdf(file_path)
        setup_vector_store(documents, INDEX_NAME, namespace=namespace)
        # Bust the chain cache so next query uses fresh vectorstore
        invalidate_chain_cache(INDEX_NAME, namespace=namespace)
        
        # Save document metadata to database
        doc = models.Document(
            user_id=current_user.id,
            filename=safe_name,
            original_filename=file.filename,
            file_size=file_size,
            namespace=namespace,
            status="active"
        )
        db.add(doc)
        db.commit()
        
        return {"status": "Success", "message": f"Document '{file.filename}' indexed successfully by {current_user.username}."}
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/documents")
async def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all documents for the current user"""
    docs = db.query(models.Document).filter(
        models.Document.user_id == current_user.id,
        models.Document.status == "active"
    ).order_by(models.Document.upload_date.desc()).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "upload_date": doc.upload_date,
            "file_size": doc.file_size,
            "namespace": doc.namespace
        }
        for doc in docs
    ]

@app.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a document and its vector embeddings"""
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Mark document as deleted in database
        doc.status = "deleted"
        db.commit()
        
        # TODO: Remove from Pinecone vector store
        # This would require Pinecone client integration
        
        return {"status": "Success", "message": f"Document '{doc.original_filename}' deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/query")
async def query_ai(request: QueryRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # Convert chat_history from dict to a formatted string for stable processing
        history_str = ""
        if request.chat_history:
            for msg in request.chat_history:
                role = "User" if msg.get("role") == "user" else "A"
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"
        
        if not history_str:
            history_str = "No previous history."

        rag_chain = get_retrieval_chain(INDEX_NAME, namespace=f"user_{current_user.id}")
        response = rag_chain.invoke({
            "input": request.question,
            "chat_history": history_str
        })
        
        # Determine the answer key (LangChain versions vary)
        answer = response.get("answer") or response.get("result") or response.get("text") or "No answer generated."

        # Extract Sources (if available in context documents)
        sources = []
        if "context" in response:
            for doc in response["context"]:
                page = doc.metadata.get("page", "N/A")
                source_name = os.path.basename(doc.metadata.get("source", "Unknown"))
                source_str = f"{source_name} (Page {page})"
                if source_str not in sources:
                    sources.append(source_str)

        # Save to Chat History
        chat_entry = models.ChatHistory(
            user_id=current_user.id,
            question=request.question,
            answer=answer
        )
        db.add(chat_entry)
        db.commit()

        return {
            "question": request.question,
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = str(e)
        print(f"Error in /query: {error_msg}")
        
        # User-friendly response for Quota limits
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "question": request.question,
                "answer": "I'm sorry, but the AI service is currently at its limit for free users. Please wait a few seconds and try again.",
                "sources": []
            }
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/batch-query")
async def batch_query_ai(request: BatchQueryRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Process multiple questions at once using conversational context"""
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        results = []
        
        # Convert history once for the batch
        langchain_history = []
        for msg in request.chat_history:
            if msg.get("role") == "user":
                langchain_history.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                langchain_history.append(AIMessage(content=msg.get("content")))

        rag_chain = get_retrieval_chain(INDEX_NAME, namespace=f"user_{current_user.id}")
        
        for question in request.questions:
            try:
                response = rag_chain.invoke({
                    "input": question,
                    "chat_history": langchain_history
                })
                answer = response.get("answer") or response.get("result") or response.get("text") or "No answer generated."
                
                # Extract Sources
                sources = []
                if "context" in response:
                    for doc in response["context"]:
                        page = doc.metadata.get("page", "N/A")
                        source_name = os.path.basename(doc.metadata.get("source", "Unknown"))
                        source_str = f"{source_name} (Page {page})"
                        if source_str not in sources:
                            sources.append(source_str)
                
                # Save to Database History
                chat_entry = models.ChatHistory(
                    user_id=current_user.id,
                    question=question,
                    answer=answer
                )
                db.add(chat_entry)
                
                results.append({
                    "question": question,
                    "answer": answer,
                    "sources": sources
                })
            except Exception as e:
                results.append({
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "sources": []
                })
        
        db.commit()
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = str(e)
        print(f"Error in /batch-query: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/history")
def get_user_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    chats = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).order_by(models.ChatHistory.timestamp.desc()).limit(20).all()
    # Return formatted for frontend (ascending order chronologically)
    return [
        {"question": c.question, "answer": c.answer, "timestamp": c.timestamp} 
        for c in reversed(chats)
    ]

@app.post("/share-chat")
async def share_chat(
    request: ShareChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a shareable link for a chat"""
    try:
        share_id = str(uuid.uuid4())[:8]
        
        shared = models.SharedChat(
            user_id=current_user.id,
            share_id=share_id,
            question=request.question,
            answer=request.answer,
            sources=request.sources,
            document_name=request.document_name
        )
        db.add(shared)
        db.commit()
        db.refresh(shared)
        
        return {
            "share_id": share_id,
            "share_url": f"/shared/{share_id}",
            "copy_text": f"Check out this answer from DocuMind:\n\n{request.question}\n\n{request.answer}"
        }
    except Exception as e:
        print(f"Share error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")

@app.get("/api/shared/{share_id}")
async def get_shared_chat_api(share_id: str, db: Session = Depends(get_db)):
    """Retrieve a shared chat (no auth required) - API endpoint"""
    try:
        shared = db.query(models.SharedChat).filter(models.SharedChat.share_id == share_id).first()
        if not shared:
            raise HTTPException(status_code=404, detail="Shared chat not found")
        
        return {
            "question": shared.question,
            "answer": shared.answer,
            "sources": shared.sources.split(",") if shared.sources else [],
            "document_name": shared.document_name,
            "created_by": shared.user.username,
            "created_at": shared.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Retrieve share error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve shared chat")

@app.post("/share-session")
async def share_session(
    request: ShareSessionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a shareable link for entire chat session"""
    try:
        import json
        share_id = str(uuid.uuid4())[:8]
        
        # Store session as JSON
        session_data = json.dumps({
            "messages": request.session_messages,
            "document_name": request.document_name,
            "created_by": current_user.username,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Use SharedChat table to store session (store entire JSON in "answer" field)
        shared = models.SharedChat(
            user_id=current_user.id,
            share_id=share_id,
            question=f"Session: {request.document_name}",
            answer=session_data,  # Store entire session JSON
            sources="",
            document_name=request.document_name
        )
        db.add(shared)
        db.commit()
        db.refresh(shared)
        
        return {
            "share_id": share_id,
            "share_url": f"/shared/{share_id}",
            "copy_text": f"Check out this DocuMind session on {request.document_name}!"
        }
    except Exception as e:
        print(f"Session share error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session share link")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

