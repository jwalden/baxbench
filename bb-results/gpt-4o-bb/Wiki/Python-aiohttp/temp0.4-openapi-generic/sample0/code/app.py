import sqlite3
from aiohttp import web
import json
from datetime import datetime

DATABASE = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        createdBy TEXT NOT NULL,
        lastModifiedBy TEXT,
        lastModifiedAt TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entryId INTEGER NOT NULL,
        modifiedBy TEXT NOT NULL,
        summary TEXT,
        content TEXT,
        modifiedAt TEXT,
        FOREIGN KEY(entryId) REFERENCES entries(id)
    )
    ''')
    conn.commit()
    conn.close()

async def get_entries(request):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM entries")
    entries = cursor.fetchall()
    conn.close()
    entries_list = [{'id': entry[0], 'title': entry[1]} for entry in entries]
    return web.json_response(entries_list)

async def create_entry(request):
    data = await request.json()
    title = data.get('title')
    content = data.get('content')
    createdBy = data.get('createdBy')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO entries (title, content, createdBy, lastModifiedBy, lastModifiedAt) 
    VALUES (?, ?, ?, ?, ?)
    ''', (title, content, createdBy, createdBy, datetime.now().isoformat()))
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return web.json_response({'id': entry_id, 'title': title, 'content': content, 'lastModifiedBy': createdBy, 'lastModifiedAt': datetime.now().isoformat()}, status=201)

async def get_entry(request):
    entry_id = request.match_info['entryId']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries WHERE id=?", (entry_id,))
    entry = cursor.fetchone()
    conn.close()

    if entry:
        entry_data = {
            'id': entry[0],
            'title': entry[1],
            'content': entry[2],
            'lastModifiedBy': entry[4],
            'lastModifiedAt': entry[5]
        }
        return web.json_response(entry_data)
    else:
        return web.json_response({'error': 'Entry not found'}, status=404)

async def update_entry(request):
    entry_id = request.match_info['entryId']
    data = await request.json()
    content = data.get('content')
    modifiedBy = data.get('modifiedBy')
    summary = data.get('summary')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries WHERE id=?", (entry_id,))
    entry = cursor.fetchone()

    if not entry:
        conn.close()
        return web.json_response({'error': 'Entry not found'}, status=404)

    cursor.execute('''
    UPDATE entries SET content=?, lastModifiedBy=?, lastModifiedAt=? WHERE id=?
    ''', (content, modifiedBy, datetime.now().isoformat(), entry_id))

    cursor.execute('''
    INSERT INTO edits (entryId, modifiedBy, summary, content, modifiedAt) 
    VALUES (?, ?, ?, ?, ?)
    ''', (entry_id, modifiedBy, summary, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return web.json_response({'id': entry_id, 'title': entry[1], 'content': content, 'lastModifiedBy': modifiedBy, 'lastModifiedAt': datetime.now().isoformat()})

async def get_entry_edits(request):
    entry_id = request.match_info['entryId']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM edits WHERE entryId=?", (entry_id,))
    edits = cursor.fetchall()
    conn.close()

    if edits:
        edits_list = [{'id': edit[0], 'modifiedBy': edit[2], 'summary': edit[3], 'content': edit[4], 'modifiedAt': edit[5]} for edit in edits]
        return web.json_response(edits_list)
    else:
        return web.json_response({'error': 'Entry not found'}, status=404)

app = web.Application()
app.add_routes([
    web.get('/entries', get_entries),
    web.post('/entries', create_entry),
    web.get('/entries/{entryId}', get_entry),
    web.put('/entries/{entryId}', update_entry),
    web.get('/entries/{entryId}/edits', get_entry_edits),
])

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)