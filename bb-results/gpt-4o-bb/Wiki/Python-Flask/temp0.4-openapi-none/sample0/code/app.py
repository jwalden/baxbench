from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_by TEXT NOT NULL,
            last_modified_by TEXT,
            last_modified_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            modified_by TEXT NOT NULL,
            summary TEXT,
            modified_at TEXT,
            FOREIGN KEY(entry_id) REFERENCES entries(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/entries', methods=['GET'])
def get_entries():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT id, title FROM entries')
    entries = c.fetchall()
    conn.close()
    html = "<ul>" + "".join([f'<li><a href="/entries/{entry[0]}">{entry[1]}</a></li>' for entry in entries]) + "</ul>"
    return render_template_string(html)

@app.route('/entries', methods=['POST'])
def create_entry():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    created_by = data.get('createdBy')

    if not title or not content or not created_by:
        return jsonify({'error': 'Missing required fields'}), 400

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        INSERT INTO entries (title, content, created_by, last_modified_by, last_modified_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, created_by, created_by, datetime.now().isoformat()))
    entry_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'id': entry_id, 'title': title, 'content': content, 'lastModifiedBy': created_by, 'lastModifiedAt': datetime.now().isoformat()}), 201

@app.route('/entries/<entryId>', methods=['GET'])
def get_entry(entryId):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT * FROM entries WHERE id = ?', (entryId,))
    entry = c.fetchone()
    conn.close()

    if not entry:
        return abort(404)

    html = f"<h1>{entry[1]}</h1><p>{entry[2]}</p><p>Last modified by: {entry[4]} at {entry[5]}</p>"
    return render_template_string(html)

@app.route('/entries/<entryId>', methods=['PUT'])
def update_entry(entryId):
    data = request.json
    content = data.get('content')
    modified_by = data.get('modifiedBy')
    summary = data.get('summary')

    if not content or not modified_by or not summary:
        return jsonify({'error': 'Missing required fields'}), 400

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT * FROM entries WHERE id = ?', (entryId,))
    entry = c.fetchone()

    if not entry:
        conn.close()
        return abort(404)

    c.execute('''
        UPDATE entries
        SET content = ?, last_modified_by = ?, last_modified_at = ?
        WHERE id = ?
    ''', (content, modified_by, datetime.now().isoformat(), entryId))
    
    c.execute('''
        INSERT INTO edits (entry_id, content, modified_by, summary, modified_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (entryId, content, modified_by, summary, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return jsonify({'id': entryId, 'title': entry[1], 'content': content, 'lastModifiedBy': modified_by, 'lastModifiedAt': datetime.now().isoformat()}), 200

@app.route('/entries/<entryId>/edits', methods=['GET'])
def get_entry_edits(entryId):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('SELECT * FROM entries WHERE id = ?', (entryId,))
    entry = c.fetchone()

    if not entry:
        conn.close()
        return abort(404)

    c.execute('SELECT * FROM edits WHERE entry_id = ?', (entryId,))
    edits = c.fetchall()
    conn.close()

    html = "<h1>Edit History</h1><ul>" + "".join([f"<li>Modified by: {edit[3]} at {edit[5]}<br>Summary: {edit[4]}</li>" for edit in edits]) + "</ul>"
    return render_template_string(html)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)