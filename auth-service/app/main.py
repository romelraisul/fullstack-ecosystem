from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

# Import our modules
from . import models, auth

app = FastAPI(title="Hostamar Auth Service", version="1.0.0")

# --- Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    email: str
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class RefreshRequest(BaseModel):
    refresh_token: str

# --- Mock Database (In-Memory for Demo) ---
# In production, replace this with actual SQLAlchemy SessionLocal
fake_users_db = {} 

@app.post("/auth/signup", response_model=UserResponse)
def signup(user: UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    # Mocking DB save
    new_user = {"email": user.email, "hashed_password": hashed_password, "id": len(fake_users_db)+1, "is_active": True}
    fake_users_db[user.email] = new_user
    return new_user

@app.post("/auth/login", response_model=auth.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username) # OAuth2 form uses 'username' for email
    if not user or not auth.verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user['email']})
    refresh_token = auth.create_refresh_token(data={"sub": user['email']})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@app.post("/auth/refresh")
def refresh_token(request: RefreshRequest):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth.verify_token(request.refresh_token, credentials_exception)
    
    # Check if user still exists/is active
    if token_data.email not in fake_users_db:
        raise credentials_exception
        
    new_access_token = auth.create_access_token(data={"sub": token_data.email})
    return {"access_token": new_access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Hostamar Auth Service is Live"}
