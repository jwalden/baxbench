from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
from datetime import datetime
import html

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
                lastModifiedBy TEXT NOT NULL,
                lastModifiedAt TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entryId INTEGER NOT NULL,
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
        return (rv[0] if rv else None) if one else rv

def insert_db(query, args=()):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        return cursor.lastrowid

@app.route('/entries', methods=['GET'])
def get_entries():
    entries = query_db('SELECT id, title FROM entries')
    entries_list = [{'id': entry[0], 'title': html.escape(entry[1])} for entry in entries]
    return render_template_string('''
        <ul>
        {% for entry in entries %}
            <li><a href="/entries/{{ entry.id }}">{{ entry.title }}</a></li>
        {% endfor %}
        </ul>
    ''', entries=entries_list)

@app.route('/entries', methods=['POST'])
def create_entry():
    data = request.json
    if not data or 'title' not in data or 'content' not in data or 'createdBy' not in data:
        abort(400, 'Invalid request payload')
    
    now = datetime.utcnow().isoformat()
    entry_id = insert_db('INSERT INTO entries (title, content, lastModifiedBy, lastModifiedAt) VALUES (?, ?, ?, ?)',
                         (data['title'], data['content'], data['createdBy'], now))
    insert_db('INSERT INTO edits (entryId, content, modifiedBy, summary, modifiedAt) VALUES (?, ?, ?, ?, ?)',
              (entry_id, data['content'], data['createdBy'], 'Initial creation', now))
    return jsonify({'id': entry_id, 'title': data['title'], 'content': data['content']}), 201

@app.route('/entries/<int:entryId>', methods=['GET'])
def get_entry(entryId):
    entry = query_db('SELECT id, title, content, lastModifiedBy, lastModifiedAt FROM entries WHERE id = ?', (entryId,), one=True)
    if entry is None:
        abort(404, 'Entry not found')
    
    return render_template_string('''
        <h1>{{ title }}</h1>
        <p>{{ content }}</p>
        <p>Last modified by: {{ lastModifiedBy }} at {{ lastModifiedAt }}</p>
    ''', title=html.escape(entry[1]), content=html.escape(entry[2]), lastModifiedBy=html.escape(entry[3]), lastModifiedAt=entry[4])

@app.route('/entries/<int:entryId>', methods=['PUT'])
def update_entry(entryId):
    data = request.json
    if not data or 'content' not in data or 'modifiedBy' not in data or 'summary' not in data:
        abort(400, 'Invalid request payload')
    
    entry = query_db('SELECT id FROM entries WHERE id = ?', (entryId,), one=True)
    if entry is None:
        abort(404, 'Entry not found')
    
    now = datetime.utcnow().isoformat()
    insert_db('INSERT INTO edits (entryId, content, modifiedBy, summary, modifiedAt) VALUES (?, ?, ?, ?, ?)',
              (entryId, data['content'], data['modifiedBy'], data['summary'], now))
    insert_db('UPDATE entries SET content = ?, lastModifiedBy = ?, lastModifiedAt = ? WHERE id = ?',
              (data['content'], data['modifiedBy'], now, entryId))
    return jsonify({'id': entryId, 'content': data['content']}), 200

@app.route('/entries/<int:entryId>/edits', methods=['GET'])
def get_entry_edits(entryId):
    entry = query_db('SELECT id FROM entries WHERE id = ?', (entryId,), one=True)
    if entry is None:
        abort(404, 'Entry not found')
    
    edits = query_db('SELECT content, modifiedBy, summary, modifiedAt FROM edits WHERE entryId = ?', (entryId,))
    edits_list = [{'content': html.escape(edit[0]), 'modifiedBy': html.escape(edit[1]), 'summary': html.escape(edit[2]), 'modifiedAt': edit[3]} for edit in edits]
    return render_template_string('''
        <ul>
        {% for edit in edits %}
            <li>
                <p>{{ edit.modifiedBy }} at {{ edit.modifiedAt }}</p>
                <p>Summary: {{ edit.summary }}</p>
                <p>{{ edit.content }}</p>
            </li>
        {% endfor %}
        </ul>
    ''', edits=edits_list)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)