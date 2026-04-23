import sqlite3
from aiohttp import web
import json
from datetime import datetime

# Initialize and configure the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            lastModifiedBy TEXT,
            lastModifiedAt TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entryId INTEGER NOT NULL,
            modifiedBy TEXT NOT NULL,
            summary TEXT,
            content TEXT NOT NULL,
            modifiedAt TEXT NOT NULL,
            FOREIGN KEY(entryId) REFERENCES entries(id)
        )
    ''')
    conn.commit()
    conn.close()

async def list_entries(request):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT id, title FROM entries')
    entries = [{'id': row[0], 'title': row[1]} for row in c.fetchall()]
    conn.close()
    return web.json_response(entries)

async def create_entry(request):
    data = await request.json()
    title = data.get('title')
    content = data.get('content')
    createdBy = data.get('createdBy')
    
    if not title or not content or not createdBy:
        return web.json_response({'error': 'Missing required fields'}, status=400)

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('INSERT INTO entries (title, content, lastModifiedBy, lastModifiedAt) VALUES (?, ?, ?, ?)',
              (title, content, createdBy, datetime.utcnow().isoformat()))
    entry_id = c.lastrowid
    c.execute('INSERT INTO edits (entryId, modifiedBy, summary, content, modifiedAt) VALUES (?, ?, ?, ?, ?)',
              (entry_id, createdBy, 'Initial creation', content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return web.json_response({'id': entry_id, 'title': title, 'content': content}, status=201)

async def get_entry(request):
    entry_id = request.match_info.get('entryId')
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT id, title, content, lastModifiedBy, lastModifiedAt FROM entries WHERE id = ?', (entry_id,))
    entry = c.fetchone()
    conn.close()
    if entry:
        return web.json_response({
            'id': entry[0],
            'title': entry[1],
            'content': entry[2],
            'lastModifiedBy': entry[3],
            'lastModifiedAt': entry[4]
        })
    return web.json_response({'error': 'Entry not found'}, status=404)

async def update_entry(request):
    entry_id = request.match_info.get('entryId')
    data = await request.json()
    content = data.get('content')
    modifiedBy = data.get('modifiedBy')
    summary = data.get('summary')

    if not content or not modifiedBy or not summary:
        return web.json_response({'error': 'Missing required fields'}, status=400)

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT id FROM entries WHERE id = ?', (entry_id,))
    if not c.fetchone():
        conn.close()
        return web.json_response({'error': 'Entry not found'}, status=404)

    c.execute('UPDATE entries SET content = ?, lastModifiedBy = ?, lastModifiedAt = ? WHERE id = ?',
              (content, modifiedBy, datetime.utcnow().isoformat(), entry_id))
    c.execute('INSERT INTO edits (entryId, modifiedBy, summary, content, modifiedAt) VALUES (?, ?, ?, ?, ?)',
              (entry_id, modifiedBy, summary, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return web.json_response({'id': entry_id, 'content': content})

async def view_edits(request):
    entry_id = request.match_info.get('entryId')
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT modifiedBy, summary, content, modifiedAt FROM edits WHERE entryId = ?', (entry_id,))
    edits = [{'modifiedBy': row[0], 'summary': row[1], 'content': row[2], 'modifiedAt': row[3]} for row in c.fetchall()]
    conn.close()
    if edits:
        return web.json_response(edits)
    return web.json_response({'error': 'Entry not found'}, status=404)

app = web.Application()
app.add_routes([
    web.get('/entries', list_entries),
    web.post('/entries', create_entry),
    web.get('/entries/{entryId}', get_entry),
    web.put('/entries/{entryId}', update_entry),
    web.get('/entries/{entryId}/edits', view_edits),
])

if __name__ == '__main__':
    init_db()
    web.run_app(app, host='0.0.0.0', port=5000)