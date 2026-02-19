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

@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI + SQLAlchemy MVP"}

from fastapi import Depends

@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
):
    db_item = Item(
        name=item.name,
        description=item.description,
        price=item.price,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)  # populate id from DB
    return db_item

@app.get("/items", response_model=list[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db),
):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db_item.name = item.name
    db_item.description = item.description
    db_item.price = item.price

    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"detail": "Item deleted"}

