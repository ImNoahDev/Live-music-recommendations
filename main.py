from flask import Flask, request, render_template, redirect, url_for, jsonify
import json
import nfc

app = Flask(__name__)

# NFC Reader Setup
def read_nfc():
    clf = nfc.ContactlessFrontend('tty:usbserial-1420:pn532')
    tag = clf.connect(rdwr={'on-connect': lambda tag: False})
    uid = tag.identifier.hex()
    return uid

# File to store user data
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    uid = read_nfc()
    user_data = load_user_data()
    if uid not in user_data:
        user_data[uid] = {"songs": []}
    save_user_data(user_data)
    return redirect(url_for('recommend', uid=uid))

@app.route('/recommend/<uid>', methods=['GET', 'POST'])
def recommend(uid):
    user_data = load_user_data()
    message = ""
    if request.method == 'POST':
        song_name = request.form['song_name']
        user_data[uid]["songs"].append(song_name)
        save_user_data(user_data)
        return redirect("index")  # Redirect to the specified URL after recommending a song
    return render_template('recommend.html', uid=uid, songs=user_data[uid]["songs"], message=message)


@app.route('/admin')
def admin():
    user_data = load_user_data()
    all_songs = []
    for uid, data in user_data.items():
        for song in data.get('songs', []):
            all_songs.append({'uid': uid, 'song': song})
    all_songs_sorted = sorted(all_songs, key=lambda x: x['uid'])  # Sort from oldest to newest based on UID (assuming UID is time-based)
    return render_template('admin.html', all_songs=all_songs_sorted)

@app.route('/remove-song', methods=['POST'])
def remove_song():
    song_to_remove = request.form['song']
    user_data = load_user_data()
    for uid, data in user_data.items():
        if song_to_remove in data.get('songs', []):
            data['songs'].remove(song_to_remove)
    save_user_data(user_data)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
