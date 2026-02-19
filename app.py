from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# ─── Database URL ───────────────────────────────────────────
DATABASE_URL = "sqlite:///./app.db"


# ─── SQLAlchemy Core Setup ──────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite + threads
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass

# ─── ORM Model (SQLAlchemy) ──────────────────────────────────
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, nullable=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    yield
    # Shutdown: (optional) place cleanup here
    print("Shutting down app")

# ─── App ────────────────────────────────────────────────────
app = FastAPI(
    title="FastAPI + SQLAlchemy MVP",
    lifespan=lifespan,
)

class ItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

