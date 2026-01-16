import glob
import os
from pathlib import Path
from random import randint
from flask import Flask, send_file, render_template, request, session, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
from dotenv import load_dotenv
from models.asset import Asset
from models.tag import Tag
from models.tag_group import TagGroup
from models.category_tag_group import CategoryTagGroup
from models.base import Base


load_dotenv()

app = Flask(__name__)
if os.getenv("ENV") == 'Dev':
    app.config.from_object('config.DevelopmentConfig')
Session(app)
db = SQLAlchemy(app, model_class=Base)
migrate = Migrate(app, db)

root_dir = os.getenv("ROOT_DIR")
if root_dir[-1] != '/':
    root_dir = root_dir + '/'
extension = os.getenv("EXT")

category = os.getenv("CATEGORY")

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list_media')
def list_media():
    if 'cached_filenames' not in session:
        root_len = len(root_dir)
        media = []
        for filename in glob.iglob(root_dir + '**/*.' + extension, recursive=True):
            if not Path(filename).is_symlink():
                path_from_root = filename[root_len:]
                media.append(path_from_root)
        media.sort()
        session['cached_filenames'] = media
    cached_filenames = session['cached_filenames']
    return render_template('list.html', media=cached_filenames, total=len(cached_filenames))

@app.route('/refresh_media_list', methods=['GET', 'POST'])
def refresh_media_list():
    session.pop('cached_filenames', None)
    return redirect(url_for('list_media'))

@app.route('/show_media')
def show_media():
    cached_filenames = session['cached_filenames'] if 'cached_filenames' in session else None
    total = len(cached_filenames) if cached_filenames is not None else 1
    idx_str = request.args.get('idx')
    idx = randint(0, total - 1) if idx_str == 'random' else int(idx_str)
    if cached_filenames is not None and idx >= 0 and idx < total:
        filename = cached_filenames[idx]
        filepath = root_dir + filename
        filesize = int(os.path.getsize(filepath) / (1024 * 1024))
        asset = ensure_media_in_db(filepath)
        return render_template('media.html',
                               filename=filename,
                               filesize=filesize,
                               media_type=extension,
                               db_id=asset.id,
                               favorite=asset.favorite,
                               idx=idx,
                               total=total)
    else:
        return("<h1>Exception: Out of bounds</h1>")

def ensure_media_in_db(path):
    asset = db.session.scalars(db.select(Asset).filter_by(path=path)).one_or_none()
    if not asset:
        asset = Asset(path=path)
        db.session.add(asset)
        db.session.commit()
        asset = db.session.scalars(db.select(Asset).filter_by(path=path)).one_or_none()
    return asset

def load_tag_groups():
    tag_groups = db.session.execute(db.select(CategoryTagGroup)
                                    .filter_by(name=category)
                                    .order_by(CategoryTagGroup.display_order)
                                    ).scalars().all()
    return tag_groups

@app.route('/send_media')
def send_media():
  try:
    idx = request.args.get('idx')
    file_path = root_dir + session['cached_filenames'][int(idx)]
    return send_file(file_path)
  except BaseException as e:
    print (e)
    return("<h1>Exception: Download operation failed</h1>")

@app.route('/handle_save')
def handle_save():
    pass

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    socketio.emit('response', 'Server received your message: ' + data)

@socketio.on('set_favorite')
def handle_set_favorite(data):
    print('Received set_favorite:', data, type(data))
    db_id = data['db_id']
    asset = db.session.get(Asset, db_id)
    if asset is None:
        return
    favorite = data['favorite']
    asset.favorite = favorite
    print('Setting favorite for ', asset.path, asset.id)
    db.session.commit()
    socketio.emit('set_favorite', 'true' if asset.favorite else 'false')

if __name__ == '__main__':
    socketio.run(app, debug=True)
