from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.base62 import encode
from app.database import Base, engine, get_db
from app.models import Url

from app.cache import get_cached_url, set_cached_url

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

@app.get("/{short_code}")
def redirect(short_code: str, db: Session = Depends(get_db)):

    long_url = get_cached_url(short_code)
    if long_url is not None:
        return RedirectResponse(url=long_url, status_code=302, headers={"X-Cache": "HIT"})

    long_url = db.scalar(select(Url.long_url).where(Url.short_code == short_code))
    if long_url is None:
        raise HTTPException(status_code=404, detail="Short link not found")

    set_cached_url(short_code, long_url)
    return RedirectResponse(url=long_url, status_code=302, headers={"X-Cache": "MISS"})