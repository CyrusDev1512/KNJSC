/* Diff app theo snapshot trước tác vụ, không stage/reset index của người dùng. */
const fs=require('fs'),path=require('path'),{spawnSync}=require('child_process');
const root=path.resolve(__dirname,'..'),baseline=process.argv[2];
if(!baseline||!fs.existsSync(path.join(baseline,'app/manage.py')))throw Error('Cần đường dẫn snapshot baseline thực tế');
const files=[
  'crm/models.py','crm/migrations/0002_grid_cell_history.py','crm/services/master_grid_service.py','crm/services/grid_service.py',
  'crm/master_views.py','crm/urls.py','crm/views.py','crm/waybill_forms.py','crm/waybill_views.py',
  'crm/tests/test_master_nine.py','crm/tests/test_master_nine_capacity.py','crm/tests/test_master_nine_storage.py',
  'crm/tests/test_master_grid.py','crm/tests/test_waybill_new.py','forms_builder/query.py',
  'forms_builder/managers.py','forms_builder/models.py','forms_builder/migrations/0010_master_cover_index.py','forms_builder/services/record_service.py','orders/models.py',
  'orders/services/order_service.py','orders/services/assignment_service.py',
  'static/js/master-working-copy.js','static/js/master-grid.js','static/css/master-grid.css',
  'templates/crm/master_grid.html','templates/crm/_waybill_entry.html','tests/perf/locust_master_nine.py',
  'tests/perf/inspect_master_nine.py','tests/perf/trial_master_index.py','tests/perf/trial_master_country_index.py'
];
let diff='';const changed=[];
for(const file of files){
  const before=path.join(baseline,'app',file),after=path.join(root,'app',file);
  const r=spawnSync('git',['diff','--no-index','--',fs.existsSync(before)?before:'NUL',after],{encoding:'utf8',maxBuffer:20*1024*1024});
  if(r.status>1)throw Error(r.stderr);if(r.stdout){diff+=r.stdout;changed.push('app/'+file);}
}
const out=path.join(root,'.agents/design-state/review/master-nine');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'implementation.diff'),diff);
fs.writeFileSync(path.join(out,'diff-files.json'),JSON.stringify({baseline,files:changed,note:'Chỉ app trong phạm vi, so snapshot workspace trước sửa; các tài liệu/script xem riêng, không nhận thay đổi ERP có sẵn là của tác vụ này.'},null,2));
console.log(changed.length+' app files; '+Buffer.byteLength(diff)+' bytes');
