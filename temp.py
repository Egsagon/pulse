from pathlib import Path
import fast_file_encryption as ffe

dec = ffe.Decryptor(ffe.read_private_key(Path('private.pem')))
enc = ffe.Encryptor(ffe.read_public_key(Path('public.pem')))

dec.copy_decrypted(Path('encrypted.mp4'), Path('resolved.mp4'))
