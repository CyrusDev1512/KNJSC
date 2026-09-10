/* DB test của fixture UI: thu quyền một dòng giữa lượt dán hai dòng. */
const assert=require('node:assert/strict');
module.exports=async({admin,leader,staff,context,base,delivery})=>{
  const rows=await admin.evaluate(async()=>Promise.all([0,1].map(async n=>{
    const data=await fetch('/bang-tinh/van_don_moi/du-lieu/?f_ma_don=MASTER-0000'+n).then(r=>r.json());return data.rows[0];
  })));
  async function assign(ids,value){await leader.evaluate(async({ids,value})=>{
    const url='/van-don/phan-cong/',snapshot=await fetch(url+'?'+ids.map(id=>'row='+id).join('&')).then(r=>r.json());
    const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({versions:Object.fromEntries(snapshot.rows.map(r=>[r.id,r.version])),changes:{delivery:value}})});
    if(!response.ok)throw Error('Phân công fixture thất bại: '+await response.text());
  },{ids,value});}
  await assign(rows.map(r=>r.id),delivery);
  await staff.goto(base+'/bang-tinh/van_don_moi/');await staff.bringToFront();
  const first=staff.locator(`.mg-cell[data-id="${rows[0].id}"][data-code="bang"]`);
  await first.waitFor();await first.click();
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  let release,seen;const arrived=new Promise(r=>seen=r),blocked=new Promise(r=>release=r),requests=[];
  await staff.route('**/luu-json/',async route=>{
    requests.push(route.request().postDataJSON());if(requests.length===1){seen();await blocked;}await route.continue();
  });
  // Một cột, hai hàng trong cùng một lượt dán nguyên tử.
  await staff.evaluate(()=>navigator.clipboard.writeText('Nháp sẽ mất quyền\nNháp vẫn còn quyền'));
  await staff.keyboard.press('Control+v');
  let timer;try{await Promise.race([arrived,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Lượt dán chưa gửi sau 10 giây')),10000);})]);}finally{clearTimeout(timer);}
  assert.deepEqual(requests[0].cells.map(c=>c.id),rows.map(r=>r.id));
  await assign([rows[0].id],null);release();
  await staff.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Lỗi lưu');
  await staff.waitForFunction(id=>!document.querySelector(`.mg-cell[data-id="${id}"]`),rows[0].id);
  const retained=staff.locator(`.mg-cell[data-id="${rows[1].id}"][data-code="bang"]`);
  await retained.waitFor();assert.equal(await retained.textContent(),'Nháp vẫn còn quyền');
  await new Promise(r=>setTimeout(r,2200));assert.equal(requests.length,1,'Không tự gửi một phần sau 403');
  const before=await admin.evaluate(async()=>fetch('/bang-tinh/van_don_moi/du-lieu/?f_ma_don=MASTER-00001').then(r=>r.json()));
  assert.equal(before.rows[0].cells.bang.value,rows[1].cells.bang.value,'Lượt bị từ chối phải rollback toàn bộ');
  await staff.getByRole('button',{name:'Thử lại',exact:true}).click();
  await staff.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
  assert.equal(requests.length,2);assert.notEqual(requests[1].operation,requests[0].operation);
  assert.deepEqual(requests[1].cells.map(c=>c.id),[rows[1].id]);
  await staff.unroute('**/luu-json/');
};
