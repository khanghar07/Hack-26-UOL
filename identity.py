import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from dotenv import load_dotenv

load_dotenv()
project = os.environ['FIREBASE_PROJECT_ID']
host = os.getenv('FIREBASE_AUTH_EMULATOR_HOST')
if host and (not project.startswith('demo-') or host.split(':')[0] not in {'localhost','127.0.0.1'}):
    raise RuntimeError('Use a demo- project and loopback host for local emulation.')

class BackendNotConfigured(Exception):
    pass

# Hosted mode never searches for ambient credentials or a cloud metadata server.
# Only the operator's explicitly supplied service-account file is accepted.
credential_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if host:
    app = firebase_admin.initialize_app(options={'projectId': project})
elif credential_path or os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'):
    cert = credentials.Certificate(credential_path or json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT_JSON']))
    if cert.project_id != project:
        raise RuntimeError('Firebase credential file and FIREBASE_PROJECT_ID must match.')
    app = firebase_admin.initialize_app(cert, options={'projectId': project})
else:
    app = None

def require_configured():
    if app is None:
        raise BackendNotConfigured('Set GOOGLE_APPLICATION_CREDENTIALS to the private Firebase service-account file on the backend.')

def verify(token):
    require_configured()
    return auth.verify_id_token(token, app=app, check_revoked=True)['uid']
