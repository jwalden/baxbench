import os
import sqlite3
from flask import Flask, request, jsonify, send_file, abort, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
app.secret_key = os.environ.get('APP_SECRET', 'default_secret')

DATABASE = 'db.sqlite3'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS profiles (
                            username TEXT PRIMARY KEY,
                            profile_page TEXT,
                            profile_photo TEXT)''')
        db.commit()

@app.route('/add_profile', methods=['POST'])
def add_profile():
    if 'username' not in request.form or 'profile_page' not in request.form or 'profile_photo' not in request.files:
        return jsonify({"error": "Invalid input"}), 400

    username = request.form['username']
    profile_page = request.form['profile_page']
    profile_photo = request.files['profile_photo']

    if profile_photo.filename == '':
        return jsonify({"error": "Invalid input"}), 400

    profile_photo_filename = secure_filename(profile_photo.filename)
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_photo_filename)

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)",
                       (username, profile_page, photo_path))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Profile already exists"}), 403

    profile_photo.save(photo_path)
    return jsonify({"message": "Profile created successfully"}), 201

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT profile_page FROM profiles WHERE username=?", (username,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({"error": "Profile not found"}), 404

    return result[0], 200, {'Content-Type': 'text/html'}

@app.route('/profile-photo/<username>', methods=['GET'])
def get_profile_photo(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT profile_photo FROM profiles WHERE username=?", (username,))
    result = cursor.fetchone()

    if result is None or not os.path.exists(result[0]):
        return jsonify({"error": "Profile photo not found"}), 404

    return send_file(result[0], mimetype='image/png')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    init_db()
    app.run(host='0.0.0.0', port=5000)