import os
import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret_key')

DATABASE = 'db.sqlite3'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                secret TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({'message': 'Invalid data'}), 400

    hashed_password = pbkdf2_sha256.hash(password)
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                       (email, username, hashed_password))
        db.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Email or username already in use'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Invalid email or password'}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user and pbkdf2_sha256.verify(password, user[1]):
        token = jwt.encode({'user_id': user[0], 'exp': datetime.utcnow() + timedelta(hours=1)},
                           app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token, 'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/set_secret', methods=['POST'])
@token_required
def set_secret():
    data = request.get_json()
    username = data.get('username')
    secret = data.get('secret')

    if not username or not secret:
        return jsonify({'message': 'Invalid data'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user:
        cursor.execute('INSERT INTO secrets (user_id, secret) VALUES (?, ?)', (user[0], secret))
        db.commit()
        return jsonify({'message': 'Secret has been set successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 400

@app.route('/get_secret', methods=['GET'])
@token_required
def get_secret():
    username = request.args.get('username')

    if not username:
        return jsonify({'message': 'Invalid data'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user:
        cursor.execute('SELECT secret FROM secrets WHERE user_id = ?', (user[0],))
        secret = cursor.fetchone()
        if secret:
            return jsonify({'secret': secret[0]}), 200
        else:
            return jsonify({'message': 'No secret found'}), 404
    else:
        return jsonify({'message': 'User not found'}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)