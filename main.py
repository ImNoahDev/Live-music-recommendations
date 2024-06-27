from flask import Flask, request, render_template, redirect, url_for
import json
import nfc

app = Flask(__name__)

# Admin password (store securely in environment variable or configuration in a real app)
ADMIN_PASSWORD = 'admin_password'

# File to store user data
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"pending": {}, "approved": []}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file)

# NFC Reader Setup
def read_nfc():
    clf = nfc.ContactlessFrontend('usb')
    tag = clf.connect(rdwr={'on-connect': lambda tag: False})
    uid = tag.identifier.hex()
    return uid

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    uid = read_nfc()
    user_data = load_user_data()
    if uid not in user_data["pending"]:
        user_data["pending"][uid] = {"songs": []}
    save_user_data(user_data)
    return redirect(url_for('recommend', uid=uid))

@app.route('/admin-login', methods=['POST'])
def admin_login():
    password = request.form['password']
    if password == ADMIN_PASSWORD:
        # Redirect to the recommend page as an admin
        return redirect(url_for('recommend', uid='admin', admin=True))
    else:
        return redirect(url_for('index'))

@app.route('/recommend/<uid>', methods=['GET', 'POST'])
def recommend(uid):
    user_data = load_user_data()
    message = ""
    is_admin = request.args.get('admin', False)
    if uid != 'admin' and uid not in user_data["pending"]:
        user_data["pending"][uid] = {"songs": []}
    if request.method == 'POST':
        song_name = request.form['song_name']
        if is_admin:
            # Allow admin to add songs to any user's pending list
            target_uid = request.form.get('target_uid', uid)
            if target_uid not in user_data["pending"]:
                user_data["pending"][target_uid] = {"songs": []}
            user_data["pending"][target_uid]["songs"].append(song_name)
        else:
            user_data["pending"][uid]["songs"].append(song_name)
        save_user_data(user_data)
        return redirect(url_for('index'))  # Redirect to index after recommending a song
    return render_template('recommend.html', uid=uid, songs=user_data["pending"].get(uid, {"songs": []})["songs"], message=message, is_admin=is_admin)

@app.route('/admin')
def admin():
    user_data = load_user_data()
    all_songs = []
    for uid, data in user_data["pending"].items():
        for song in data.get('songs', []):
            all_songs.append({'uid': uid, 'song': song})
    all_songs_sorted = sorted(all_songs, key=lambda x: x['uid'])  # Sort from oldest to newest based on UID (assuming UID is time-based)
    approved_songs = user_data["approved"]
    return render_template('admin.html', all_songs=all_songs_sorted, approved_songs=approved_songs)

@app.route('/remove-song', methods=['POST'])
def remove_song():
    song_to_remove = request.form['song']
    user_data = load_user_data()
    for uid, data in user_data["pending"].items():
        if song_to_remove in data.get('songs', []):
            data['songs'].remove(song_to_remove)
            break
    save_user_data(user_data)
    return redirect(url_for('admin'))

@app.route('/approve-song', methods=['POST'])
def approve_song():
    song_to_approve = request.form['song']
    user_data = load_user_data()
    for uid, data in user_data["pending"].items():
        if song_to_approve in data.get('songs', []):
            data['songs'].remove(song_to_approve)
            user_data["approved"].append({'uid': uid, 'song': song_to_approve})
            break
    save_user_data(user_data)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
