import os, tempfile
from fastapi.testclient import TestClient

os.environ['DATA_FILE']=os.path.join(tempfile.gettempdir(),'flyrank-capstone-test.json')
try: os.remove(os.environ['DATA_FILE'])
except FileNotFoundError: pass
from app.main import app, DB, LIMITS
DB.clear(); DB.update({'tenants':[], 'widgets':[], 'submissions':[], 'users':[{'tenant_id':'A','token':'token-a'},{'tenant_id':'B','token':'token-b'}]})
LIMITS.clear()
client=TestClient(app)
H=lambda t:{'Authorization':f'Bearer {t}'}

def make(t='token-a'):
    r=client.post('/widgets',headers=H(t),json={'type':'signup','title':'Demo','description':'Lead','form_fields':['name','email'],'button_text':'Join','allowed_origins':['*']})
    assert r.status_code==201; return r.json()['id']

def submit(wid, **kw):
    body={'widget_id':wid,'data':{'name':'A','email':'a@x.com'},'hp':''}; body.update(kw)
    return client.post('/submissions',headers={'Origin':'http://localhost:5500'},json=body)

def test_auth_crud_and_tenant_isolation():
    assert client.get('/widgets').status_code==401
    wid=make(); assert client.get('/widgets',headers=H('token-a')).json()[0]['id']==wid
    assert client.get(f'/widgets/{wid}',headers=H('token-b')).status_code==404
    r=client.put(f'/widgets/{wid}',headers=H('token-a'),json={'type':'cta','title':'Updated','description':'x','form_fields':['name'],'button_text':'Go','allowed_origins':['*']})
    assert r.status_code==200 and r.json()['version']==2
    assert client.delete(f'/widgets/{wid}',headers=H('token-b')).status_code==404
    assert client.delete(f'/widgets/{wid}',headers=H('token-a')).status_code==200

def test_config_embed_and_versioned_bundle():
    wid=make(); r=client.get(f'/widgets/{wid}/embed',headers=H('token-a')); assert r.status_code==200 and 'widget.v1.js' in r.json()['snippet']
    r=client.get(f'/widgets/{wid}/config'); assert r.status_code==200 and 'max-age=60' in r.headers['cache-control']
    r=client.get(f'/widget.v1.js?id={wid}'); assert r.status_code==200 and 'immutable' in r.headers['cache-control']

def test_cors_validation_oversize_and_honeypot():
    wid=make()
    r=client.options('/submissions',headers={'Origin':'http://localhost:5500','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
    assert r.status_code in (200, 204) and r.headers['access-control-allow-origin']=='*'
    assert submit(wid, data={'name':'A'}).status_code==422
    assert submit(wid, hp='bot').status_code==400
    assert submit(wid, data={'name':'A','email':'x','extra':'x'*11000}).status_code==413
    assert submit(wid).status_code==201

def test_rate_limit_returns_429():
    wid=make()
    for _ in range(20): assert submit(wid).status_code==201
    assert submit(wid).status_code==429

def test_geo_fallback_and_all_down_still_succeeds():
    wid=make(); os.environ['GEO_PROVIDER_A_DOWN']='1'
    try:
        r=submit(wid); assert r.status_code==201
        row=client.get('/dashboard/submissions',headers=H('token-a')).json()[-1]; assert row['geo']['provider']=='B'
        os.environ['GEO_PROVIDER_B_DOWN']='1'
        r=submit(wid); assert r.status_code==201
        row=client.get('/dashboard/submissions',headers=H('token-a')).json()[-1]; assert row['geo']['provider'] is None
    finally:
        os.environ.pop('GEO_PROVIDER_A_DOWN',None); os.environ.pop('GEO_PROVIDER_B_DOWN',None)

def test_side_effect_failure_does_not_block_and_dashboard_is_tenant_scoped():
    wid=make(); os.environ['SIDE_EFFECT_DOWN']='1'
    try: assert submit(wid).status_code==201
    finally: os.environ.pop('SIDE_EFFECT_DOWN',None)
    assert client.get('/dashboard/stats',headers=H('token-a')).status_code==200
    assert client.get('/dashboard/stats',headers=H('token-b')).json()['total_submissions']==0
