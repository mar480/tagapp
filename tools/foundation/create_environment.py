"""Generate local Compose secrets without printing or overwriting them."""
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[2]

def main():
    directory = ROOT / '.local/foundation'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / 'compose.env'
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print('Environment already exists; unchanged.')
        return
    with os.fdopen(fd, 'w') as stream:
        for key in ('TAGGER_SECRET_KEY', 'POSTGRES_PASSWORD', 'RABBITMQ_PASSWORD'):
            stream.write(key + '=' + secrets.token_hex(32) + '\n')
    print('Created .local/foundation/compose.env (mode 600); values were not printed.')

if __name__ == '__main__':
    main()
