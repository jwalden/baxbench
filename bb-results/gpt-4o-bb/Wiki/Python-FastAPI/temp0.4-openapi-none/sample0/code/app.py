import sqlite3
from fastapi import FastAPI, HTTPException, Path, Request
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
import uvicorn

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
        lastModifiedBy TEXT,
        lastModifiedAt TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entryId INTEGER,
        content TEXT,
        modifiedBy TEXT,
        summary TEXT,
        modifiedAt TEXT,
        FOREIGN KEY(entryId) REFERENCES entries(id)
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class Entry(BaseModel):
    id: str
    title: str
    content: str
    lastModifiedBy: str
    lastModifiedAt: str

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

# Routes
@app.get("/entries", response_class=HTMLResponse)
async def get_entries():
    conn = get_db_connection()
    entries = conn.execute('SELECT id, title FROM entries').fetchall()
    conn.close()
    html_content = "<ul>"
    for entry in entries:
        html_content += f'<li><a href="/entries/{entry["id"]}">{entry["title"]}</a></li>'
    html_content += "</ul>"
    return html_content

@app.post("/entries", response_model=Entry, status_code=201)
async def create_entry(new_entry: NewEntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO entries (title, content, lastModifiedBy, lastModifiedAt)
    VALUES (?, ?, ?, ?)
    ''', (new_entry.title, new_entry.content, new_entry.createdBy, datetime.now().isoformat()))
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return Entry(id=str(entry_id), title=new_entry.title, content=new_entry.content, lastModifiedBy=new_entry.createdBy, lastModifiedAt=datetime.now().isoformat())

@app.get("/entries/{entryId}", response_class=HTMLResponse)
async def get_entry(entryId: str = Path(..., description="The ID of the entry to retrieve")):
    conn = get_db_connection()
    entry = conn.execute('SELECT * FROM entries WHERE id = ?', (entryId,)).fetchone()
    conn.close()
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    html_content = f"<h1>{entry['title']}</h1><p>{entry['content']}</p><p>Last modified by {entry['lastModifiedBy']} at {entry['lastModifiedAt']}</p>"
    return html_content

@app.put("/entries/{entryId}", response_model=Entry)
async def update_entry(entryId: str, update_entry: UpdateEntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    entry = cursor.execute('SELECT * FROM entries WHERE id = ?', (entryId,)).fetchone()
    if entry is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Entry not found")
    
    cursor.execute('''
    UPDATE entries SET content = ?, lastModifiedBy = ?, lastModifiedAt = ?
    WHERE id = ?
    ''', (update_entry.content, update_entry.modifiedBy, datetime.now().isoformat(), entryId))
    
    cursor.execute('''
    INSERT INTO edits (entryId, content, modifiedBy, summary, modifiedAt)
    VALUES (?, ?, ?, ?, ?)
    ''', (entryId, update_entry.content, update_entry.modifiedBy, update_entry.summary, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return Entry(id=str(entryId), title=entry['title'], content=update_entry.content, lastModifiedBy=update_entry.modifiedBy, lastModifiedAt=datetime.now().isoformat())

@app.get("/entries/{entryId}/edits", response_class=HTMLResponse)
async def get_entry_edits(entryId: str = Path(..., description="The ID of the entry to retrieve edit history for")):
    conn = get_db_connection()
    edits = conn.execute('SELECT * FROM edits WHERE entryId = ?', (entryId,)).fetchall()
    conn.close()
    if not edits:
        raise HTTPException(status_code=404, detail="Entry not found")
    html_content = "<ul>"
    for edit in edits:
        html_content += f'<li>{edit["modifiedAt"]} by {edit["modifiedBy"]}: {edit["summary"]}</li>'
    html_content += "</ul>"
    return html_content

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)