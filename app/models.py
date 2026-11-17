from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Url(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    long_url: Mapped[str] = mapped_column(Text, nullable=False)
    short_code: Mapped[str | None] = mapped_column(String(10), unique=True, index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())