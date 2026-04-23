import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeSerializer

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_secret')

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            invite_id TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Serializer for generating invite IDs
serializer = URLSafeSerializer(app.secret_key)

@app.route('/invite_user', methods=['POST'])
def invite_user():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Check if the email already has an invitation
    cursor.execute('SELECT invite_id FROM invitations WHERE email = ?', (email,))
    row = cursor.fetchone()

    if row:
        invite_id = row[0]
    else:
        invite_id = serializer.dumps(email)
        cursor.execute('INSERT INTO invitations (email, invite_id) VALUES (?, ?)', (email, invite_id))
        conn.commit()

    conn.close()
    return jsonify({'invite_id': invite_id, 'message': 'Invitation created successfully'}), 200

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    invite_id = data.get('invite_id')
    user_name = data.get('user_name')
    password = data.get('password')

    if not invite_id or not user_name or not password:
        return jsonify({'message': 'Invite ID, username, and password are required'}), 400

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Verify the invite_id
    cursor.execute('SELECT email FROM invitations WHERE invite_id = ?', (invite_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'message': 'Invalid invite_id'}), 401

    # Check if the username already exists
    cursor.execute('SELECT id FROM users WHERE user_name = ?', (user_name,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Username already exists. Try providing different username.'}), 400

    # Create the user
    hashed_password = generate_password_hash(password)
    cursor.execute('INSERT INTO users (user_name, password) VALUES (?, ?)', (user_name, hashed_password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User created successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)