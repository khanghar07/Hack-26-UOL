"""Real emulator tokens exercise import authorization, revocation and custom admin identity."""
import os, tempfile, json, time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import requests
from fastapi.testclient import TestClient
from firebase_admin import auth
from main import app
from seed import seed
from directory import PEOPLE,email_for,password_for
from storage import database
from extraction import validate,save
from datetime import date

if os.getenv('FIREBASE_AUTH_EMULATOR_HOST')!='127.0.0.1:9099' or os.getenv('FIREBASE_PROJECT_ID')!='demo-novaworks':
    raise SystemExit('Run via the local demo emulator only.')

def token(name):
    r=requests.post('http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo',
        json={'email':email_for(name),'password':password_for(name),'returnSecureToken':True},timeout=10)
    r.raise_for_status()
    return {'Authorization':'Bearer '+r.json()['idToken']}

with tempfile.TemporaryDirectory() as folder:
    os.environ['DATABASE_URL'] = ''  # Always isolate regression fixtures from hosted data.
    os.environ['DATABASE_PATH']=folder+'/security.db'
    seed()
    body={'meetingDate':'2026-10-07','transcript':'API task estimate: 14 hours.'}
    raw={'projects':[{'name':'Secure demo','clientName':'Client','description':'Scope','managerId':'PM01',
         'deadline':'2026-10-24','tasks':[{'title':'API','description':'API endpoint','assigneeId':'DEV02',
         'deadline':'2026-10-14','estimatedHours':14}]}],'issues':[]}
    with TestClient(app) as client:
        assert client.post('/api/transcript',json=body).status_code==401
        assert client.post('/api/transcript',json=body,headers={'Authorization':'Bearer invalid'}).status_code==401
        for uid,name,role,*_ in PEOPLE:
            h=token(name)
            if role!='ADMIN':
                with patch('main.generate') as call:
                    assert client.post('/api/transcript?role=ADMIN',json=body,headers=h).status_code==403
                    call.assert_not_called()
        admin=token('Admin')
        with patch('main.generate',return_value=(raw,'fixture','test')):
            r=client.post('/api/transcript',json=body,headers=admin)
            assert r.status_code==200,r.text
        pid=r.json()['projectIds'][0]
        assert client.get('/api/projects/'+pid,headers=token('Ayesha Khan')).json()['taskCount']==1
        assert client.get('/api/projects/'+pid,headers=token('Hamza Shah')).json()['taskCount']==1
        assert client.get('/api/projects/'+pid,headers=token('Ali Raza')).status_code==404
        # Concurrent saves must commit exactly one import, including its tasks.
        with database() as db:
            directory=[dict(u) for u in db.execute('SELECT * FROM users')]
        parsed=validate(raw,directory,date(2026,10,7),body['transcript'])
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:save(parsed,'concurrent','fixture','test'),range(4)))
        assert sum(not r['replayed'] for r in results)==1
        assert len({tuple(r['projectIds']) for r in results})==1
        with database() as db:
            assert db.execute('SELECT count(*) FROM projects').fetchone()[0]==2
            assert db.execute('SELECT count(*) FROM tasks').fetchone()[0]==2
        # Browser preflight: only the configured frontend origin can POST.
        headers={'Origin':os.getenv('FRONTEND_ORIGIN','http://localhost:5173'),'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'}
        assert client.options('/api/transcript',headers=headers).status_code==200
        assert client.options('/api/transcript',headers={**headers,'Origin':'https://untrusted.example'}).status_code==400
        disabled=token('Ali Raza');auth.update_user('DEV01',disabled=True)
        assert client.get('/api/me',headers=disabled).status_code==401
        auth.update_user('DEV01',disabled=False)
        revoked=token('Hamza Shah');time.sleep(1.1);auth.revoke_refresh_tokens('DEV02')
        assert client.get('/api/me',headers=revoked).status_code==401
        # Web-created account may use a generated UID; seeder must keep that UID.
        auth.delete_user('ADMIN')
        custom=auth.create_user(email=email_for('Admin'),password=password_for('Admin'))
        seed();seed()
        h=token('Admin');me=client.get('/api/me',headers=h)
        assert me.status_code==200,me.text
        assert me.json()['id']==custom.uid and me.json()['role']=='ADMIN'
        with database() as db:
            assert db.execute('SELECT count(*) FROM users').fetchone()[0]==10
            assert db.execute("SELECT count(*) FROM users WHERE role='ADMIN'").fetchone()[0]==1
        assert len(list(auth.list_users().iterate_all()))==10
print('PASS: real tokens, admin import, 9 role denials, project isolation, concurrent replay, CORS, disabled/revoked tokens, existing-admin UID, repeat seed.')
