import json, os
from pathlib import Path

path=Path(os.getenv('DATA_FILE','data.json'))
data={
 'tenants':[{'id':'tenant-a','name':'Acme A'},{'id':'tenant-b','name':'Acme B'}],
 'users':[{'tenant_id':'tenant-a','token':'demo-token-a'},{'tenant_id':'tenant-b','token':'demo-token-b'}],
 'widgets':[{'id':'demo-widget','tenant_id':'tenant-a','type':'signup','title':'Join Acme','description':'Get product updates','form_fields':['name','email'],'button_text':'Subscribe','display_options':{},'allowed_origins':['http://localhost:5500'],'version':1,'created_at':'2026-09-10T00:00:00+00:00','updated_at':'2026-09-10T00:00:00+00:00'}],
 'submissions':[]
}
path.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(f'Seeded {path} with tenant-a, tenant-b and demo-widget')
print('Tenant A token: demo-token-a')
print('Tenant B token: demo-token-b')
