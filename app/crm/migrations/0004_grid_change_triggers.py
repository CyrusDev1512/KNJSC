"""Thu metadata bằng statement trigger; cấp revision tại commit, sau ghi nghiệp vụ.

Không đưa giá trị JSON của khách vào journal. Transition tables bao phủ bulk SQL,
service lồng và admin; deferred trigger gom một revision/bảng/giao dịch.
"""
from django.db import migrations

SQL = r"""
CREATE FUNCTION crm_grid_flush() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t bigint; rev bigint; ids jsonb; cols jsonb; needs_reset boolean;
BEGIN
 FOR t IN SELECT DISTINCT table_id FROM crm_gridpendingchange WHERE transaction_id=txid_current() ORDER BY table_id LOOP
  IF NOT EXISTS(SELECT 1 FROM forms_builder_tabledef WHERE id=t) THEN CONTINUE; END IF;
  INSERT INTO crm_gridrevision(table_id,revision,fields) VALUES(t,0,'{}') ON CONFLICT DO NOTHING;
  SELECT revision+1 INTO rev FROM crm_gridrevision WHERE table_id=t FOR UPDATE;
  SELECT coalesce(jsonb_agg(v),'[]') INTO ids FROM
    (SELECT DISTINCT v FROM crm_gridpendingchange p CROSS JOIN LATERAL jsonb_array_elements(p.record_ids) v
     WHERE p.transaction_id=txid_current() AND p.table_id=t LIMIT 2001) q;
  SELECT coalesce(jsonb_agg(v),'[]') INTO cols FROM
    (SELECT DISTINCT v FROM crm_gridpendingchange p CROSS JOIN LATERAL jsonb_array_elements(p.columns) v
     WHERE p.transaction_id=txid_current() AND p.table_id=t) q;
  SELECT bool_or(reset) OR jsonb_array_length(ids)>2000 INTO needs_reset FROM crm_gridpendingchange WHERE transaction_id=txid_current() AND table_id=t;
  IF needs_reset THEN ids='[]'; END IF;
  UPDATE crm_gridrevision SET revision=rev, fields=fields || coalesce((SELECT jsonb_object_agg(v,rev) FROM jsonb_array_elements_text(cols) v),'{}') WHERE table_id=t;
  INSERT INTO crm_gridchange(table_id,revision,record_ids,columns,reset) VALUES(t,rev,ids,cols,needs_reset);
  DELETE FROM crm_gridchange WHERE table_id=t AND revision<=rev-10000;
 END LOOP;
 DELETE FROM crm_gridpendingchange WHERE transaction_id=txid_current();
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER crm_grid_commit AFTER INSERT ON crm_gridpendingchange
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION crm_grid_flush();

CREATE FUNCTION crm_grid_capture() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t bigint; ids jsonb; cols jsonb; reset_needed boolean; source_sql text;
BEGIN
 IF TG_TABLE_NAME='forms_builder_datarecord' THEN
  IF TG_OP='UPDATE' THEN
   source_sql='SELECT n.table_id,n.id, CASE WHEN n.table_id<>o.table_id OR (n.deleted_at,n.created_by_id,n.department_id,n.team_id,n.created_at) IS DISTINCT FROM (o.deleted_at,o.created_by_id,o.department_id,o.team_id,o.created_at) OR (n.data=o.data AND (to_jsonb(n)-''data''-''style''-''updated_at'') IS DISTINCT FROM (to_jsonb(o)-''data''-''style''-''updated_at'')) THEN ''["__membership","__access"]''::jsonb ELSE ''[]''::jsonb END || coalesce((SELECT jsonb_agg(k) FROM (SELECT jsonb_object_keys(n.data) k UNION SELECT jsonb_object_keys(o.data) k) keys WHERE n.data->k IS DISTINCT FROM o.data->k),''[]'') || CASE WHEN n.style IS DISTINCT FROM o.style THEN ''["__style"]''::jsonb ELSE ''[]''::jsonb END AS cols FROM new_rows n JOIN old_rows o USING(id) UNION ALL SELECT o.table_id,o.id,''["__membership","__access"]''::jsonb FROM old_rows o JOIN new_rows n USING(id) WHERE o.table_id<>n.table_id';
  ELSIF TG_OP='INSERT' THEN source_sql='SELECT table_id,id,''["__membership"]''::jsonb cols FROM new_rows';
  ELSE source_sql='SELECT table_id,id,''["__membership","__access"]''::jsonb cols FROM old_rows'; END IF;
 ELSIF TG_TABLE_NAME IN ('orders_waybillitem','orders_waybillassignment') THEN
  source_sql=format('SELECT r.table_id,r.id,%L::jsonb cols FROM %s n JOIN forms_builder_datarecord r ON r.id=n.record_id',
   CASE WHEN TG_TABLE_NAME='orders_waybillassignment' THEN '["__membership","__access","phu_trach_van_don","phu_trach_cskh","marketing"]' ELSE '["__items","san_pham"]' END,
   CASE WHEN TG_OP='DELETE' THEN 'old_rows' WHEN TG_OP='UPDATE' THEN '(SELECT record_id FROM new_rows UNION SELECT record_id FROM old_rows)' ELSE 'new_rows' END);
 ELSIF TG_TABLE_NAME='orders_order' THEN
  source_sql=format('SELECT r.table_id,r.id,''["__membership","__access"]''::jsonb cols FROM %s n JOIN forms_builder_datarecord r ON r.id=n.record_id',CASE WHEN TG_OP='DELETE' THEN 'old_rows' WHEN TG_OP='UPDATE' THEN '(SELECT record_id FROM new_rows UNION SELECT record_id FROM old_rows)' ELSE 'new_rows' END);
 ELSIF TG_TABLE_NAME='forms_builder_columndef' THEN
  source_sql=format('SELECT table_id,0::bigint id,''["__schema","__membership","__access"]''::jsonb cols FROM %s',CASE WHEN TG_OP='DELETE' THEN 'old_rows' WHEN TG_OP='UPDATE' THEN '(SELECT table_id FROM new_rows UNION SELECT table_id FROM old_rows) moved' ELSE 'new_rows' END);
 ELSE
  -- Quyền/định danh thay đổi: chỉ epoch, tuyệt đối không lưu nội dung hồ sơ.
  IF TG_TABLE_NAME='auth_user' AND TG_OP='UPDATE' THEN
   IF NOT EXISTS(SELECT 1 FROM new_rows n JOIN old_rows o USING(id) WHERE (n.is_active,n.is_staff,n.is_superuser,n.username) IS DISTINCT FROM (o.is_active,o.is_staff,o.is_superuser,o.username)) THEN RETURN NULL; END IF;
  END IF;
  source_sql='SELECT id table_id,0::bigint id,''["__access","__schema","__membership"]''::jsonb cols FROM forms_builder_tabledef';
 END IF;
 FOR t IN EXECUTE 'SELECT DISTINCT table_id FROM ('||source_sql||') s WHERE cols<>''[]''' LOOP
  EXECUTE 'SELECT coalesce(jsonb_agg(id),''[]'') FROM (SELECT DISTINCT id FROM ('||source_sql||') s WHERE table_id=$1 AND cols<>''[]'' LIMIT 2001) q' INTO ids USING t;
  EXECUTE 'SELECT coalesce(jsonb_agg(v),''[]'') FROM (SELECT DISTINCT v FROM ('||source_sql||') s CROSS JOIN LATERAL jsonb_array_elements(s.cols) v WHERE table_id=$1) q' INTO cols USING t;
  reset_needed=jsonb_array_length(ids)>2000 OR ids @> '[0]';
  INSERT INTO crm_gridpendingchange(transaction_id,table_id,record_ids,columns,reset) VALUES(txid_current(),t,CASE WHEN reset_needed THEN '[]'::jsonb ELSE ids END,cols,reset_needed);
 END LOOP;
 RETURN NULL;
END $$;
"""

TABLES=('forms_builder_datarecord','orders_waybillitem','orders_waybillassignment','forms_builder_columndef','forms_builder_tabledef','forms_builder_grant','org_userprofile','org_department','org_team','auth_user','orders_product','orders_order')
for table in TABLES:
    for operation in ('INSERT','UPDATE','DELETE'):
        refs='REFERENCING '+('OLD TABLE AS old_rows ' if operation!='INSERT' else '')+('NEW TABLE AS new_rows ' if operation!='DELETE' else '')
        SQL+=f'CREATE TRIGGER crm_capture_{operation.lower()} AFTER {operation} ON {table} {refs} FOR EACH STATEMENT EXECUTE FUNCTION crm_grid_capture();\n'

REVERSE='\n'.join(f'DROP TRIGGER IF EXISTS crm_capture_{op} ON {t};' for t in TABLES for op in ('insert','update','delete'))+'''
DROP TRIGGER IF EXISTS crm_grid_commit ON crm_gridpendingchange;
DROP FUNCTION crm_grid_capture();
DROP FUNCTION crm_grid_flush();
'''


class Migration(migrations.Migration):
    dependencies=[('crm','0003_grid_revision')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
