import os
import shutil
from datetime import timedelta
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
app.config["SESSION_PERMANENT"] = False # Session expires when browser closes
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQLAlchemy(app, model_class=Base)
migrate = Migrate(app, db)

base_root_dir = os.getenv("ROOT_DIR")
if base_root_dir[-1] != '/':
    base_root_dir = base_root_dir + '/'

base_trash_dir = os.getenv("TRASH_DIR")

base_extensions = os.getenv("EXTENSIONS")
base_category = os.getenv("CATEGORY")

socketio = SocketIO(app, manage_session=False)

@app.route('/')
def index():
    return render_template('index.html')

def get_and_set_root_dir():
    root_dir = request.args.get('root_dir')
    if root_dir:
        if root_dir[-1] != '/':
            root_dir = root_dir + '/'
        session.pop('all_available_media', None)
        session.pop('filtered_media', None)
        session.pop('assets', None)
        session['user_specified_root_dir'] = root_dir
        extensions = request.args.get('extensions')
        if extensions:
            session['user_specified_extensions'] = extensions
        category = request.args.get('category')
        if category:
            session['user_specified_category'] = category
    elif 'user_specified_root_dir' in session:
        root_dir = session['user_specified_root_dir']
    else:
        root_dir = base_root_dir
    return root_dir

def get_root_dir():
    return session['user_specified_root_dir'] if 'user_specified_root_dir' in session \
        else base_root_dir

def get_extensions():
    extensions_str = session['user_specified_extensions'] if \
        'user_specified_extensions' in session else base_extensions
    return extensions_str.split(',')

def get_category():
    return session['user_specified_category'] if \
        'user_specified_category' in session else base_category

@app.route('/list_media')
def list_media():
    # must do this first because it sets the session to be aware of
    # whether root_dir is set at the request level
    root_dir = get_and_set_root_dir()
    session.pop('carries', None)
    if 'tag_groups' in session:
        tag_groups = session['tag_groups']
    else:
        tag_groups = load_tag_groups()
        session['tag_groups'] = tag_groups
    filtered_media = get_filtered_media()
    media = {}
    bookmarks = load_bookmarks()
    favorites = load_favorites()
    for idx, path in enumerate(filtered_media):
        media[idx] = {
            'path': path,
            'bookmarked': (root_dir + path) in bookmarks,
            'favorite': (root_dir + path) in favorites,
        }
    query = session["query"] if "query" in session else {}
    tag_ids = []
    for key in query.keys():
        #TODO: use constant
        if key.startswith("tag_"):
            tag_ids.append(int(key[len("tag_"):]))
    return render_template('list.html',
                           media=media,
                           root_dir=root_dir,
                           extensions=get_extensions(),
                           search_mode=True,
                           checked_tag_ids = "TODO",
                           favorite=("bool_" + "favorite") in query,
                           bookmark=("bool_" + "bookmark") in query,
                           should_delete=("bool_" + "should_delete") in query,
                           tag_groups=tag_groups,
                           tag_ids=tag_ids,
                           total=len(filtered_media))

def get_filtered_media():
    if 'filtered_media' not in session:
        scan_all_available_media()
        filter_by_searched()
    return session['filtered_media']

def scan_all_available_media():
    root_dir = get_root_dir()
    if 'all_available_media' not in session:
        root_len = len(root_dir)
        media_arr = []
        root_path = Path(root_dir)
        extensions = get_extensions()
        for extension in extensions:
            for path in root_path.rglob('*.' + extension, case_sensitive=False):
                if not Path(path).is_symlink():
                    rel_path = str(path)[root_len:]
                    media_arr.append(rel_path)
        media_arr.sort()
        session['all_available_media'] = media_arr

def filter_by_searched():
    root_dir = get_root_dir()
    all_available_media = session['all_available_media']
    if 'assets' not in session:
        session['filtered_media'] = all_available_media
        return
    filtered_paths = set()
    assets = session['assets']
    for asset in assets:
        filtered_paths.add(asset['path'])
    session['filtered_media'] = \
        [rel_path for rel_path in all_available_media if (root_dir + rel_path) in filtered_paths]

