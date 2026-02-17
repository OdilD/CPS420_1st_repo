import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ─── App ────────────────────────────────────────────────────
app = FastAPI(title="FastAPI + SQLite MVP")

# ─── Database Setup ─────────────────────────────────────────
DATABASE = "app.db"


def get_db():
    """Get a database connection with row_factory set."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables on startup."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ─── Models (Pydantic) ──────────────────────────────────────
class ItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float


# ─── Startup Event ──────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()


# ─── Routes ─────────────────────────────────────────────────

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI + SQLite MVP"}


# CREATE
@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO items (name, description, price) VALUES (?, ?, ?)",
        (item.name, item.description, item.price),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, **item.model_dump()}


# READ ALL
@app.get("/items", response_model=list[ItemResponse])
def read_items():
    conn = get_db()
    rows = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    return [dict(row) for row in rows]


# READ ONE
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)


# UPDATE
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate):
    conn = get_db()
    cursor = conn.execute(
        "UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?",
        (item.name, item.description, item.price, item_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    conn.close()
    return {"id": item_id, **item.model_dump()}


# DELETE
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db()
    cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    conn.close()
    return {"detail": "Item deleted"}


# ─── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)