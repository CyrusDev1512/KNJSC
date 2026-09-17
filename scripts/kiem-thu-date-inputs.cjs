// Kiểm parser và round-trip; thao tác trình duyệt được kiểm riêng trên local.
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
class Input { get value(){return this.raw||'';} set value(v){this.raw=v;} }
const context = {HTMLInputElement:Input, window:{}, Date, WeakSet, Map,
  document:{querySelectorAll:()=>[],addEventListener(){},body:{}},
  MutationObserver:class {observe(){}}};
vm.runInNewContext(fs.readFileSync('app/static/js/date-inputs.js','utf8'),context);
const dates=context.window.KNDate;
for (const [raw,iso] of [['1/9/2026','2026-09-01'],['29/02/2024','2024-02-29'],['31/12/2026','2026-12-31'],['','']]) {
  assert.equal(dates.canonical(raw),iso);
  assert.equal(dates.canonical(dates.display(iso,false)),iso);
}
for (const raw of ['29/02/2025','31/04/2026','00/09/2026','12/13/2026','2026/09/16','16/09/0000']) assert.equal(dates.canonical(raw),null);
assert.equal(dates.canonical('16/09/2026 23:59:59.123',true),'2026-09-16T23:59:59.123');
assert.equal(dates.canonical('16/09/2026 24:00',true),null);
assert.equal(dates.display('2026-09-15T18:30:00Z',true),'16/09/2026 01:30:00.000');
console.log('PASS: ngày hợp lệ, năm nhuận, ngày sai, round-trip ISO và ngày giờ Việt Nam.');

// Chạy chính đường hiển thị nháp của lưới, không chỉ test bộ đổi ngày.
const grid=fs.readFileSync('app/static/js/master-grid.js','utf8');
const cellValueSource=grid.slice(grid.indexOf('  function cellValue('),grid.indexOf('  function refreshStatus('));
context.config={styleClasses:{}};
context.state={columns:[{code:'ngay',type:'date'},{code:'luc',type:'datetime'}]};
context.same=(a,b)=>a===b;
let pending='2026-01-22';
context.working={value:(id,col,original,prop)=>prop?original:pending};
vm.runInNewContext(cellValueSource,context);
const row={id:1,cells:{ngay:{value:'2026-01-21',display:'21/01/2026',style:{}}}};
assert.equal(context.cellValue(row,'ngay').display,'22/01/2026');
assert.equal(context.cellValue(row,'ngay').value,'2026-01-22');
pending='2026-01-21';
assert.equal(context.cellValue(row,'ngay').display,'21/01/2026');
pending='';
assert.equal(context.cellValue(row,'ngay').display,'');
row.cells.luc={value:null,display:'',style:{}};
pending='2026-09-15T18:30:00Z';
assert.equal(context.cellValue(row,'luc').display,'16/09/2026 01:30');
console.log('PASS: ô nháp/hoàn tác hiển thị D/M/Y, giữ giá trị ISO, ngày giờ Việt Nam.');
