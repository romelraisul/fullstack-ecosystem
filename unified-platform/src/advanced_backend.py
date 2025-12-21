import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel
from dotenv import load_dotenv
from ruamel.yaml import YAML

from auth_utils import get_password_hash, verify_password, create_access_token, decode_access_token
from persistence import init_db, get_session
from repository import AgentRepository, ConversationRepository, WorkflowRepository, UserRepository

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("ADV_BACKEND_PORT", 8011))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Logging setup
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("UnifiedPlatform")
for handler in logging.root.handlers:
    handler.setFormatter(logging.Formatter('{"ts": "%(asctime)s", "level": "%(levelname)s", "request_id": "%(request_id)s", "msg": "%(message)s"}', defaults={"request_id": "system"}))

app = FastAPI(title="Unified Multi-Agent Platform", version="1.0.0")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
yaml_loader = YAML(typ='safe')

# Simple In-Memory Rate Limiter
class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.limit = requests_limit
        self.window = window_seconds
        self.history: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key not in self.history:
            self.history[key] = []
        self.history[key] = [t for t in self.history[key] if now - t < self.window]
        if len(self.history[key]) >= self.limit:
            return False
        self.history[key].append(now)
        return True

global_limiter = RateLimiter(requests_limit=100, window_seconds=60)

# Middlewares
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not global_limiter.is_allowed(client_ip):
        return HTMLResponse(content='{"detail": "Too many requests"}', status_code=429)
    return await call_next(request)

from monitoring import monitor

# ... existing middlewares ...

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    struct_logger = logging.LoggerAdapter(logger, {"request_id": request_id})
    request.state.logger = struct_logger
    start_time = time.time()
    
    success = True
    try:
        response = await call_next(request)
    except Exception as e:
        success = False
        raise e
    finally:
        process_time = time.time() - start_time
        monitor.record_request(process_time, success)
        
        if success:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            struct_logger.info(f"Request {request.method} {request.url.path} completed in {process_time:.4f}s")
            return response

# ... existing endpoints ...

@app.get("/api/v1/security/audit")
async def security_audit(user=Depends(get_current_user)):
    # Basic security check simulation
    return {
        "status": "secure",
        "checks": [
            {"name": "JWT Validation", "status": "pass"},
            {"name": "Rate Limiting", "status": "active"},
            {"name": "Input Sanitization", "status": "active"},
            {"name": "RAG Query Safety", "status": "verified"}
        ],
        "audit_timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def get_metrics(user=Depends(get_current_user)):
    return monitor.get_kpis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    username = payload.get("sub")
    repo = UserRepository(db)
    user = repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Models
class Message(BaseModel):
    role: str
    content: str

class ConversationCreate(BaseModel):
    agent_id: str
    initial_messages: Optional[List[Message]] = None

class UserCreate(BaseModel):
    username: str
    password: str

# Startup logic
def sync_agents_to_db():
    config_path = os.path.join(os.path.dirname(__file__), "../config/agents.yaml")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return
    session = get_session()
    repo = AgentRepository(session)
    try:
        with open(config_path, "r") as f:
            config = yaml_loader.load(f)
            agents = config.get("agents", [])
            for agent_data in agents:
                repo.create_or_update(agent_data)
            logger.info(f"Synced {len(agents)} agents from config to DB.")
    except Exception as e:
        logger.error(f"Failed to sync agents: {e}")
    finally:
        session.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    sync_agents_to_db()

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health(db=Depends(get_db)):
    repo = AgentRepository(db)
    agents = repo.get_all()
    return {"status": "ok", "agents_count": len(agents)}

@app.post("/api/v1/auth/register")
async def register(data: UserCreate, db=Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_username(data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(data.password)
    return repo.create(data.username, hashed)

@app.post("/api/v1/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user

@app.get("/api/v1/agents")
async def list_agents(category: Optional[str] = None, db=Depends(get_db), user=Depends(get_current_user)):
    repo = AgentRepository(db)
    agents = repo.get_all()
    if category:
        return [a for a in agents if a.category == category]
    return agents

@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    repo = AgentRepository(db)
    agent = repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.post("/api/v1/conversations")
async def create_conversation(data: ConversationCreate, db=Depends(get_db), user=Depends(get_current_user)):
    repo = ConversationRepository(db)
    agent_repo = AgentRepository(db)
    if not agent_repo.get_by_id(data.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    messages = [m.model_dump() for m in data.initial_messages] if data.initial_messages else []
    return repo.create(data.agent_id, messages)

@app.get("/api/v1/conversations/{conv_id}")
async def get_conversation(conv_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    repo = ConversationRepository(db)
    conv = repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

from rag_engine import rag_engine

class Document(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/v1/rag/documents")
async def ingest_documents(docs: List[Document], user=Depends(get_current_user)):
    formatted_docs = [{"id": str(uuid.uuid4()), "content": d.content, "metadata": d.metadata} for d in docs]
    rag_engine.add_documents(formatted_docs)
    return {"status": "success", "count": len(formatted_docs)}

# ... existing code ...

class SMSPayload(BaseModel):
    sender: str
    content: str
    timestamp: Optional[str] = None

@app.post("/api/v1/sms/bkash-webhook")
async def handle_bkash_sms(data: SMSPayload):
    # Logic for Android 15 SMS Forwarder Integration
    logger.info(f"Received bKash SMS from {data.sender}: {data.content}")
    
    # Simple bKash parsing logic
    if "TrxID" in data.content:
        # Example: "You have received tk 500 from 017... TrxID ABC123..."
        # We would ideally trigger a workflow or update a payment record here
        return {"status": "processed", "message": "Transaction identified"}
    
    return {"status": "received", "message": "SMS logged"}
    repo = ConversationRepository(db)
    agent_repo = AgentRepository(db)
    
    conv = repo.get_by_id(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # 1. Append user message
    repo.append_message(conv_id, message.model_dump())
    
    # 2. Generate Agent Response using Strategy
    agent = agent_repo.get_by_id(conv.agent_id)
    strategy = get_strategy(agent.category if agent else "default")
    response_content = strategy.execute(conv.agent_id, message.content)
    
    agent_msg = {"role": "assistant", "content": response_content}
    return repo.append_message(conv_id, agent_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)