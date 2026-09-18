const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.env.GRID_INTERACTION_SOURCE||'app/static/js/master-grid.js','utf8');
const calls=[];const ctx={config:{canCreate:false},state:{total:100,visible:[{},{}],drafts:[]},dirty:()=>false,rowAt:r=>({id:r+1}),reader:{},viewport:{focus(){}},repaint:()=>calls.push('full'),repaintSelection:()=>calls.push('selection')};
vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  function choose('),source.indexOf('  function ensureVisible(')),ctx);
ctx.choose(1,1);assert.deepEqual(calls,['selection'],'Chọn ô không được dựng lại nội dung lưới');
assert.equal(ctx.state.currentId,2);
console.log('PASS: chọn ô chỉ cập nhật vùng chọn');
// Một frame chỉ có một callback; lưu/scroll không bị lựa chọn che mất.
const frames=[],paints=[];
const scheduler={scheduled:false,scrollPaint:false,selectionPaint:false,requestAnimationFrame:f=>frames.push(f),render:scroll=>paints.push(scroll?'scroll':'full'),renderSelection:()=>paints.push('selection')};
vm.createContext(scheduler);vm.runInContext(source.slice(source.indexOf('  function repaint('),source.indexOf('  function invalidate(')),scheduler);
function flush(expected){assert.equal(frames.length,1);frames.shift()();assert.deepEqual(paints.splice(0),[expected]);}
scheduler.repaintSelection();scheduler.repaintSelection();flush('selection');
scheduler.repaintSelection();scheduler.repaint();flush('full');
scheduler.repaint();scheduler.repaintSelection();flush('full');
scheduler.repaintSelection();scheduler.repaint(true);flush('full');
scheduler.repaint(true);scheduler.repaintSelection();flush('full');
console.log('PASS: gộp frame; thay đổi dữ liệu luôn thắng cập nhật lựa chọn');
