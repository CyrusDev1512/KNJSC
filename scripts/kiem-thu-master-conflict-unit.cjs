const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm'),Working=require('../app/static/js/master-working-copy.js');
const source=fs.readFileSync(require.resolve('../app/static/js/master-grid.js'),'utf8');
const conflictCode=source.slice(source.indexOf('  function propertyName('),source.indexOf("  $('mg-conflict-button').onclick"));
const updateCode=source.slice(source.indexOf('  function updateRows('),source.indexOf('  async function saveAll('));
function run(choice){
  let messageCleared=false;
  const row={id:1,cells:{note:{value:'Ban đầu',display:'Ban đầu',style:{}}}},working=new Working();working.stage([{id:1,column:'note',old:'Ban đầu',value:'Của tôi'}]);
  const body={children:[],append(...children){this.children.push(...children);},replaceChildren(){this.children=[];}};
  const ctx={state:{cache:new Map([[0,{rows:[row]}]]),pending:new Map(),generation:0,conflicts:[{id:1,column:'note',old:'Ban đầu',value:'Của tôi',current:'Đồng nghiệp'}]},working,window:{KNJSCWorkingCopy:Working},Map,Option:function(text,value){this.text=text;this.value=value;},
    config:{},$:id=>id==='mg-conflict-body'?body:{close(){}},element:(tag,css,text)=>({tag,text,children:[],setAttribute(){},append(...children){this.children.push(...children);}}),message(){messageCleared=true;},openDialog(){},saveAll(){},repaint(){}};
  vm.createContext(ctx);vm.runInContext(updateCode+conflictCode+';showConflicts();',ctx);
  const section=body.children.find(c=>c.tag==='section'),select=section.children.find(c=>c.tag==='select');select.value=choice;select.onchange();body.children.find(c=>c.tag==='button').onclick();
  const cached=ctx.state.cache.get(0).rows[0].cells.note.value;
  assert.equal(working.value(1,'note',cached),choice==='server'?'Đồng nghiệp':'Của tôi');
  if(choice==='mine')assert.equal(working.pending()[0].old,'Đồng nghiệp');
  assert(messageCleared,'Xóa thông báo xung đột sau khi đã đối chiếu');
}
run('server');run('mine');console.log('PASS: dùng hiện tại hiển thị ngay; giữ của tôi dùng mốc CAS hiện tại');
