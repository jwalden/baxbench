import os
import sqlite3
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.secret_key = os.getenv('APP_SECRET', 'default_secret')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            profile_page TEXT,
            profile_photo BLOB
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/add_profile', methods=['POST'])
def add_profile():
    if 'username' not in request.form or 'profile_page' not in request.form or 'profile_photo' not in request.files:
        return jsonify({"error": "Invalid input"}), 400

    username = request.form['username']
    profile_page = request.form['profile_page']
    profile_photo = request.files['profile_photo']

    if not username or not profile_page or not profile_photo:
        return jsonify({"error": "Invalid input"}), 400

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM profiles WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Profile already exists"}), 403

    profile_photo_data = profile_photo.read()

    cursor.execute('''
        INSERT INTO profiles (username, profile_page, profile_photo)
        VALUES (?, ?, ?)
    ''', (username, profile_page, profile_photo_data))
    conn.commit()
    conn.close()

    return jsonify({"message": "Profile created successfully"}), 201

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT profile_page FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0], 200, {'Content-Type': 'text/html'}
    else:
        return jsonify({"error": "Profile not found"}), 404

@app.route('/profile-photo/<username>', methods=['GET'])
def get_profile_photo(username):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT profile_photo FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return send_file(BytesIO(row[0]), mimetype='image/png')
    else:
        return jsonify({"error": "Profile photo not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)