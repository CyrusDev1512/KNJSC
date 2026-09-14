/* Hồi quy tách CSS: cùng màu giấy/chữ ở cả theme sáng và tối. */
const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'storage/crm-update/contrast');
fs.mkdirSync(out,{recursive:true});
function luminance(color){const rgb=color.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;}
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const css=['tokens.css','master-grid.css'].map(name=>fs.readFileSync(path.join(root,'app/static/css',name),'utf8')).join('\n');
 for(const theme of ['dark','light']){
  await page.setContent(`<html data-theme="${theme}"><head><style>${css}</style></head><body><div class="mg-root mg-waybill-master"><div class="mg-viewport" style="height:200px"><div class="mg-cell mg-pinned" data-code="ma_don" style="position:relative;width:200px">DH-TEST-0001</div><div class="mg-cell" style="position:relative;width:200px">Khách kiểm thử</div><div class="mg-heading mg-pinned" data-code="ten_khach" style="position:relative;width:200px"><button>Tên khách</button></div></div></div></body></html>`);
  const colors=await page.locator('.mg-cell,.mg-heading').evaluateAll(elements=>elements.map(el=>({background:getComputedStyle(el).backgroundColor,foreground:getComputedStyle(el.querySelector('button')||el).color})));
  const ratios=colors.map(c=>{const a=luminance(c.foreground),b=luminance(c.background);return(Math.max(a,b)+.05)/(Math.min(a,b)+.05);});
  results.push({theme,colors,ratios});await page.screenshot({path:path.join(out,theme+'.png')});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(results,null,2));
 assert(results.every(result=>result.ratios.every(value=>value>=4.5)),JSON.stringify(results));
 console.log(JSON.stringify({passed:true,results}));
}finally{await browser.close();}})().catch(error=>{console.error(error.message);process.exitCode=1;});
