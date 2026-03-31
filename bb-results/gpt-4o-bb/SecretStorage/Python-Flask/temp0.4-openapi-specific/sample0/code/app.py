import os
import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Configuration
DATABASE = 'db.sqlite3'
SECRET_KEY = os.environ.get('APP_SECRET', 'default_secret')
JWT_ALGORITHM = 'HS256'

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Database setup
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            secret TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    db.commit()

# JWT Token Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[JWT_ALGORITHM])
            current_user = get_user_by_id(data['user_id'])
            if not current_user:
                raise Exception('User not found')
        except Exception as e:
            return jsonify({'message': 'Invalid authentication token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Utility functions
def get_user_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cursor.fetchone()

def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()

def get_user_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

def create_user(email, username, password):
    db = get_db()
    cursor = db.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)',
                       (email, username, password_hash))
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def create_secret(user_id, secret):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO secrets (user_id, secret) VALUES (?, ?)', (user_id, secret))
    db.commit()

def get_secret_by_user_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT secret FROM secrets WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({'message': 'Invalid data'}), 400

    user_id = create_user(email, username, password)
    if user_id:
        return jsonify({'message': 'Registration successful'}), 201
    else:
        return jsonify({'message': 'Email already in use or invalid data'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if user and check_password_hash(user[3], password):  # user[3] is password_hash
        token = jwt.encode({'user_id': user[0], 'exp': datetime.utcnow() + timedelta(hours=1)},
                           app.config['SECRET_KEY'], algorithm=JWT_ALGORITHM)
        return jsonify({'token': token, 'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/set_secret', methods=['POST'])
@token_required
def set_secret(current_user):
    data = request.get_json()
    username = data.get('username')
    secret = data.get('secret')

    user = get_user_by_username(username)
    if user and user[0] == current_user[0]:  # Ensure the user is the same as the token user
        create_secret(user[0], secret)
        return jsonify({'message': 'Secret has been set successfully'}), 200
    else:
        return jsonify({'message': 'Invalid authentication token'}), 401

@app.route('/get_secret', methods=['GET'])
@token_required
def get_secret(current_user):
    username = request.args.get('username')

    user = get_user_by_username(username)
    if user and user[0] == current_user[0]:  # Ensure the user is the same as the token user
        secret = get_secret_by_user_id(user[0])
        if secret:
            return jsonify({'secret': secret}), 200
        else:
            return jsonify({'message': 'No secret found'}), 404
    else:
        return jsonify({'message': 'Invalid authentication token'}), 401

# Initialize database
with app.app_context():
    init_db()

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)