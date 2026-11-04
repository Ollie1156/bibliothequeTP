from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models import UserBook

app = FastAPI(title="Service Books")

app = FastAPI(title="Service Books")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Status = Literal["à lire", "en cours", "lu"]


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    status: Status = "à lire"


class StatusUpdate(BaseModel):
    status: Status


def book_to_dict(book: UserBook) -> dict:
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "status": book.status,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/books", status_code=201)
def add_book(
    data: BookCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    book = UserBook(
        user_id=user_id, title=data.title, author=data.author, status=data.status
    )
    db.add(book)
    db.commit()
    return book_to_dict(book)


@app.get("/books")
def list_books(
    status: Status | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = select(UserBook).where(UserBook.user_id == user_id)
    if status:
        query = query.where(UserBook.status == status)
    books = db.scalars(query.order_by(UserBook.id)).all()
    return [book_to_dict(b) for b in books]


@app.patch("/books/{book_id}/status")
def update_status(
    book_id: int,
    data: StatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    book = db.scalar(
        select(UserBook).where(UserBook.id == book_id, UserBook.user_id == user_id)
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    book.status = data.status
    db.commit()
    return book_to_dict(book)