import aiohttp
from aiohttp import web
import sqlite3
import json
import html
from datetime import datetime

# Initialize the database
conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Create tables
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
    content TEXT,
    modifiedAt TEXT,
    FOREIGN KEY(entryId) REFERENCES entries(id)
)
''')

conn.commit()


# Helper functions
def get_entries():
    c.execute('SELECT id, title FROM entries')
    return c.fetchall()

def get_entry(entry_id):
    c.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    return c.fetchone()

def create_entry(title, content, created_by):
    now = datetime.now().isoformat()
    c.execute('INSERT INTO entries (title, content, lastModifiedBy, lastModifiedAt) VALUES (?, ?, ?, ?)', 
              (title, content, created_by, now))
    conn.commit()
    return c.lastrowid

def update_entry(entry_id, content, modified_by, summary):
    now = datetime.now().isoformat()
    c.execute('UPDATE entries SET content = ?, lastModifiedBy = ?, lastModifiedAt = ? WHERE id = ?', 
              (content, modified_by, now, entry_id))
    c.execute('INSERT INTO edits (entryId, modifiedBy, summary, content, modifiedAt) VALUES (?, ?, ?, ?, ?)', 
              (entry_id, modified_by, summary, content, now))
    conn.commit()

def get_edits(entry_id):
    c.execute('SELECT modifiedBy, summary, content, modifiedAt FROM edits WHERE entryId = ?', (entry_id,))
    return c.fetchall()


# Handlers
async def list_entries(request):
    entries = get_entries()
    response = '<h1>Wiki Entries</h1><ul>'
    for entry in entries:
        response += f'<li><a href="/entries/{entry[0]}">{html.escape(entry[1])}</a></li>'
    response += '</ul>'
    return web.Response(text=response, content_type='text/html')

async def create_new_entry(request):
    try:
        data = await request.json()
        title = data['title']
        content = data['content']
        created_by = data['createdBy']
        entry_id = create_entry(title, content, created_by)
        return web.json_response({'id': entry_id, 'title': title, 'content': content, 'lastModifiedBy': created_by, 'lastModifiedAt': datetime.now().isoformat()}, status=201)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

async def get_entry_details(request):
    entry_id = request.match_info['entryId']
    entry = get_entry(entry_id)
    if entry:
        response = f'<h1>{html.escape(entry[1])}</h1><p>{html.escape(entry[2])}</p><p>Last modified by: {html.escape(entry[3])} at {entry[4]}</p>'
        return web.Response(text=response, content_type='text/html')
    else:
        return web.json_response({'error': 'Entry not found'}, status=404)

async def update_entry_details(request):
    entry_id = request.match_info['entryId']
    entry = get_entry(entry_id)
    if not entry:
        return web.json_response({'error': 'Entry not found'}, status=404)
    try:
        data = await request.json()
        content = data['content']
        modified_by = data['modifiedBy']
        summary = data['summary']
        update_entry(entry_id, content, modified_by, summary)
        return web.json_response({'id': entry_id, 'title': entry[1], 'content': content, 'lastModifiedBy': modified_by, 'lastModifiedAt': datetime.now().isoformat()})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)

async def get_entry_edits(request):
    entry_id = request.match_info['entryId']
    entry = get_entry(entry_id)
    if not entry:
        return web.json_response({'error': 'Entry not found'}, status=404)
    edits = get_edits(entry_id)
    response = f'<h1>Edits for {html.escape(entry[1])}</h1><ul>'
    for edit in edits:
        response += f'<li>Modified by: {html.escape(edit[0])} at {edit[3]} - Summary: {html.escape(edit[1])}</li>'
    response += '</ul>'
    return web.Response(text=response, content_type='text/html')


# Setup app and routes
app = web.Application()
app.router.add_get('/entries', list_entries)
app.router.add_post('/entries', create_new_entry)
app.router.add_get('/entries/{entryId}', get_entry_details)
app.router.add_put('/entries/{entryId}', update_entry_details)
app.router.add_get('/entries/{entryId}/edits', get_entry_edits)

# Run app
web.run_app(app, host='0.0.0.0', port=5000)