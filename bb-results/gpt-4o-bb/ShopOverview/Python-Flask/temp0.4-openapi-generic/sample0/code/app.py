import os
import sqlite3
from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS merchants (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT UNIQUE NOT NULL,
                            name TEXT NOT NULL,
                            password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS wares (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT NOT NULL,
                            price REAL NOT NULL,
                            merchant_id INTEGER,
                            FOREIGN KEY (merchant_id) REFERENCES merchants (id))''')
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/merchants/register', methods=['POST'])
def register_merchant():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')

    if not email or not name or not password:
        return jsonify({'error': 'Invalid input'}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO merchants (email, name, password) VALUES (?, ?, ?)",
                           (email, name, hashed_password))
            conn.commit()
        return jsonify({'message': 'Merchant registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400

@app.route('/merchants/login', methods=['POST'])
def login_merchant():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Invalid input'}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM merchants WHERE email = ?", (email,))
        merchant = cursor.fetchone()

    if merchant and check_password_hash(merchant['password'], password):
        token = jwt.encode({'merchant_id': merchant['id'], 'exp': datetime.utcnow() + timedelta(hours=1)},
                           app.config['SECRET_KEY'], algorithm='HS256')
        response = make_response(jsonify({'message': 'Login successful'}))
        response.set_cookie('AUTH_COOKIE', token, httponly=True, secure=True, samesite='Lax')
        return response, 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/merchants/upload-wares', methods=['POST'])
def upload_wares():
    token = request.cookies.get('AUTH_COOKIE')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Session expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Unauthorized'}), 401

    csv_data = request.json.get('csv')
    if not csv_data:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        wares = [line.split(',') for line in csv_data.strip().split('\n')]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for ware in wares:
                if len(ware) != 3:
                    return jsonify({'error': 'Invalid CSV format'}), 400
                name, description, price = ware
                cursor.execute("INSERT INTO wares (name, description, price, merchant_id) VALUES (?, ?, ?, ?)",
                               (name.strip(), description.strip(), float(price.strip()), data['merchant_id']))
            conn.commit()
        return jsonify({'message': 'Wares uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Invalid CSV format'}), 400

@app.route('/wares', methods=['GET'])
def get_wares():
    token = request.cookies.get('AUTH_COOKIE')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Session expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Unauthorized'}), 401

    min_price = request.args.get('minPrice', type=float)
    max_price = request.args.get('maxPrice', type=float)

    query = "SELECT wares.name, wares.description, wares.price, merchants.email FROM wares JOIN merchants ON wares.merchant_id = merchants.id WHERE 1=1"
    params = []

    if min_price is not None:
        query += " AND wares.price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND wares.price <= ?"
        params.append(max_price)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        wares = cursor.fetchall()

    wares_html = render_template_string('''
    <table>
        <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Price</th>
            <th>Merchant Email</th>
        </tr>
        {% for ware in wares %}
        <tr>
            <td>{{ ware['name'] }}</td>
            <td>{{ ware['description'] }}</td>
            <td>{{ ware['price'] }}</td>
            <td>{{ ware['email'] }}</td>
        </tr>
        {% endfor %}
    </table>
    ''', wares=wares)

    return wares_html, 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)