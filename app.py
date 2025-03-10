import glob
import os
from pathlib import Path
from random import randint
from flask import Flask, send_file, render_template, request, session
from flask_socketio import SocketIO
from flask_session import Session
from dotenv import load_dotenv


app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
# What is this?
app.config['SECRET_KEY'] = 'my_secret_key'  # Replace with your own secret key

load_dotenv()
root_dir = os.getenv("ROOT_DIR")
extension = os.getenv("EXT")

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list_media')
def list_media():
    print("=====HERE" + root_dir)
    if 'cached_filenames' not in session:
        root_len = len(root_dir)
        media = []
        for filename in glob.iglob(root_dir + '**/*.' + extension, recursive=True):
            print("=====" + filename)
            if not Path(filename).is_symlink():
                path_from_root = filename[root_len:]
                media.append(path_from_root)
        media.sort()
        session['cached_filenames'] = media
    cached_filenames = session['cached_filenames']
    return render_template('list.html', media=cached_filenames, total=len(cached_filenames))

@app.route('/show_media')
def show_media():
    cached_filenames = session['cached_filenames'] if 'cached_filenames' in session else None
    total = len(cached_filenames) if cached_filenames is not None else 1
    idx_str = request.args.get('idx')
    idx = randint(0, total - 1) if idx_str == 'random' else int(idx_str)
    if cached_filenames is not None and idx >= 0 and idx < total:
        filename = cached_filenames[idx]
        return render_template('media.html', filename=filename, media_type=extension, idx=idx, total=total)
    else:
        return("<h1>Exception: Out of bounds</h1>")

@app.route('/send_media')
def send_media():
  try:
    idx = request.args.get('idx')
    file_path = root_dir + session['cached_filenames'][int(idx)]
    print('Fetching ' + file_path)
    return send_file(file_path)
  except BaseException as e:
    print (e)
    return("<h1>Exception: Download operation failed</h1>")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    socketio.emit('response', 'Server received your message: ' + data)

if __name__ == '__main__':
    socketio.run(app, debug=True)
