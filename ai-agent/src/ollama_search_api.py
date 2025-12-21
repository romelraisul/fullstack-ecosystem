import os
import logging
import json
import numpy as np
import faiss
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
import ollama

# Configure Logging (JSON-like format for point 12/38)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("OllamaSearchAPI")

app = FastAPI(title="Ollama Semantic Search API")

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-for-local-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "hostamar-prod-2025":
        access_token = jwt.encode({"sub": form_data.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"
INDEX_PATH = "vector_index.faiss"
METADATA_PATH = "metadata.json"

# In-memory store for metadata (for point 47/89)
document_metadata = {}
index = None

def load_index():
    global index, document_metadata
    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r") as f:
            document_metadata = json.load(f)
        logger.info("Index and metadata loaded successfully.")
    else:
        # Initialize a new index if none exists (d=768 for nomic-embed-text)
        index = faiss.IndexFlatL2(768)
        logger.info("Initialized new FAISS index.")

@app.on_event("startup")
async def startup_event():
    load_index()

class SearchResult(BaseModel):
    document_id: str
    score: float
    metadata: dict

class SearchQuery(BaseModel):
    query: str
    k: int = 5
    temperature: float = 0.7

@app.post("/search", response_model=List[SearchResult])
async def search(query_data: SearchQuery, username: str = Depends(get_current_user)):
    try:
        logger.info(f"Query from {username}: {query_data.query}")
        
        # Generate embedding for the query
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query_data.query)
        query_embedding = np.array([response['embedding']]).astype('float32')
        
        # Search FAISS index
        D, I = index.search(query_embedding, query_data.k)
        
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx == -1: continue
            doc_id = list(document_metadata.keys())[idx]
            results.append(SearchResult(
                document_id=doc_id,
                score=float(dist),
                metadata=document_metadata[doc_id]
            ))
            
        return results
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Search Error")

@app.post("/index")
async def index_document(doc: dict, username: str = Depends(get_current_user)):
    """
    Expects doc matching document_indexing.schema.json
    """
    global index, document_metadata
    try:
        logger.info(f"Indexing request from {username}")
        doc_id = doc['document_id']
        content = doc['content']
        
        # Generate embedding
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=content)
        embedding = np.array([response['embedding']]).astype('float32')
        
        # Add to FAISS
        index.add(embedding)
        
        # Store metadata
        # idx is the current size of the index - 1
        pos = index.ntotal - 1
        document_metadata[doc_id] = doc['metadata']
        
        # Save persistence
        faiss.write_index(index, INDEX_PATH)
        with open(METADATA_PATH, "w") as f:
            json.dump(document_metadata, f)
            
        logger.info(f"Document {doc_id} indexed at position {pos}")
        return {"status": "success", "document_id": doc_id}
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)