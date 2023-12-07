# PULSE
A small webpp that can display encrypted medias in your browser.

## Running
1. Clone the repository and install dependencies:
```sh
git clone https://github.com/Egsagon/pulse/
pip install -r pulse/requirements.txt
```
2. Generate a new AES key pair (e.g.with FFE):
```py
form pathlib import Path
import fast_file_encryption as ffe

ffe.save_key_pair(
  public_key = Path('public.pem'),
  private_key = Path('private.pem')
)
```
2. Prepare for encryption. Remux videos if needed (browsers are stricter than normal players):
```sh
mkdir pulse/data/
```
```sh
# For each video file
ffmpeg -i video.mp4 -c copy remuxed_video.mp4
```
4. Encrypt your files in the `pulse/data/` directory and register them in a database:
```py
import uuid
import sqlite3
import mimetypes
from pathlib import Path
import fast_file_encryption as ffe

ENCRYPTION_KEY = './public.pem'
INPUT = Path('path/to/your/files')
OUTPUT = Path('pulse/data')

BASE = sqlite3.connect('pulse/base.db')
BASE.execute('CREATE TABLE IF NOT EXISTS main (uuid, type, ext)')

encryptor = ffe.Encryptor(ffe.read_public_key(Path(ENCRYPTION_KEY)))

for file in INPUT.glob('*')
  fid = uuid.uuid4().hex
  ext = file.split('.')[-1]
  mime = mimetypes.types_map[ '.' + ext ]
  BASE.execute('INSERT INTO main VALUES (?, ?, ?)', (fid, mime, ext))
  encryptor.copy_encrypted( file, OUTPUT / fid + '.pulse' )

BASE.commit()
BASE.close()
```

4. Run the server:
```sh
py -m flask run
```

5. Naviguate your browser to 127.0.0.1:5000.

## License

Pulse uses a GPLv3 license. Refer to the `LICENSE` file.
