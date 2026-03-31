import os
import sqlite3
from flask import Flask, request, jsonify, send_file, abort, g
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Use APP_SECRET from environment for security
app.secret_key = os.environ.get('APP_SECRET', 'default_secret_key')

DATABASE = 'db.sqlite3'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        profile_page TEXT,
        profile_photo BLOB
    )
    ''')
    db.commit()

@app.route('/add_profile', methods=['POST'])
def add_profile():
    if 'username' not in request.form or 'profile_page' not in request.form or 'profile_photo' not in request.files:
        return jsonify({'error': 'Invalid input'}), 400

    username = request.form['username']
    profile_page = request.form['profile_page']
    profile_photo = request.files['profile_photo']

    if not username or not profile_page or not profile_photo:
        return jsonify({'error': 'Invalid input'}), 400

    filename = secure_filename(profile_photo.filename)
    if not filename.lower().endswith('.png'):
        return jsonify({'error': 'Profile photo must be a PNG image'}), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM profiles WHERE username = ?', (username,))
    if cursor.fetchone():
        return jsonify({'error': 'Profile already exists'}), 403

    photo_data = profile_photo.read()
    cursor.execute('INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)',
                   (username, profile_page, photo_data))
    db.commit()

    return jsonify({'message': 'Profile created successfully'}), 201

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT profile_page FROM profiles WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({'error': 'Profile not found'}), 404

    return result[0], 200, {'Content-Type': 'text/html'}

@app.route('/profile-photo/<username>', methods=['GET'])
def get_profile_photo(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT profile_photo FROM profiles WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({'error': 'Profile photo not found'}), 404

    return send_file(BytesIO(result[0]), mimetype='image/png')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000)