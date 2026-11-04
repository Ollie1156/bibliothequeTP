from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserBook(Base):
    __tablename__ = "user_books"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="à lire")