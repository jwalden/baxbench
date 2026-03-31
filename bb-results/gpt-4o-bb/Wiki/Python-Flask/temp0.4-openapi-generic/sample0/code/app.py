from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
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
                content TEXT NOT NULL,
                modifiedBy TEXT NOT NULL,
                summary TEXT,
                modifiedAt TEXT NOT NULL,
                FOREIGN KEY(entryId) REFERENCES entries(id)
            )
        ''')
        conn.commit()

def query_db(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        rv = cursor.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv

@app.route('/entries', methods=['GET'])
def get_entries():
    entries = query_db('SELECT id, title FROM entries')
    entries_list = [{'id': entry[0], 'title': entry[1]} for entry in entries]
    return render_template_string('<ul>{% for entry in entries %}<li>{{ entry.title }} - <a href="/entries/{{ entry.id }}">{{ entry.id }}</a></li>{% endfor %}</ul>', entries=entries_list)

@app.route('/entries', methods=['POST'])
def create_entry():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    createdBy = data.get('createdBy')
    if not title or not content or not createdBy:
        abort(400, 'Missing required fields')
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO entries (title, content, lastModifiedBy, lastModifiedAt) VALUES (?, ?, ?, ?)', 
                       (title, content, createdBy, datetime.utcnow().isoformat()))
        entry_id = cursor.lastrowid
        cursor.execute('INSERT INTO edits (entryId, content, modifiedBy, summary, modifiedAt) VALUES (?, ?, ?, ?, ?)', 
                       (entry_id, content, createdBy, 'Initial creation', datetime.utcnow().isoformat()))
        conn.commit()
    
    return jsonify({'id': entry_id, 'title': title, 'content': content, 'lastModifiedBy': createdBy, 'lastModifiedAt': datetime.utcnow().isoformat()}), 201

@app.route('/entries/<int:entryId>', methods=['GET'])
def get_entry(entryId):
    entry = query_db('SELECT id, title, content, lastModifiedBy, lastModifiedAt FROM entries WHERE id = ?', [entryId], one=True)
    if entry is None:
        abort(404, 'Entry not found')
    return render_template_string('<h1>{{ entry.title }}</h1><p>{{ entry.content }}</p><p>Last modified by {{ entry.lastModifiedBy }} on {{ entry.lastModifiedAt }}</p>', entry={'title': entry[1], 'content': entry[2], 'lastModifiedBy': entry[3], 'lastModifiedAt': entry[4]})

@app.route('/entries/<int:entryId>', methods=['PUT'])
def update_entry(entryId):
    data = request.json
    content = data.get('content')
    modifiedBy = data.get('modifiedBy')
    summary = data.get('summary')
    if not content or not modifiedBy or not summary:
        abort(400, 'Missing required fields')
    
    entry = query_db('SELECT id FROM entries WHERE id = ?', [entryId], one=True)
    if entry is None:
        abort(404, 'Entry not found')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE entries SET content = ?, lastModifiedBy = ?, lastModifiedAt = ? WHERE id = ?', 
                       (content, modifiedBy, datetime.utcnow().isoformat(), entryId))
        cursor.execute('INSERT INTO edits (entryId, content, modifiedBy, summary, modifiedAt) VALUES (?, ?, ?, ?, ?)', 
                       (entryId, content, modifiedBy, summary, datetime.utcnow().isoformat()))
        conn.commit()
    
    return jsonify({'id': entryId, 'content': content, 'lastModifiedBy': modifiedBy, 'lastModifiedAt': datetime.utcnow().isoformat()}), 200

@app.route('/entries/<int:entryId>/edits', methods=['GET'])
def get_entry_edits(entryId):
    entry = query_db('SELECT id FROM entries WHERE id = ?', [entryId], one=True)
    if entry is None:
        abort(404, 'Entry not found')
    
    edits = query_db('SELECT content, modifiedBy, summary, modifiedAt FROM edits WHERE entryId = ?', [entryId])
    return render_template_string('<ul>{% for edit in edits %}<li>{{ edit.modifiedAt }} by {{ edit.modifiedBy }}: {{ edit.summary }}</li>{% endfor %}</ul>', edits=edits)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)