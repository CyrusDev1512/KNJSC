"""Chỉ cho bài bền sau so sánh: đưa timestamp synthetic tương lai về quá khứ."""
import json
from pathlib import Path
import django
django.setup()
from django.db import connection

assert connection.settings_dict['HOST']=='knjsc-crm-update-db'
assert connection.settings_dict['NAME']=='test_crm_update_load_300000'
with connection.cursor() as cursor:
    assert not connection.in_atomic_block
    cursor.execute('SELECT table_id,max(id) FROM forms_builder_datarecord GROUP BY table_id')
    bounds=cursor.fetchall()
    changed=0
    for table_id,last_id in bounds:
        while True:
            # Chia lô để không giữ một transaction cập nhật gần một triệu dòng.
            cursor.execute('''WITH batch AS (
              SELECT id FROM forms_builder_datarecord
              WHERE table_id=%s AND created_at>NOW() ORDER BY id LIMIT 10000
            ) UPDATE forms_builder_datarecord r
              SET created_at=NOW()-(%s-r.id)*interval '1 second',
                  updated_at=NOW()-(%s-r.id)*interval '1 second'
              FROM batch b WHERE r.id=b.id''', [table_id,last_id,last_id])
            batch_size=cursor.rowcount
            changed+=batch_size
            if not batch_size:break
        # Container test có /dev/shm nhỏ; bảo trì tuần tự không dùng DSM
        # của parallel VACUUM. Không thay cấu hình truy vấn ứng dụng.
        cursor.execute('VACUUM (ANALYZE, PARALLEL 0) forms_builder_datarecord')
    cursor.execute('ANALYZE forms_builder_datarecord')
    cursor.execute('SELECT count(*) FROM forms_builder_datarecord WHERE updated_at>NOW()')
    future=cursor.fetchone()[0]
assert future==0
result={'corrected_timestamps':changed,'future_remaining':future,'scope':'Chỉ bài bền, sau tất cả phép so sánh before/after'}
Path('/runtime/time-normalization.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
