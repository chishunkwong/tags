import glob
import os
import json
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
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


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
    if 'tag_groups' not in session:
        tag_groups = load_tag_groups()
        session['tag_groups'] = tag_groups
    if 'cached_filenames' not in session:
        root_len = len(root_dir)
        media_arr = []
        for filename in glob.iglob(root_dir + '**/*.' + extension, recursive=True):
            if not Path(filename).is_symlink():
                rel_path = filename[root_len:]
                media_arr.append(rel_path)
        media_arr.sort()
        session['cached_filenames'] = media_arr
    cached_filenames = session['cached_filenames']
    media = {}
    bookmarks = load_bookmarks()
    for idx, path in enumerate(cached_filenames):
        media[idx] = {
            'path': path,
            'bookmarked': (root_dir + path) in bookmarks
        }
    return render_template('list.html',
                           media=media,
                           total=len(cached_filenames))

@app.route('/refresh_media_list', methods=['GET', 'POST'])
def refresh_media_list():
    session.pop('cached_filenames', None)
    session.pop('tag_groups', None)
    return redirect(url_for('list_media'))

def refresh_one_tag_group(id):
    tag_group = load_one_tag_group(id)
    tag_groups = session['tag_groups'] if 'tag_groups' in session else []
    found = None
    for i, tg in enumerate(tag_groups):
        if tg.id == id:
            found = i
            break
    if found is not None:
        tag_groups[found] = tag_group

@app.route('/search', methods=["POST"])
def handle_search():
    print("Search data:", request.form)
    return redirect(url_for('list_media'))

@app.route('/show_media')
def show_media():
    tag_groups = session['tag_groups'] if 'tag_groups' in session else []
    cached_filenames = session['cached_filenames'] if 'cached_filenames' in session else None
    total = len(cached_filenames) if cached_filenames is not None else 1
    idx_str = request.args.get('idx')
    idx = randint(0, total - 1) if idx_str == 'random' else int(idx_str)
    if cached_filenames is not None and idx >= 0 and idx < total:
        filename = cached_filenames[idx]
        filepath = root_dir + filename
        filesize = int(os.path.getsize(filepath) / (1024 * 1024))
        asset = ensure_media_in_db(filepath)
        checked_tag_ids = get_checked_tag_ids(asset)
        return render_template('media.html',
                               filename=filename,
                               filesize=filesize,
                               media_type=extension,
                               db_id=asset.id,
                               search_mode=False,
                               favorite=asset.favorite,
                               bookmark=asset.bookmark,
                               should_delete=asset.should_delete,
                               tag_groups=tag_groups,
                               tag_ids={tag.id for tag in asset.tags},
                               checked_tag_ids = checked_tag_ids,
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

def get_checked_tag_ids(asset):
    seen_groups = set()
    tag_ids = []
    for tag in asset.tags:
        if tag.tag_group_id not in seen_groups:
            seen_groups.add(tag.tag_group_id)
            tag_ids.append(str(tag.id))
    return " ".join(tag_ids)

def load_tag_groups():
    category_tag_groups = db.session.execute(db.select(CategoryTagGroup)
                                    .filter_by(name=category)
                                    .order_by(CategoryTagGroup.display_order)
                                    ).scalars().all()
    return [load_one_tag_group(ctg.tag_group_id) for ctg in category_tag_groups]

def load_one_tag_group(id):
    return db.session.scalars(db.select(TagGroup)
                              .options(joinedload(TagGroup.tags))
                              .filter_by(id=id)
                              ).unique().one()

# Return a set of bookmarks
def load_bookmarks():
    bookmarked = db.session.execute(db.select(Asset)
                                    .filter_by(bookmark=True)
                                    ).scalars().all()
    return {asset.path for asset in bookmarked}

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
    socketio.emit('response', 'Server received your message: ' + data)

@socketio.on('set_asset_boolean')
def handle_set_asset_boolean(data):
    db_id = data['db_id']
    asset = db.session.get(Asset, db_id)
    attribute = data['attribute']
    setattr(asset, attribute, data['value'])
    db.session.commit()
    # TODO: business logic!
    broadcast = attribute == 'favorite'
    if broadcast:
        socketio.emit('set_asset_' + db_id + '_attribute',
                      {
                          'attribute': attribute,
                          'value': getattr(asset, attribute) == True
                      })

@socketio.on('set_tag')
def handle_set_tag(data):
    try:
        checked = data["value"]
        db_id = data["db_id"]
        tag_group_id = int(data["tag_group_id"])
        tag_id = data["tag_id"]
        asset = db.session.get(Asset, db_id)
        tag_group = db.session.get(TagGroup, tag_group_id)
        involved_tag = db.session.get(Tag, tag_id)
        tag_to_remove = None
        tag_to_add = None
        if checked:
            tag_to_add = involved_tag
            if not tag_group.multiselect:
                for tag in asset.tags:
                    if tag.tag_group_id == tag_group_id:
                        tag_to_remove = tag
                        break
        else:
            tag_to_remove = involved_tag
        if tag_to_remove is not None:
            asset.tags.remove(tag_to_remove)
        if tag_to_add is not None:
            asset.tags.append(tag_to_add)
        db.session.add(asset)
        db.session.commit()
    except NoResultFound:
        print(f"Error: No entity found for asset {db_id} or tag group {tag_group_id} or tag {tag_id}")
    except MultipleResultsFound:
        print("Not possible")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

@app.route('/add_tag', methods=["POST"])
def handle_add_tag():
    try:
        name = request.form.get("name")
        idx = request.form.get("idx")
        tag_group_id = int(request.form.get("tag_group_id"))
        db_id = request.form.get("db_id")
        asset = db.session.get(Asset, db_id)
        tag_group = db.session.get(TagGroup, tag_group_id)
        new_tag = Tag(name=name, tag_group_id=tag_group_id)
        db.session.add(new_tag)
        tag_to_remove_first = None
        if not tag_group.multiselect:
            for tag in asset.tags:
                if tag.tag_group_id == tag_group_id:
                    tag_to_remove_first = tag
                    break
            if tag_to_remove_first is not None:
                asset.tags.remove(tag_to_remove_first)
        asset.tags.append(new_tag)
        db.session.add(asset)
        db.session.commit()
    except NoResultFound:
        print(f"Error: No entity found for asset {db_id} or {tag_group_id}")
    except MultipleResultsFound:
        print("Not possible")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    refresh_one_tag_group(tag_group_id)

    return redirect(url_for('show_media', idx=idx))

if __name__ == '__main__':
    socketio.run(app, debug=True)
