"""HTTPS/request ID trên proxy test; không dùng chứng chỉ hoặc phiên thật."""
import json
import os
import re
from pathlib import Path
import requests
import urllib3

m=json.loads(Path(os.environ['OPT_MANIFEST']).read_text())
assert m['database']=='test_knjsc_opt_after100'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
client=requests.Session();client.cookies['sessionid']=m['actors'][0]['session']
results=[]
for value in ['a'*32,'invalid-request-id']:
    response=client.get('https://crm-opt-proxy:18443/bang-tinh/van_don_moi/du-lieu/',
        params={'protocol':2,'f_ma_don':m['actors'][0]['code']},headers={'Host':'crm.test.invalid','X-Request-ID':value},verify=False,timeout=10)
    assert response.status_code==200
    request_id=response.headers['X-Request-ID']
    assert re.fullmatch('[0-9a-fA-F]{32}',request_id)
    assert (request_id==value)==(value=='a'*32)
    assert [row['id'] for row in response.json()['rows']]==[m['actors'][0]['row']]
    results.append({'status':response.status_code,'request_id':request_id})
Path('/runtime/proxy-probe.json').write_text(json.dumps(results))
print('PASS HTTPS test, mã request hợp lệ được giữ, mã không hợp lệ được thay.')
