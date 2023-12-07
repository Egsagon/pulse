import json
import flask
import random
import sqlite3
from pathlib import Path
from flask_caching import Cache
import fast_file_encryption as ffe

decryptor: ffe.Decryptor = None
app = flask.Flask(__name__, static_folder = 'client', template_folder = 'client')

batch: list[tuple[str, str]] = None
cbatch: dict[str, tuple[str, int]] = None

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

@app.route('/')
def home():
    base = sqlite3.connect('base.db')
    types = base.execute('SELECT DISTINCT ext FROM main').fetchall()
    base.close()
    
    error = '?err=' in flask.request.url
    
    return flask.render_template('index.jinja',
        haskey = bool(decryptor),
        types = list(set(types)),
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
    base = sqlite3.connect('base.db')
    e = flask.request.args.get('ext')
    
    if e: batch = base.execute('SELECT * FROM main WHERE ext = ?', [e]).fetchall()
    else: batch = base.execute('SELECT * FROM main').fetchall()
    
    cbatch = {u: (t, i) for i, (u, t, e) in enumerate(batch)}
    base.close()
    return flask.jsonify(batch)

@app.route('/get/<uuid>')
def get_file(uuid: str):
    if not batch: return flask.redirect('/?err=b')
    if not decryptor: return flask.redirect('/?err=d')
    
    ctype, index = cbatch[uuid]
    
    return flask.render_template('page.jinja',
        uuid = uuid,
        type = ctype,
        config = config,
        next = ('/get/' + batch[index + 1][0]) if index + 1 < len(batch) else '#',
        prev = ('/get/' + batch[index - 1][0]) if index > 0 else '#',
        src = '/raw/' + uuid
    )

@app.route('/rand')
def randomize():
    global batch, cbatch
    assert batch
    random.shuffle(batch)
    cbatch = {u: (t, i) for i, (u, t, e) in enumerate(batch)}
    return flask.jsonify(batch)

@app.route('/conf')
def update():
    for key, value in flask.request.args.items():
        print(f'Changing config {key} to {value}')
        config[key] = value
    
    with open('config.json', 'w') as file:
        file.write(json.dumps(config, indent = 4))
    
    return 'ok'

if __name__ == '__main__':
    app.run( debug = True )

# EOF