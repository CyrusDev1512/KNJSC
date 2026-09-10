const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try{
    const page=await browser.newPage();
    await page.setContent(`<style>${fs.readFileSync(require.resolve('../app/static/css/master-grid.css'),'utf8')}</style><div style="position:relative;width:700px;height:100px"><div class="mg-row" style="position:relative;height:28px"><div id="pinned" class="mg-cell mg-pinned" style="left:46px;top:0;width:160px;height:28px">Tên khách</div><div id="selected" class="mg-cell mg-current mg-selected" style="left:100px;top:0;width:160px;height:28px">Ô cuộn bên dưới</div></div></div>`);
    assert.equal(await page.locator('#pinned').evaluate(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+100,r.y+10).id;}),'pinned','Ô hiện hành không được đè lên cột cố định khi cuộn ngang');
    console.log('PASS: lớp ô hiện hành nằm dưới cột cố định');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
