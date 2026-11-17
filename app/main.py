from fastapi import Depends, FastAPI
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app.base62 import encode
from app.database import Base, engine, get_db
from app.models import Url

app = FastAPI(title="URL Shortener")

Base.metadata.create_all(bind=engine)


class BodyRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/shorten", status_code=201)
def shorten(body: BodyRequest, db: Session = Depends(get_db)):
    row = Url(long_url=str(body.url))
    db.add(row)
    db.flush()                      # runs the INSERT now, so the id exists
    code = encode(row.id)           # 125 -> "21"
    row.short_code = code
    db.commit()                     # saves everything for real

    return {"short_code": code, "short_url": f"http://localhost:8000/{code}"}