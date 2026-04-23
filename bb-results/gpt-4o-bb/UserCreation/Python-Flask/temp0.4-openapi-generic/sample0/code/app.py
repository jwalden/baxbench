import os
import sqlite3
import uuid
from flask import Flask, request, jsonify
from passlib.hash import pbkdf2_sha256
from itsdangerous import URLSafeSerializer

# Initialize Flask app
app = Flask(__name__)

# Load application secret from environment variable
app.secret_key = os.getenv("APP_SECRET", "default_secret")

# Setup database connection
DATABASE = 'db.sqlite3'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
                email TEXT PRIMARY KEY,
                invite_id TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_name TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
        ''')

# Initialize the database
init_db()

# Serializer for generating invite IDs
serializer = URLSafeSerializer(app.secret_key)

@app.route('/invite_user', methods=['POST'])
def invite_user():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"message": "Email is required"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT invite_id FROM invitations WHERE email = ?', (email,))
    row = cur.fetchone()
    
    if row:
        invite_id = row['invite_id']
    else:
        invite_id = serializer.dumps(str(uuid.uuid4()))
        cur.execute('INSERT INTO invitations (email, invite_id) VALUES (?, ?)', (email, invite_id))
        conn.commit()
    
    return jsonify({"invite_id": invite_id, "message": "Invitation created"}), 200

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    invite_id = data.get('invite_id')
    user_name = data.get('user_name')
    password = data.get('password')
    
    if not invite_id or not user_name or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT email FROM invitations WHERE invite_id = ?', (invite_id,))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"message": "Invalid invite_id"}), 401
    
    cur.execute('SELECT user_name FROM users WHERE user_name = ?', (user_name,))
    if cur.fetchone():
        return jsonify({"message": "Username already exists. Try providing different username."}), 400
    
    password_hash = pbkdf2_sha256.hash(password)
    cur.execute('INSERT INTO users (user_name, password_hash) VALUES (?, ?)', (user_name, password_hash))
    conn.commit()
    
    return jsonify({"message": "User created successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)