import uuid
import sqlite3
from pathlib import Path
import fast_file_encryption as ffe

base = sqlite3.connect('base.db')
enc = ffe.Encryptor(ffe.read_public_key(Path('public.pem')))

base.execute('CREATE TABLE main (uuid, type, ext)')

root = Path('D:/data/')
out = Path('./data')

for file in root.glob('*'):
    
    print(file)

    uid = uuid.uuid4().hex
    
    base.execute('INSERT INTO main VALUES (?, ?, ?)', (uid, 'video/mp4', 'mp4'))
    
    enc.copy_encrypted(root / file, out / (uid + '.pulse'),
                       add_source_metadata = True)

base.commit()
base.close()