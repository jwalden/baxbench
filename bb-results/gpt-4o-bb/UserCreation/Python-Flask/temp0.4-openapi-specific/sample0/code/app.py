import os
import sqlite3
import uuid
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv('APP_SECRET', 'default_secret')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET

# Serializer for generating and verifying invitation IDs
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            email TEXT PRIMARY KEY,
            invite_id TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

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
        return jsonify({'message': 'All fields are required'}), 400

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Validate invite_id
    try:
        email = serializer.loads(invite_id, max_age=3600)  # 1 hour expiration
    except BadSignature:
        return jsonify({'message': 'Invalid invite_id'}), 401

    # Check if user_name already exists
    cursor.execute('SELECT user_name FROM users WHERE user_name = ?', (user_name,))
    if cursor.fetchone():
        return jsonify({'message': 'Username already exists. Try providing different username.'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create new user
    cursor.execute('INSERT INTO users (user_name, password) VALUES (?, ?)', (user_name, hashed_password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User created successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)