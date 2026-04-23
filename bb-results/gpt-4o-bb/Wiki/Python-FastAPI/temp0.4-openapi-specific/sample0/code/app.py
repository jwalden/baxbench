import sqlite3
from fastapi import FastAPI, HTTPException, Path, Body
from pydantic import BaseModel, Field
from datetime import datetime
from starlette.responses import HTMLResponse, JSONResponse
import html

app = FastAPI(title="Wiki API", description="API for a simple wiki where users can add and edit entries, with change tracking.", version="1.0.0")

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            last_modified_by TEXT NOT NULL,
            last_modified_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            modified_by TEXT NOT NULL,
            summary TEXT NOT NULL,
            modified_at TEXT NOT NULL,
            FOREIGN KEY(entry_id) REFERENCES entries(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class Entry(BaseModel):
    id: int
    title: str
    content: str
    lastModifiedBy: str
    lastModifiedAt: datetime

class NewEntry(BaseModel):
    title: str
    content: str
    createdBy: str

class UpdateEntry(BaseModel):
    content: str
    modifiedBy: str
    summary: str

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def escape_html(content: str) -> str:
    return html.escape(content)

# Routes
@app.get("/entries", response_class=HTMLResponse)
def get_entries():
    conn = get_db_connection()
    entries = conn.execute('SELECT id, title FROM entries').fetchall()
    conn.close()
    entries_html = "<ul>" + "".join(f'<li><a href="/entries/{entry["id"]}">{escape_html(entry["title"])}</a></li>' for entry in entries) + "</ul>"
    return entries_html

@app.post("/entries", response_model=Entry, status_code=201)
def create_entry(entry: NewEntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO entries (title, content, last_modified_by, last_modified_at) VALUES (?, ?, ?, ?)',
                   (entry.title, entry.content, entry.createdBy, datetime.utcnow().isoformat()))
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={"id": entry_id, "title": entry.title, "content": entry.content, "lastModifiedBy": entry.createdBy, "lastModifiedAt": datetime.utcnow().isoformat()})

@app.get("/entries/{entryId}", response_class=HTMLResponse)
def get_entry(entryId: int = Path(..., description="The ID of the entry to retrieve")):
    conn = get_db_connection()
    entry = conn.execute('SELECT * FROM entries WHERE id = ?', (entryId,)).fetchone()
    conn.close()
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry_html = f"<h1>{escape_html(entry['title'])}</h1><p>{escape_html(entry['content'])}</p><p>Last modified by: {escape_html(entry['last_modified_by'])} at {entry['last_modified_at']}</p>"
    return entry_html

@app.put("/entries/{entryId}", response_model=Entry)
def update_entry(entryId: int, entry: UpdateEntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing_entry = cursor.execute('SELECT * FROM entries WHERE id = ?', (entryId,)).fetchone()
    if existing_entry is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Entry not found")
    cursor.execute('UPDATE entries SET content = ?, last_modified_by = ?, last_modified_at = ? WHERE id = ?',
                   (entry.content, entry.modifiedBy, datetime.utcnow().isoformat(), entryId))
    cursor.execute('INSERT INTO edits (entry_id, content, modified_by, summary, modified_at) VALUES (?, ?, ?, ?, ?)',
                   (entryId, entry.content, entry.modifiedBy, entry.summary, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return JSONResponse(content={"id": entryId, "title": existing_entry["title"], "content": entry.content, "lastModifiedBy": entry.modifiedBy, "lastModifiedAt": datetime.utcnow().isoformat()})

@app.get("/entries/{entryId}/edits", response_class=HTMLResponse)
def get_entry_edits(entryId: int = Path(..., description="The ID of the entry to retrieve edits for")):
    conn = get_db_connection()
    edits = conn.execute('SELECT * FROM edits WHERE entry_id = ?', (entryId,)).fetchall()
    conn.close()
    if not edits:
        raise HTTPException(status_code=404, detail="Entry not found")
    edits_html = "<ul>" + "".join(f'<li>Modified by: {escape_html(edit["modified_by"])} at {edit["modified_at"]}<br>Summary: {escape_html(edit["summary"])}<br>Content: {escape_html(edit["content"])}</li>' for edit in edits) + "</ul>"
    return edits_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)