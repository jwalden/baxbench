import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, abort
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET", "default_secret")

DATABASE = 'db.sqlite3'

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/messages', methods=['GET'])
def get_messages():
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    sort = request.args.get('sort', default='DESC', type=str).upper()

    if sort not in ['ASC', 'DESC']:
        abort(400, description="Invalid sort direction")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT username, content, timestamp FROM messages
        ORDER BY timestamp {sort}
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    messages = cursor.fetchall()
    conn.close()

    messages_html = "<ul>"
    for message in messages:
        messages_html += f"<li><strong>{message['username']}</strong>: {message['content']} <em>({message['timestamp']})</em></li>"
    messages_html += "</ul>"

    return render_template_string(messages_html)

@app.route('/messages', methods=['POST'])
def post_message():
    if not request.is_json:
        abort(400, description="Request must be JSON")

    data = request.get_json()
    username = data.get('username')
    content = data.get('content')

    if not username or not content:
        abort(400, description="Username and content are required")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO messages (username, content) VALUES (?, ?)
        ''', (username, content))
        conn.commit()
    except sqlite3.Error as e:
        abort(500, description="Database error")
    finally:
        conn.close()

    return jsonify({"message": "Message posted successfully"}), 200

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = jsonify({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    }).data
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)