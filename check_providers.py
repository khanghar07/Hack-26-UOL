"""No network: transport failures, fallback, incomplete output and private payload boundaries."""
import os
from unittest.mock import MagicMock,patch
import requests
from extraction import generate,ImportRequest,ProviderError

body=ImportRequest(transcript='Final: Catalog UI, 12 hours.',meetingDate='2026-10-07')

def response(value):
    r=MagicMock();r.json.return_value=value;return r

def router(content='{"projects":[],"issues":[]}',finish='stop'):
    return response({'choices':[{'finish_reason':finish,'message':{'content':content}}]})

settings={'AI_PROVIDER':'gemini','AI_FALLBACK_PROVIDER':'openrouter','GEMINI_API_KEY':'fake-google',
          'OPENROUTER_API_KEY':'fake-router','GEMINI_MODEL':'test-google','OPENROUTER_MODEL':'test-router'}
with patch.dict(os.environ,settings):
    failed=response({});failed.raise_for_status.side_effect=requests.HTTPError()
    session=MagicMock();session.__enter__.return_value=session
    with patch('extraction.requests.Session',return_value=session):
        session.post.side_effect=[failed,router()]
        result,provider,model=generate(body,[{'id':'DEV01','name':'Ali','role':'AGENT'}])
        assert provider=='openrouter' and model=='test-router'
        assert session.post.call_count==2
        for call in session.post.call_args_list:
            payload=str(call.kwargs['json'])
            assert 'fake-google' not in payload and 'fake-router' not in payload
            assert call.kwargs['timeout']==90
    for broken in [router(finish='length'),router(content='not json'),response({})]:
        with patch('extraction.requests.Session',return_value=session):
            session.post.side_effect=[failed,broken]
            try:generate(body,[])
            except ProviderError:pass
            else:raise AssertionError('Incomplete response must not be accepted')
with patch.dict(os.environ,{'AI_PROVIDER':'openrouter','AI_FALLBACK_PROVIDER':'','OPENROUTER_API_KEY':''}):
    with patch('extraction.requests.Session') as session:
        try:generate(body,[])
        except ProviderError:pass
        else:raise AssertionError('Missing key must fail')
        session.assert_not_called()
print('PASS: fallback, incomplete/malformed responses, bounded requests, missing credentials and secret-free model payloads.')
