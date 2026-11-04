import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="Service Auth")


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users/signup", status_code=201)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur existe déjà")

    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(username=data.username, hashed_password=hashed)
    db.add(user)
    db.commit()

    return {"id": user.id, "username": user.username}


@app.post("/users/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))

    if user is None or not bcrypt.checkpw(
        data.password.encode("utf-8"), user.hashed_password.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": str(user.id), "username": user.username, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {"access_token": token, "token_type": "bearer"}