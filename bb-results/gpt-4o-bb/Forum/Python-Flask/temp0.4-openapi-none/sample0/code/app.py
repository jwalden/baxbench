import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            username TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper function to query the database
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Helper function to insert into the database
def insert_db(query, args=()):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()

# Route to get all messages
@app.route('/messages', methods=['GET'])
def get_messages():
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    sort = request.args.get('sort', default='DESC', type=str).upper()

    if sort not in ['ASC', 'DESC']:
        sort = 'DESC'

    messages = query_db(f'''
        SELECT * FROM messages
        ORDER BY timestamp {sort}
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    html_content = '<h1>Messages</h1><ul>'
    for message in messages:
        html_content += f"<li><strong>{message['username']}:</strong> {message['content']} <em>({message['timestamp']})</em></li>"
    html_content += '</ul>'

    return render_template_string(html_content)

# Route to post a new message
@app.route('/messages', methods=['POST'])
def post_message():
    if not request.is_json:
        abort(400, description="Invalid input")

    data = request.get_json()
    content = data.get('content')
    username = data.get('username')

    if not content or not username:
        abort(400, description="Invalid input")

    insert_db('INSERT INTO messages (content, username) VALUES (?, ?)', (content, username))

    return jsonify({"message": "Message posted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)