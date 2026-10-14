const assert=require('assert/strict'),Copy=require('../app/static/js/master-working-copy.js');
const w=new Copy(),c=(old,value,id=1)=>({id,column:'text',old,value});
w.stage([c(null,'')]);assert.equal(w.count,0);assert.equal(w.undo.length,0);
w.stage([c('A','B')]);assert.equal(w.count,1);assert.equal(w.pending()[0].old,'A');
w.stage([c('B','C')]);assert.equal(w.count,1);assert.equal(w.pending()[0].old,'A');w.travel();assert.equal(w.value(1,'text'),'B');w.travel(true);assert.equal(w.value(1,'text'),'C');
const payload=w.pending();w.hold(payload);w.stage([c('C','A')]);assert.equal(w.count,0);
w.acknowledge(payload,[{id:1,cells:{text:{value:'C'}}}]);assert.deepEqual(w.pending(),[c('C','A')]);assert.equal(w.count,1);
w.hold(w.pending());w.acknowledge(w.pending(),[{id:1,cells:{text:{value:'A'}}}]);assert.equal(w.count,0);
w.travel();assert.equal(w.pending()[0].value,'C');assert.equal(w.pending()[0].old,'A');
// Trọn lượt bị từ chối khi vượt giới hạn, không stage một phần.
const cap=new Copy();cap.stage(Array.from({length:2000},(_,i)=>c('a','b',i+1)));
assert.throws(()=>cap.stage([c('a','b',2001)]),/2.000/);assert.equal(cap.count,2000);assert.equal(cap.entries.has('2001:text'),false);
// Poll không đè nháp hoặc làm mất giá trị cũ dùng CAS.
const polling=new Copy();polling.stage([c('a','b')]);polling.observe([{id:1,cells:{text:{value:'other'}}}]);assert.equal(polling.pending()[0].old,'a');assert.equal(polling.value(1,'text'),'b');
console.log('PASS working copy: staging, undo/redo, save acknowledgement, unknown response, atomic cap, polling');

const normalized=new Copy();normalized.stage([c('old ','new')]);normalized.acknowledge(normalized.pending(),[{id:1,cells:{text:{value:'new'}}}]);normalized.travel();normalized.acknowledge(normalized.pending(),[{id:1,cells:{text:{value:'old'}}}]);normalized.travel(true);assert.equal(normalized.pending()[0].value,'new');
console.log('PASS history after server normalization');

// TL-03: hoàn tác, làm lại gửi lại chuỗi máy kèm cờ machine — máy chủ không đọc "0.125" theo luật Việt (thành 125).
const may=new Copy(),m=(old,value)=>({id:1,column:'tien',old,value});
may.stage([m('0.125','0,126')]);let goi=may.pending();assert.equal(goi[0].machine,undefined);
may.hold(goi);may.acknowledge(goi,[{id:1,cells:{tien:{value:'0.126'}}}]);
may.travel();goi=may.pending();assert.deepEqual([goi[0].value,goi[0].machine],['0.125',true]);
may.hold(goi);may.acknowledge(goi,[{id:1,cells:{tien:{value:'0.125'}}}]);
may.travel(true);goi=may.pending();assert.deepEqual([goi[0].value,goi[0].machine],['0.126',true]);
console.log('PASS machine flag: undo/redo after server normalization');
