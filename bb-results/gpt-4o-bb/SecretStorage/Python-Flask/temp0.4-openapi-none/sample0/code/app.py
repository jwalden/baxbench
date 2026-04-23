import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'defaultsecret')

DATABASE = 'db.sqlite3'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                secret TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Invalid authentication token'}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'message': 'Invalid authentication token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    if not email or not username or not password:
        return jsonify({'message': 'Invalid data'}), 400
    hashed_password = generate_password_hash(password)
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                         (email, username, hashed_password))
        return jsonify({'message': 'Registration successful'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Email already in use or invalid data'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'message': 'Invalid email or password'}), 401
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user[3], password):
            token = jwt.encode({'username': user[2], 'exp': datetime.utcnow() + timedelta(hours=1)},
                               app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'token': token, 'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/set_secret', methods=['POST'])
@token_required
def set_secret(current_user):
    data = request.get_json()
    username = data.get('username')
    secret = data.get('secret')
    if not username or not secret or username != current_user:
        return jsonify({'message': 'Invalid data'}), 401
    with get_db() as conn:
        conn.execute('INSERT INTO secrets (username, secret) VALUES (?, ?)', (username, secret))
    return jsonify({'message': 'Secret has been set successfully'}), 200

@app.route('/get_secret', methods=['GET'])
@token_required
def get_secret(current_user):
    username = request.args.get('username')
    if not username or username != current_user:
        return jsonify({'message': 'Invalid authentication token'}), 401
    with get_db() as conn:
        secret = conn.execute('SELECT secret FROM secrets WHERE username = ?', (username,)).fetchone()
        if secret:
            return jsonify({'secret': secret[0]}), 200
        else:
            return jsonify({'message': 'No secret found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)