@app.route('/refresh_all', methods=['GET', 'POST'])
def refresh_all():
    session.pop('deleted', None)
    session.pop('all_available_media', None)
    session.pop('filtered_media', None)
    session.pop('tag_groups', None)
    session.pop('assets', None)
    session.pop('query', None)
    session.pop('carries', None)
    return redirect(url_for('list_media'))

@app.route('/refresh_tags', methods=['GET', 'POST'])
def refresh_tags():
    session.pop('tag_groups', None)
    session.pop('query', None)
    session.pop('carries', None)
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
    root_dir = get_root_dir()
    session.pop('filtered_media', None)
    print("Search data:", request.form)
    query = request.form
    if query["action"] == "Clear":
        session.pop('assets', None)
        session.pop('query', None)
        return redirect(url_for('list_media'))
    session['query'] = query
    bool_filters = {}
    tag_filters = []
    for key, value in query.items():
        #TODO: use constants
        if key.startswith("bool_"):
            bool_filters[key[len("bool_"):]] = True
        if key.startswith("tag_"):
            tag_filters.append(int(key[len("tag_"):]))
    stmt = db.select(Asset).filter_by(**bool_filters).filter(Asset.path.startswith(root_dir))
    for tag_id in tag_filters:
        stmt = stmt.where(Asset.tags.any(Tag.id == tag_id))
    assets = db.session.scalars(stmt)
    session['assets'] = [asset.to_dict() for asset in assets]
    return redirect(url_for('list_media'))

@app.route('/show_media')
def show_media():
    root_dir = get_root_dir()
    tag_groups = session['tag_groups'] if 'tag_groups' in session else []
    carries = session['carries'] if 'carries' in session else set()
    filtered_media = session['filtered_media'] if 'filtered_media' in session else None
    total = len(filtered_media) if filtered_media is not None else 1
    idx_str = request.args.get('idx')
    idx = randint(0, total - 1) if idx_str == 'random' else int(idx_str)
    next_prev = request.args.get('next_prev')
    if next_prev:
        idx = find_valid_media(idx, next_prev == 'next', filtered_media, root_dir)
    if filtered_media is not None and idx >= 0 and idx < total:
        filename = filtered_media[idx]
        filepath = root_dir + filename
        file_found = False
        try:
            filesize_mb = int(os.path.getsize(filepath) / (1024 * 1024))
            file_found = True
            if filesize_mb > 9:
                filesize = f"{filesize_mb} MB"
            else:
                filesize_kb = int(os.path.getsize(filepath) / 1024)
                filesize = f"{filesize_kb} KB"
            asset = ensure_media_in_db(filepath)
            referrer = request.args.get('current')
            set_carried_tags(asset, referrer)
            # HERE HERE
            db_id = asset.id
            favorite = asset.favorite
            bookmark = asset.bookmark
            should_delete = asset.should_delete
            tag_ids = {tag.id for tag in asset.tags}
            checked_tag_ids = get_checked_tag_ids(asset)
        except FileNotFoundError:
            filesize = 0 #dummy
            db_id = ""
            favorite = False
            bookmark = False
            should_delete = False
            tag_ids = {}
            checked_tag_ids = ""
        return render_template('media.html',
                               file_found=file_found,
                               filename=filename,
                               filesize=filesize,
                               search_mode=False,
                               tag_groups=tag_groups,
                               carries=carries,
                               db_id=db_id,
                               favorite=favorite,
                               bookmark=bookmark,
                               should_delete=should_delete,
                               tag_ids=tag_ids,
                               checked_tag_ids = checked_tag_ids,
                               idx=idx,
                               total=total)
    else:
        return("<h1>Exception: Out of bounds</h1>")

def find_valid_media(idx, forward, filtered_media, root_dir):
    if not filtered_media:
        return -1;
    total = len(filtered_media)
    found = -1
    while (forward and idx < total) or (not forward and idx >= 0):
        filename = filtered_media[idx]
        filepath = root_dir + filename
        try:
            os.path.getsize(filepath)
            found = idx
            break
        except FileNotFoundError:
            idx = idx + 1 if forward else idx - 1
    return found

def ensure_media_in_db(path):
    asset = db.session.scalars(db.select(Asset).filter_by(path=path)).one_or_none()
    if not asset:
        asset = Asset(path=path)
        db.session.add(asset)
        db.session.commit()
        asset = db.session.scalars(db.select(Asset).filter_by(path=path)).one_or_none()
    return asset

