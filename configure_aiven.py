"""Save a private Aiven connection in the local .env after a successful TLS check."""
import getpass
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import psycopg
from dotenv import set_key

def main():
    uri = getpass.getpass('Paste the Aiven PostgreSQL service URI (hidden): ').strip()
    parsed = urlparse(uri)
    if parsed.scheme not in {'postgres', 'postgresql'} or not parsed.hostname or not parsed.hostname.endswith('.aivencloud.com'):
        raise SystemExit('Expected the PostgreSQL service URI from your Aiven console.')
    if parse_qs(parsed.query).get('sslmode', [''])[0] not in {'require','verify-ca','verify-full'}:
        raise SystemExit('Use the Aiven TLS connection URI.')
    try:
        with psycopg.connect(uri, connect_timeout=10) as db:
            if not db.execute('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()').fetchone()[0]:
                raise SystemExit('TLS check failed.')
    except psycopg.Error:
        raise SystemExit('Connection failed. Check the service status, hostname, network access and password. Existing configuration preserved.')
    path = Path(__file__).resolve().with_name('.env')
    if not path.exists():
        raise SystemExit('Copy .env.example to .env first.')
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as tmp:
        tmp.write(path.read_bytes())
    try:
        set_key(tmp.name, 'DATABASE_URL', uri)
        os.replace(tmp.name,path)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    print('TLS verified and DATABASE_URL configured privately. Now run python seed.py.')

if __name__ == '__main__':
    main()
