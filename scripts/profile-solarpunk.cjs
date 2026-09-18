const {chromium}=require('./solarpunk-browser.cjs');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 for(const port of [18022,18021]){
  const p=await browser.newPage({viewport:{width:1440,height:900}});await p.goto(`http://localhost:${port}/dang-nhap/`);
  await p.locator('[name=username]').fill('quantri');await p.locator('[name=password]').fill('matkhaucuatoi');await Promise.all([p.waitForURL(u=>!u.pathname.includes('dang-nhap')),p.locator('button[type=submit]').click()]);
  await p.goto(`http://localhost:${port}/bang-tinh/van_don/`);await p.locator('.mg-cell').first().waitFor();
  await p.waitForTimeout(300);
  const metrics=await p.evaluate(async()=>{
   const grid=document.querySelector('#mg-viewport'),samples=[],selection=[],edit=[],tasks=[];
   const observer=new PerformanceObserver(list=>tasks.push(...list.getEntries().map(e=>e.duration)));observer.observe({type:'longtask',buffered:false});
   const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
   for(let i=0;i<30;i++){const t=performance.now();grid.scrollTop=(i%10)*160;grid.scrollLeft=(i%4)*180;await frame();samples.push(performance.now()-t);}
   grid.scrollTop=grid.scrollLeft=0;await frame();
   for(let i=0;i<15;i++){
    const cells=[...document.querySelectorAll('.mg-cell[data-code="ten_khach"]')];const cell=cells[i%cells.length];
    const t=performance.now();cell.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));cell.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0}));await frame();selection.push(performance.now()-t);
    const e=performance.now();cell.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));await frame();edit.push(performance.now()-e);
    document.querySelector('#mg-input input')?.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));
   }
   observer.disconnect();const summary=a=>({median:a.slice().sort((a,b)=>a-b)[Math.floor(a.length/2)],max:Math.max(...a)});
   return{scroll:summary(samples),selection:summary(selection),editor:summary(edit),longTasks:tasks,dom:document.querySelectorAll('*').length,cells:document.querySelectorAll('.mg-cell').length,cellBlur:getComputedStyle(document.querySelector('.mg-cell')).backdropFilter};
  });
  results.push({port,viewport:'1440x900',rows:120,...metrics});await p.close();
 }
 fs.writeFileSync('artifacts/solarpunk/performance.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
