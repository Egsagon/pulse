from pathlib import Path
import fast_file_encryption as ffe

enc = ffe.Encryptor(ffe.read_public_key(Path('public.pem')))

root = Path('C:/Users/tita/watched')
output = Path('D:\pulse')

for i, file in enumerate(root.glob('*')):
    
    print(i, file)
    enc.copy_encrypted(file, output / file.name, add_source_metadata = True)

# EOF