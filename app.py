import flask
import sqlite3
from pathlib import Path
import fast_file_encryption as ffe

app = flask.Flask(__name__, static_folder = 'client', template_folder = 'client')
batch: list[tuple[str, str]] = None
cbatch: dict[str, tuple[str, int]] = None
decryptor: ffe.Decryptor = None

@app.route('/')
def home():
    # Send the home page
    return flask.send_file('client/index.html')

@app.route('/key', methods = ['POST'])
def load_key():
    # Load decryptor wih private key
    global decryptor
    raw = flask.request.get_data(False, True)
    key = ffe.read_private_key(raw)
    decryptor = ffe.Decryptor(key)
    return 'ok'

@app.route('/haskey')
def has_key():
    # Check if key is loaded
    return str(int(bool(decryptor)))

@app.route('/raw/<uuid>')
def decrypt(uuid: str):
    # Decrypt a file, used by client DOM video or img
    assert batch
    assert decryptor
    path = Path(f'data/{uuid}.pulse')
    size = path.stat().st_size
    meta = decryptor.read_metadata(path)
    buffer = decryptor.load_decrypted(path, size)
    return flask.Response(buffer, content_type = cbatch[uuid][0])

@app.route('/search')
def search():
    # Search for files
    global batch, cbatch
    base = sqlite3.connect('base.db')
    ctype = flask.request.args.get('ct')
    
    if ctype: batch = base.execute('SELECT * FROM main WHERE type = ?', [ctype]).fetchall()
    else:     batch = base.execute('SELECT * FROM main').fetchall()
    
    cbatch = {u: (t, i) for i, (u, t, e) in enumerate(batch)}
    base.close()
    return flask.jsonify(batch)

@app.route('/get/<uuid>')
def get_file(uuid: str):
    # Load a file page
    assert batch
    assert decryptor
    
    ctype, index = cbatch[uuid]
    tag = 'video' if 'video' in ctype else 'img'
    
    return flask.render_template('page.html',
        uuid = uuid,
        type = ctype,
        next = ('/get/' + batch[index + 1][0]) if index + 1 < len(batch) else '#',
        prev = ('/get/' + batch[index - 1][0]) if index > 0 else '#',
        content = f'<{tag} src="/raw/{uuid}"></{tag}>'
    )

if __name__ == '__main__':
    app.run(debug = True)

# EOF