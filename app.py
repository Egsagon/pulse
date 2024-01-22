import re
import json
import flask
import random
import sqlite3
from pathlib import Path
from flask_caching import Cache
import fast_file_encryption as ffe
from sqlfilter import build_sql_filter

decryptor: ffe.Decryptor = None
app = flask.Flask(__name__, static_folder = 'client', template_folder = 'client')

batch: list[tuple[str, str]] = None
cbatch: dict[str, tuple[str, int, str]] = None

with open('config.json', 'r') as file:
    config: dict = json.load(file)

cache = Cache(app, config = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_THRESHOLD': int(config['cache-length'])
})

redirect_errors = {
    'b': 'No batch initialised.',
    'd': 'No decryptor ready.'
}

base = sqlite3.connect('base.db', check_same_thread = False)

def decrypt_group(grp: str) -> list[str]:
    # Decrypt a raw group list.
    
    pass
    

def get_groups() -> list[str]:
    
    rgrps = base.execute('SELECT DISTINCT groups FROM main').fetchall()
    
    groups = set()
    for raw in rgrps:
        groups.update(json.loads(raw[0]))
    
    return groups

@app.route('/')
def home():
    types = base.execute('SELECT DISTINCT ext FROM main').fetchall()
    groups = get_groups()
    
    error = '?err=' in flask.request.url
    
    return flask.render_template('index.jinja',
        haskey = bool(decryptor),
        types = list(set(types)),
        groups = list(groups),
        error = redirect_errors.get(flask.request.args.get('err'),
                                    'Unknown error') if error else None
    )

@app.route('/key', methods = ['POST'])
def load_key():
    global decryptor
    try:
        raw = flask.request.get_data(False, True)
        key = ffe.read_private_key(raw)
        decryptor = ffe.Decryptor(key)
        return '1'

    except Exception as err:
        print('Failed to load key:', err)
        return '0'

@app.route('/raw/<uuid>')
@cache.cached()
def decrypt(uuid: str):
    assert batch
    assert decryptor
    path = Path(f'data/{uuid}.pulse')
    
    size = path.stat().st_size
    buffer = decryptor.load_decrypted(path, size)
    return flask.Response(buffer, content_type = cbatch[uuid][0])

@app.route('/search')
def search():
    global batch, cbatch
    ext = flask.request.url.split('ext=')[1]
    sql = build_sql_filter(ext)
    print('Executing sql:', sql)
    batch = base.execute(sql).fetchall()
    cbatch = {u: (t, i, json.loads(g)) for i, (u, t, e, g) in enumerate(batch)}
    return flask.jsonify(batch)

@app.route('/get/<uuid>')
def get_file(uuid: str):
    if not batch: return flask.redirect('/?err=b')
    if not decryptor: return flask.redirect('/?err=d')
    
    ctype, index, *_ = cbatch[uuid]
    
    groups = json.loads(base.execute('SELECT groups FROM main WHERE uuid = ?', [uuid]).fetchone()[0])
    
    return flask.render_template('page.jinja',
        uuid = uuid,
        index = index,
        type = ctype,
        config = config,
        groups = groups,
        base_groups = get_groups(),
        batch_length = len(batch),
        next = ('/get/' + batch[index + 1][0]) if index + 1 < len(batch) else '#',
        prev = ('/get/' + batch[index - 1][0]) if index > 0 else '#',
        src = '/raw/' + uuid
    )

@app.route('/rand')
def randomize():
    global batch, cbatch
    assert batch
    random.shuffle(batch)
    cbatch = {u: (t, i) for i, (u, t, *_) in enumerate(batch)}
    return flask.jsonify(batch)

@app.route('/conf')
def update():
    for key, value in flask.request.args.items():
        print(f'Changing config {key} to {value}')
        config[key] = value
    
    with open('config.json', 'w') as file:
        file.write(json.dumps(config, indent = 4))
    
    return 'ok'

@app.route('/group/<uuid>')
def update_group(uuid: str):
    # Update a group
    value = json.loads(base.execute('SELECT groups FROM main WHERE uuid = ?', [uuid]).fetchone()[0])
    
    if addeable := flask.request.args.get('add'):
        value.append(addeable)
    
    if deletable := flask.request.args.get('del'):
        value.remove(deletable)
    
    print('updating', uuid, 'groups to', value)
    base.execute('UPDATE main SET groups = ? WHERE uuid = ?', (json.dumps(value), uuid))
    base.commit()
    return flask.redirect('/get/' + uuid)

if __name__ == '__main__':
    app.run( debug = True )

# EOF