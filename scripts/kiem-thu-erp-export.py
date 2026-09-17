"""Đo xuất toàn kỳ trên server kiểm thử; không ghi dữ liệu nghiệp vụ."""
import json,re,time
from io import BytesIO
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlencode
from http.cookiejar import CookieJar
from openpyxl import load_workbook

BASE='http://127.0.0.1:8135'
client=build_opener(HTTPCookieProcessor(CookieJar()))
page=client.open(BASE+'/dang-nhap/',timeout=10)
token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page.read().decode())[1]
logged=client.open(Request(BASE+'/dang-nhap/',data=urlencode({'username':'erp_admin','password':'erp-test-only-2026','csrfmiddlewaretoken':token}).encode(),headers={'Referer':BASE+'/dang-nhap/'}),timeout=10)
assert logged.geturl()==BASE+'/'
results=[]
for source,groups in [('bao_cao_mkt',1500),('bao_cao_sale',1500),('van_don_moi',2000)]:
 start=time.perf_counter()
 response=client.open(BASE+'/bao-cao/hoat-dong/xuat/?'+urlencode({'nguon':source,'tu':'2020-01-01','den':'2025-12-31'}),timeout=30)
 content=response.read()
 elapsed=round((time.perf_counter()-start)*1000,2)
 assert response.status==200
 book=load_workbook(BytesIO(content),data_only=True)
 rows=list(book.active.values)
 assert len(rows)-5==groups
 totals=dict(zip(rows[3][1:],rows[-1][1:]))
 if source=='van_don_moi':
  assert totals=={'Số đơn':40000,'Số lượng sản phẩm':120000}
  assert sum(r[1] for r in list(book.worksheets[1].values)[1:])==40000
 else:
  assert totals['Số Mess']==3000000 and totals['Số đơn']==150000 and totals['Doanh số']==30000000
  assert totals['Doanh thu'] is None
 output=Path('storage/erp-verification')/(source+'-full.xlsx')
 output.write_bytes(content)
 results.append({'source':source,'groups':groups,'milliseconds':elapsed,'bytes':len(content),'passed':True})
Path('storage/erp-verification/export-large.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