def set_carried_tags(asset, referrer_id):
    # we don't carry over any tags if the current asset is already tagged
    # (even if the tags and the carries do not contradict)
    if not referrer_id or referrer_id == "" or int(referrer_id) < 0 or asset.tags:
        return
    if 'carries' not in session:
        return
    carries = session['carries']
    referrer = db.session.get(Asset, referrer_id)
    added = False
    for tag in referrer.tags:
        if tag.tag_group_id in carries:
            added = True
            asset.tags.append(tag)
    if added:
        db.session.add(asset)
        db.session.commit()

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
                                    .filter_by(name=get_category())
                                    .order_by(CategoryTagGroup.display_order)
                                    ).scalars().all()
    return [load_one_tag_group(ctg.tag_group_id) for ctg in category_tag_groups]

def load_one_tag_group(id):
    return db.session.scalars(db.select(TagGroup)
                              .options(joinedload(TagGroup.tags))
                              .filter_by(id=id)
                              ).unique().one()

# Return a set of paths
def load_bookmarks():
    bookmarked = db.session.execute(db.select(Asset)
                                    .filter_by(bookmark=True)
                                    ).scalars().all()
    return {asset.path for asset in bookmarked}

def load_favorites():
    favorites = db.session.execute(db.select(Asset)
                                   .filter_by(favorite=True)
                                   ).scalars().all()
    return {asset.path for asset in favorites}

@app.route('/send_media')
def send_media():
  root_dir = get_root_dir()
  try:
    idx = request.args.get('idx')
    file_path = root_dir + session['filtered_media'][int(idx)]
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

@socketio.on('disconnect')
def handle_connect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    socketio.emit('response', 'Server received your message: ' + data)

@socketio.on('set_tag_group_carry')
def handle_set_tag_group_carry(data):
    existed = False
    if 'carries' in session:
        carries = session['carries']
        existed = True
    else:
        carries = set()
        session['carries'] = carries
    tag_group_id = data['tag_group_id']
    if data['value']:
        carries.add(int(tag_group_id))
    else:
        carries.remove(int(tag_group_id))
    if existed:
        #TODO: for some reason directly altering an object in session from socketio code
        # won't persist that change, has to pop and re-add
        session.pop('carries', None)
        session['carries'] = carries

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

@app.route('/delete')
def handle_delete():
    idx = int(request.args.get('idx'))
    db_id = int(request.args.get('db_id'))
    asset = db.session.get(Asset, db_id)
    full_path = asset.path
    head, name = os.path.split(full_path)
    head, dir = os.path.split(head)
    # keep the last two levels (name count as one) but flatten it
    new_path = os.path.join(get_trash_dir(), dir + '_' + name)
    print("Moving", full_path, new_path)
    shutil.move(full_path, new_path)
    set_deleted(idx, full_path, new_path)
    db.session.delete(asset)
    db.session.commit()
    # Let show_media takes care of bounds check
    return redirect(url_for('show_media', idx=idx+1, next_prev='next'))

def set_deleted(idx, full_path, new_path):
    if 'deleted' in session:
        deleted = session['deleted']
    else:
        deleted = []
        session['deleted'] = deleted
    deleted.append({
        'idx': idx,
        'full_path': full_path,
        'new_path': new_path,
    })
    if len(deleted) >= 10:
        session['deleted'] = deleted[-5:]

@app.route('/undo_delete')
def handle_undo_delete():
    try:
        idx = int(request.args.get('idx'))
    except:
        idx = None
    deleted = session['deleted'] if 'deleted' in session else []
    next_idx = None
    if len(deleted) == 0:
        next_idx = idx
    else:
        last_deleted = deleted.pop()
        print("last_deleted", last_deleted)
        new_path = last_deleted['full_path']
        full_path = last_deleted['new_path']
        print("Moving back", full_path, new_path)
        shutil.move(full_path, new_path)
        next_idx = last_deleted['idx']
    if next_idx is None:
        return redirect(url_for('list_media'))
    else:
        return redirect(url_for('show_media', idx=next_idx))

def get_trash_dir():
    trash_dir = os.getenv(get_category() + "_TRASH_DIR")
    return trash_dir if trash_dir else base_trash_dir

if __name__ == '__main__':
    socketio.run(app, debug=True)
