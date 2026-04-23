import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET", "default_secret_key")

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

# Get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Route to get all messages
@app.route('/messages', methods=['GET'])
def get_messages():
    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    sort = request.args.get('sort', default='DESC', type=str).upper()

    if sort not in ['ASC', 'DESC']:
        abort(400, description="Invalid sort parameter")

    conn = get_db_connection()
    messages = conn.execute(
        'SELECT username, content, timestamp FROM messages ORDER BY timestamp {} LIMIT ? OFFSET ?'.format(sort),
        (limit, offset)
    ).fetchall()
    conn.close()

    messages_list = [dict(message) for message in messages]
    return render_template_string(
        '''
        <h1>Messages</h1>
        <ul>
        {% for message in messages %}
            <li><strong>{{ message['username'] }}</strong>: {{ message['content'] }} <em>at {{ message['timestamp'] }}</em></li>
        {% endfor %}
        </ul>
        ''', messages=messages_list
    )

# Route to post a new message
@app.route('/messages', methods=['POST'])
def post_message():
    if not request.is_json:
        abort(400, description="Request must be JSON")

    data = request.get_json()
    username = data.get('username')
    content = data.get('content')

    if not username or not content:
        abort(400, description="Invalid input")

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO messages (username, content) VALUES (?, ?)',
        (username, content)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Message posted successfully"}), 200

# Initialize the database when the app starts
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)