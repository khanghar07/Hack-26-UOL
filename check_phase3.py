import copy, json, os, tempfile, sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app, current_user
from storage import initialize, database
from directory import PEOPLE
from extraction import generate, validate, ImportRequest, ProviderError, save, Correction

with tempfile.TemporaryDirectory() as folder:
    os.environ['DATABASE_URL'] = ''  # Always isolate regression fixtures from hosted data.
    os.environ['DATABASE_PATH']=folder+'/test.db'
    initialize()
    with database() as db:
        db.executemany('INSERT INTO users VALUES(?,?,?,?,?,?)',[(u,n,n+'@test',r,s,json.dumps(k)) for u,n,r,s,k in PEOPLE])
        directory=[dict(r) for r in db.execute('SELECT * FROM users')]
    raw={'projects':[{'name':'Demo','clientName':'Client','description':'Scope','managerId':'PM01','deadline':'2026-10-24','tasks':[{'title':'Integration','description':'Connect UI','assigneeId':'DEV04','deadline':'2026-10-22','estimatedHours':10}]}],'issues':[]}
    body={'transcript':'Final agreement: Integration 10 hours','meetingDate':'2026-10-07'}
    app.dependency_overrides[current_user]=lambda:{'id':'ADMIN','role':'ADMIN'}
    with TestClient(app) as client:
        with patch('main.generate',return_value=(raw,'fixture','test')) as mock:
            assert client.post('/api/transcript',json=body).status_code==200
            assert client.post('/api/transcript',json=body).json()['replayed']
            assert mock.call_count==1
        for field,value in [('assigneeId','PM01'),('deadline','2026-10-25'),('estimatedHours',-1),('estimatedHours',None),('estimatedHours',14)]:
            bad=copy.deepcopy(raw);bad['projects'][0]['tasks'][0][field]=value
            with patch('main.generate',return_value=(bad,'fixture','test')):
                assert client.post('/api/transcript',json={**body,'transcript':body['transcript']+str((field,value))}).status_code==422
        with patch('main.generate',side_effect=ProviderError('Unavailable')):
            assert client.post('/api/transcript',json={**body,'transcript':'Failure'}).status_code==503
        assert client.post('/api/transcript',json={**body,'transcript':'   '}).status_code==422
        app.dependency_overrides[current_user]=lambda:{'id':'DEV01','role':'AGENT'}
        with patch('main.generate') as mock:
            assert client.post('/api/transcript',json=body).status_code==403
            mock.assert_not_called()
        with database() as db:
            db.execute("CREATE TRIGGER reject_extra BEFORE INSERT ON projects WHEN (SELECT count(*) FROM projects)>1 BEGIN SELECT RAISE(ABORT, 'rollback'); END")
        from datetime import date
        parsed=validate(raw,directory,date(2026,10,7),body['transcript']);parsed.projects.append(copy.deepcopy(parsed.projects[0]))
        try: save(parsed,'rollback','fixture','test')
        except Correction: pass
        else: raise AssertionError('Expected rollback')
        with database() as db:
            for table in ['projects','tasks','transcript_imports']:
                assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==1
    app.dependency_overrides.clear()
    print('PASS isolated: admin authorization, invalid owner/date/hours, provider failure, replay, rollback.')
    if '--live' in sys.argv:
        transcript=Path('sample_transcript.txt').read_text()
        modified=transcript.replace('10 hours. Keep the task deadline at 22 October','12 hours. Keep the task deadline at 23 October').replace('Usman, 10 hours, 22 October','Usman, 12 hours, 23 October').replace('10 hours, 22 October.','12 hours, 23 October.')
        for label,text in [('original',transcript),('modified',modified)]:
            request=ImportRequest(transcript=text,meetingDate='2026-10-07')
            output,provider,model=generate(request,directory)
            parsed=validate(output,directory,request.meetingDate,request.transcript)
            assert len(parsed.projects)==3 and sum(len(p.tasks) for p in parsed.projects)==12
            totals={p.name:sum(t.estimatedHours for t in p.tasks) for p in parsed.projects}
            assert totals=={'UrbanCart Website':40,'QuickServe Mobile App':48 if label=='modified' else 46,'HelpDeskPro AI Assistant':38},totals
            tasks=[t for p in parsed.projects for t in p.tasks]
            usman=next(t for t in tasks if t.assigneeId=='DEV04')
            assert usman.estimatedHours==(12 if label=='modified' else 10)
            assert usman.deadline.isoformat()==('2026-10-23' if label=='modified' else '2026-10-22')
            web=next(p for p in parsed.projects if p.name=='UrbanCart Website')
            assert web.deadline.isoformat()=='2026-10-20'
            assert next(t for t in web.tasks if 'integration' in t.title.lower()).deadline.isoformat()=='2026-10-19'
            assert next(t for t in tasks if 'evaluation' in t.title.lower()).assigneeId=='DEV06'
            print('PASS live',label,provider,model,totals,flush=True)

        missing=ImportRequest(meetingDate='2026-10-07',transcript='Final agreement: client Acme needs a website called Acme Site. Ayesha Khan manages it, delivery 24 October 2026. Ali Raza owns the catalog UI task, due 12 October 2026. Scope: product listing. The team never agreed any estimated hours. No other tasks.')
        output,provider,model=generate(missing,directory)
        try: validate(output,directory,missing.meetingDate,missing.transcript)
        except Correction as exc:
            assert exc.issues
            print('PASS live missing estimate: correction requested; nothing saved.',flush=True)
        else: raise AssertionError('Missing hours must request correction')
