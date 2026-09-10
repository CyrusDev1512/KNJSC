/* Baseline lịch sử: chạy test_feedback_browser_server từ snapshot HEAD trước ADR-021, không dùng server hiện tại hoặc DB dev. */
const {chromium}=require('playwright');
const fs=require('fs'), path=require('path');
const root=path.resolve(__dirname,'..'), out=path.join(root,'.agents/design-state/review/master');
(async()=>{
  const signal=path.join(root,'app/.feedback-browser-ready.json');
  for(let n=0;n<120&&!fs.existsSync(signal);n++) await new Promise(r=>setTimeout(r,500));
  if(!fs.existsSync(signal)) throw Error('Thiếu server test');
  const fixture=JSON.parse(fs.readFileSync(signal)); fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:900}});
  try {
    await page.goto('http://127.0.0.1:8031/dang-nhap/');
    await page.locator('[name=username]').fill('quan_tri');
    await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
    await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
    await page.goto('http://127.0.0.1:8031/bang-tinh/van_don_moi/');
    const measure=()=>page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth,
      grid:document.querySelector('#luoi-vd').getBoundingClientRect().toJSON(),cells:document.querySelectorAll('#luoi-vd td').length,
      columns:[...document.querySelectorAll('#luoi-vd thead tr.bt-hang-chu th')].map(e=>e.getBoundingClientRect().width)}));
    const before=await measure();
    await page.locator(`#o-${fixture.rows[0]}-ma_don`).click(); await page.keyboard.press('Control+a');
    const selected=await measure(); await page.screenshot({path:path.join(out,'before-select.png')});
    const handle=page.locator('.bt-keo-cot').first(), box=await handle.boundingBox();
    await page.mouse.move(box.x+3,box.y+8);await page.mouse.down();await page.mouse.move(box.x+200,box.y+8,{steps:10});await page.mouse.up();
    const resized=await measure(); await page.reload();
    const note=page.locator(`#o-${fixture.rows[0]}-ghi_chu`);await note.scrollIntoViewIfNeeded();await note.dblclick();
    const ta=page.locator('.o-sua-form textarea');await ta.waitFor();const b=await ta.boundingBox();
    await page.mouse.move(b.x+b.width-3,b.y+b.height-3);await page.mouse.down();await page.mouse.move(b.x+b.width+120,b.y+b.height+180,{steps:10});await page.mouse.up();
    await page.screenshot({path:path.join(out,'before-editor.png')});
    const editor=await measure();await page.keyboard.press('Escape');
    fs.writeFileSync(path.join(out,'baseline.json'),JSON.stringify({before,selected,resized,editor},null,2));
    fs.writeFileSync(path.join(root,'app/.feedback-browser-result.json'),JSON.stringify({ok:true}));
    console.log(JSON.stringify({before,selected,resized,editor}));
  }catch(e){fs.writeFileSync(path.join(root,'app/.feedback-browser-result.json'),JSON.stringify({ok:false,error:e.stack}));throw e;}
  finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
