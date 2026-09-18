/* Hồi quy lưới dùng chung trên fixture Vận đơn mới, không chạy độc lập. */
const assert=require('assert/strict');
module.exports=async({page,context,base,delivery})=>{
 const url=base+'/bang-tinh/van_don/?sap=ma_don';
 await page.setViewportSize({width:1440,height:900});await page.goto(url);
 await page.locator('.mg-cell[data-id]').first().waitFor();
 const api=base+'/bang-tinh/van_don/';
 const read=async()=>await(await context.request.get(api+'du-lieu/?sap=ma_don&offset=98')).json();
 const snapshot=await read(),row=snapshot.rows[0];
 await page.locator('#mg-viewport').evaluate(v=>{v.scrollTop=98*28;v.scrollLeft=0;});
 await page.locator('.mg-cell[data-r="98"][data-code="ma_don"]').click();
 for(let i=0;i<4;i++)await page.keyboard.press('Shift+ArrowDown');
 await page.evaluate(()=>navigator.clipboard.writeText('waiting'));
 await page.keyboard.press('Control+c');await page.waitForFunction(async()=>await navigator.clipboard.readText()!=='waiting');
 assert.deepEqual((await page.evaluate(()=>navigator.clipboard.readText())).split('\r\n'),snapshot.rows.slice(0,5).map(r=>r.cells.ma_don.value));
 // Tay kéo thật; hủy và phím Home đều đưa chiều cao về đúng giới hạn.
 const handle=page.locator('[data-row-resize="98"]');const b=await handle.boundingBox();
 await page.mouse.move(b.x+15,b.y+2);await page.mouse.down();await page.mouse.move(b.x+15,b.y+102,{steps:8});await page.mouse.up();
 await page.waitForFunction(()=>document.querySelector('.mg-row[aria-rowindex="100"]').getBoundingClientRect().height===128);
 await handle.focus();await page.keyboard.press('Home');
 await page.waitForFunction(()=>document.querySelector('.mg-row[aria-rowindex="100"]').getBoundingClientRect().height===28);
 // Phân công qua popup; nhân viên chỉ thấy dòng vừa được giao.
 await page.locator('[data-select-row="98"]').click();await page.locator('#mg-more-button').click();await page.locator('#mg-assign').click();
 await page.locator('#vd-assignment-fields select[name=delivery]').selectOption(String(delivery));
 await page.locator('#vd-assignment-save').click();await page.locator('#vd-assignment').waitFor({state:'hidden'});
 const staff=await context.browser().newContext({viewport:{width:1440,height:900}});
 try{
  const p=await staff.newPage();await p.goto(base+'/dang-nhap/');await p.locator('[name=username]').fill('staff_vd');await p.locator('[name=password]').fill('matkhau-kiem-thu-1');
  await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);
  await p.goto(api+'?f_ma_don='+encodeURIComponent(row.cells.ma_don.value));await p.locator('.mg-cell[data-id]').first().waitFor();
  assert.match(await p.locator('#mg-count').textContent(),/^1 dòng/);
  const metadata=await(await staff.request.get(api+'du-lieu/')).json();assert.equal(metadata.total,1);
  const left=46+metadata.columns.slice(0,metadata.columns.findIndex(c=>c.code==='ghi_chu')).reduce((sum,c)=>sum+c.width,0);
  await p.locator('#mg-viewport').evaluate((v,x)=>v.scrollLeft=Math.max(0,x-600),left);
  await p.locator('.mg-cell[data-code="ghi_chu"]').first().dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('Staff xác nhận qua lưới chung');
  const save=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.request().method()==='POST');await p.locator('#mg-input [name=value]').press('Control+Enter');assert.equal((await save).status(),200);
  assert.equal((await read()).rows[0].cells.ghi_chu.value,'Staff xác nhận qua lưới chung');
  // Mất phản hồi sau commit: tự gửi lại cùng UUID, chỉ có một lần ghi lịch sử.
  const operations=[];const capture=r=>{if(r.method()==='POST'&&r.url().includes('luu-json/'))operations.push(JSON.parse(r.postData()).operation);};p.on('request',capture);
  await p.route('**/luu-json/',async route=>{await route.fetch();await route.abort('failed');await p.unroute('**/luu-json/');});
  await p.locator('.mg-cell[data-code="ghi_chu"]').first().dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('Gửi lại sau mất phản hồi');
  const acknowledged=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.status()===200);await p.locator('#mg-input [name=value]').press('Control+Enter');await acknowledged;
  await p.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');p.off('request',capture);
  assert.equal(operations.length,2);assert.equal(operations[0],operations[1]);
  // Đồng nghiệp sửa trong lúc Staff giữ nháp, chọn giá trị server sau CAS 409.
  await p.locator('.mg-cell[data-code="ghi_chu"]').first().dblclick({delay:120});await p.locator('#mg-input [name=value]').fill('Nháp cần đối chiếu');
  const token=await page.locator('[name=csrfmiddlewaretoken]').first().inputValue();
  const other=await context.request.post(api+'luu-json/',{headers:{'X-CSRFToken':token},data:{operation:require('crypto').randomUUID(),cells:[{id:row.id,column:'ghi_chu',old:'Gửi lại sau mất phản hồi',value:'Quản lý đã cập nhật'}]}});assert.equal(other.status(),200);
  const conflict=p.waitForResponse(r=>r.url().includes('luu-json/')&&r.status()===409);await p.locator('#mg-input [name=value]').press('Control+Enter');await conflict;
  await p.locator('#mg-more-button').click();await p.locator('#mg-conflict-button').click();await p.locator('#mg-conflict select').selectOption('server');await p.getByRole('button',{name:'Áp dụng lựa chọn và lưu',exact:true}).click();
  await p.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');assert.equal((await read()).rows[0].cells.ghi_chu.value,'Quản lý đã cập nhật');
  await p.locator('#mg-viewport').focus();await p.keyboard.press('Escape');await p.locator('.mg-cell[data-code="ghi_chu"]').first().click();
  await p.locator('#mg-more-button').click();await p.locator('#mg-history-button').click();await p.locator('#mg-history-body').getByText('staff_vd',{exact:false}).first().waitFor();
 }finally{await staff.close();}
 return {crossBlockCopy:true,rowResize:true,assignment:true,staffAutosave:true,history:true,lostResponseReplay:true,conflict:true};
};
