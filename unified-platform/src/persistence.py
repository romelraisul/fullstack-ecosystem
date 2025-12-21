import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/unified_platform.db")

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # admin, user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ConversationModel(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    payload_json = Column(JSON) # Stores messages list
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class WorkflowModel(Base):
    __tablename__ = "workflows"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    spec_json = Column(JSON)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WorkflowExecutionModel(Base):
    __tablename__ = "workflow_executions"
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    state_json = Column(JSON)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

def init_db():
    # Ensure data directory exists
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if "/" in db_path:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_URL}")
