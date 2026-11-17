"""Full Section 7 -> real AI -> saved database -> all ten Firebase sessions."""
import json,os,tempfile
from pathlib import Path
from unittest.mock import patch
import requests
from fastapi.testclient import TestClient
from main import app
from directory import email_for,password_for
from seed import seed
from storage import database

if os.getenv('FIREBASE_AUTH_EMULATOR_HOST')!='127.0.0.1:9099' or os.getenv('FIREBASE_PROJECT_ID')!='demo-novaworks':
    raise SystemExit('Use the demo Firebase emulator only.')
fixture=json.loads(Path('expected_meeting.json').read_text())
body={'transcript':Path('sample_transcript.txt').read_text(),'meetingDate':'2026-10-07'}
with tempfile.TemporaryDirectory() as folder:
    os.environ['DATABASE_URL'] = ''  # Always isolate regression fixtures from hosted data.
    os.environ['DATABASE_PATH']=folder+'/full.db'
    seed()
    headers={}
    for name in fixture['EXPECTED']:
        r=requests.post('http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo',json={
            'email':email_for(name),'password':password_for(name),'returnSecureToken':True},timeout=10)
        r.raise_for_status();headers[name]={'Authorization':'Bearer '+r.json()['idToken']}
    with TestClient(app) as client:
        response=client.post('/api/transcript',headers=headers['admin'],json=body)
        assert response.status_code==200,response.text
        result=response.json()
        assert result['projectCount']==3 and result['taskCount']==12 and not result['replayed']
        # Exact expected projects and all 12 task assignments, estimates and dates.
        with database() as db:
            actual_projects={r['name']:dict(r) for r in db.execute('SELECT * FROM projects')}
            actual_tasks={r['title']:dict(r) for r in db.execute('SELECT * FROM tasks')}
        short_ids={}
        for short,name,client_name,_,manager,deadline in fixture['PROJECTS']:
            p=actual_projects[name];short_ids[short]=p['id']
            assert (p['clientName'],p['managerId'],p['deadline'])==(client_name,manager,deadline)
        for _,project,title,_,owner,deadline,hours in fixture['TASKS']:
            t=actual_tasks[title]
            assert (t['projectId'],t['assigneeId'],t['deadline'],t['estimatedHours'])==(short_ids[project],owner,deadline,hours),title
        for name,expected in fixture['EXPECTED'].items():
            projects=client.get('/api/projects',headers=headers[name]).json()['projects']
            assert {p['id']:p['taskCount'] for p in projects}=={short_ids[k]:v for k,v in expected.items()},name
            uid=client.get('/api/me',headers=headers[name]).json()['id']
            for p in projects:
                detail=client.get('/api/projects/'+p['id'],headers=headers[name]).json()
                assert detail==p
                if name in {'ali','hamza','sara','usman','zain','maryam'}:
                    assert all(t['assigneeId']==uid for t in p['tasks'])
            for denied in set(short_ids)-set(expected):
                assert client.get('/api/projects/'+short_ids[denied],headers=headers[name]).status_code==404
        with patch('main.generate',side_effect=AssertionError('Replay must not call AI')):
            repeat=client.post('/api/transcript',headers=headers['admin'],json=body)
            assert repeat.status_code==200 and repeat.json()['replayed']
    with TestClient(app) as restarted:
        assert len(restarted.get('/api/tasks/mine',headers=headers['hamza']).json()['tasks'])==2
    print('PASS FULL LIVE FLOW:',result['provider'],result['model'],'3 exact projects / 12 exact tasks; all 10 identities, role reads, replay, restart.',flush=True)
