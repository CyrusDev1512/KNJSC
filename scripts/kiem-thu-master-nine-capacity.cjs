/* Chrome lớn: chỉ nhận session test từ marker pytest, không dùng tài khoản thật. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const out=process.env.NINE_EVIDENCE_DIR||path.resolve(__dirname,'../.agents/design-state/review/master-nine-capacity');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const percentile=(v,p)=>[...v].sort((a,b)=>a-b)[Math.min(v.length-1,Math.floor(v.length*p))];
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true}),deadline=Date.now()+100*60*1000;let last='';
  while(Date.now()<deadline){
    const marker=path.join(out,'nine-browser-ready.json'),done=path.join(out,'nine-browser-done.json');
    if(!fs.existsSync(marker)||fs.existsSync(done)){await pause(500);continue;}
    const cfg=JSON.parse(fs.readFileSync(marker)),label=`${cfg.stage}-${cfg.rows}`,metrics={label,operations:{},memory:[],ok:false};
    if(last===label){await pause(500);continue;}last=label;
    const context=await browser.newContext({viewport:{width:1440,height:900}});await context.addCookies([{name:'sessionid',value:cfg.session,url:`http://127.0.0.1:${cfg.port}`}]);const page=await context.newPage();
    try{
      await page.goto(`http://127.0.0.1:${cfg.port}/bang-tinh/van_don_moi/`);await page.locator('.mg-cell[data-id]').first().waitFor({timeout:60000});
      const cdp=await context.newCDPSession(page);await cdp.send('Performance.enable');
      const values=[];
      for(let i=0;i<100;i++)values.push(await page.evaluate(async i=>{
        const start=performance.now(),rows=document.querySelectorAll('.mg-number');rows[i%Math.min(10,rows.length)].click();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return performance.now()-start;
      },i));
      metrics.operations.select={samples:values.length,p50:percentile(values,.5),p95:percentile(values,.95),p99:percentile(values,.99)};
      // Bản mới: đo thêm mở/nhập ô và vùng đọc. Không gọi đây là IME thật.
      if(cfg.stage==='after'){
        const inputSamples=[],readSamples=[];
        await page.locator('.mg-cell[data-r="0"][data-code="bang"]').click();
        let release;const gate=new Promise(resolve=>release=resolve);
        await page.route('**/luu-json/',async route=>{const response=await route.fetch();await gate;await route.fulfill({response});});
        await page.keyboard.press('F2');await page.locator('#mg-editor input').fill('Kiểm tự lưu '+Date.now());await page.keyboard.press('Enter');
        await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đang lưu');
        for(let i=0;i<100;i++){
          const start=Date.now();await page.keyboard.press('F2');await page.locator('#mg-editor input').waitFor();await page.keyboard.insertText('Việt');
          await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));inputSamples.push(Date.now()-start);await page.keyboard.press('Escape');
          if(await page.locator('#bt-trang-thai').textContent()!=='Đang lưu')throw Error('Mẫu nhập không còn nằm trong lượt đang lưu');
        }
        release();await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');await page.unroute('**/luu-json/');
        await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=3000);await page.locator('.mg-cell[data-code="ghi_chu"]').first().waitFor();
        const target=await page.locator('.mg-cell[data-code="ghi_chu"]').evaluateAll(es=>es.find(e=>e.scrollWidth>e.clientWidth)?.dataset.r);
        if(target===undefined)throw Error('Không có nội dung dài để đo reader');
        let loadingRetries=0;
        for(let attempt=0;readSamples.length<100&&attempt<500;attempt++){
          // Kiểm ô đã nạp và click trong cùng lượt JS, tránh chọn placeholder
          // giữa hai lệnh Playwright khi polling vừa làm mới cache.
          const sample=await page.evaluate(async r=>{
            const cell=document.querySelector(`.mg-cell[data-code="ghi_chu"][data-r="${r}"][data-id]`);
            if(!cell||cell.scrollWidth<=cell.clientWidth)return null;
            const box=cell.getBoundingClientRect(),x=box.x+box.width/2,y=box.y+box.height/2,start=performance.now();
            const options={bubbles:true,button:0,pointerId:1,clientX:x,clientY:y};
            cell.dispatchEvent(new PointerEvent('pointerdown',options));cell.dispatchEvent(new PointerEvent('pointerup',options));
            await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
            return document.getElementById('mg-reader').hidden?null:performance.now()-start;
          },target);
          if(sample===null){loadingRetries++;await pause(30);continue;}
          readSamples.push(sample);await page.keyboard.press('Escape');
        }
        if(readSamples.length!==100)throw Error('Không đủ 100 mẫu mở nội dung đã tải');
        for(const [name,samples] of [['openAndTypeWhileSaving',inputSamples],['reader',readSamples]])metrics.operations[name]={samples:100,p50:percentile(samples,.5),p95:percentile(samples,.95),p99:percentile(samples,.99),method:name==='reader'?'Synthetic pointer on loaded cell to two frames; real pointer covered by E2E':'Playwright action to two frames, includes driver overhead; write response held during typing'};
        metrics.operations.reader.loadingRetries=loadingRetries;
        await page.locator('#mg-viewport').evaluate(e=>e.scrollLeft=0);
      }
      // Đo pointer thật tới hai frame sau thao tác; không chỉ đo thời gian HTTP.
      for(const [name,selector,axis] of [['column','[data-resize="ma_don"]','x'],['row','[data-row-resize="0"]','y']]){
        const handle=page.locator(selector),box=await handle.boundingBox(),samples=[];
        await page.mouse.move(box.x+3,box.y+3);await page.mouse.down();
        for(let i=0;i<100;i++){
          await page.evaluate(()=>{window.__nineStart=performance.now();});
          await page.mouse.move(box.x+3+(axis==='x'?i%40:0),box.y+3+(axis==='y'?i%80:0));
          samples.push(await page.evaluate(async()=>{await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return performance.now()-window.__nineStart;}));
        }
        await page.mouse.up();metrics.operations[name]={samples:100,p50:percentile(samples,.5),p95:percentile(samples,.95),p99:percentile(samples,.99)};
      }
      for(let cycle=0;cycle<3;cycle++){
        for(const fraction of [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,.99,0]){
          await page.locator('#mg-viewport').evaluate((e,f)=>e.scrollTop=(e.scrollHeight-e.clientHeight)*f,fraction);
          await page.waitForFunction(()=>document.querySelectorAll('.mg-cell[data-id]').length>20);await pause(150);
          const d=await page.evaluate(()=>window.KNJSC_MASTER.diagnostics());if(d.cache>10)throw Error('Cache vượt 10 khối');
        }
        await cdp.send('HeapProfiler.collectGarbage');const measured=await cdp.send('Performance.getMetrics'),dom=await cdp.send('Memory.getDOMCounters');
        metrics.memory.push({cycle,heap:measured.metrics.find(x=>x.name==='JSHeapUsedSize').value,dom,...await page.evaluate(()=>window.KNJSC_MASTER.diagnostics())});
      }
      await page.screenshot({path:path.join(out,label+'-grid.png')});metrics.ok=true;
    }catch(error){metrics.error=error.stack;metrics.failureState=await page.evaluate(()=>({editor:!document.getElementById('mg-editor').hidden,reader:!document.getElementById('mg-reader').hidden,...window.KNJSC_MASTER.diagnostics()})).catch(()=>null);await page.screenshot({path:path.join(out,label+'-failure.png')}).catch(()=>{});}
    finally{await context.close();fs.writeFileSync(path.join(out,label+'-browser.json'),JSON.stringify(metrics,null,2));fs.writeFileSync(done,JSON.stringify({ok:metrics.ok,error:metrics.error}));console.log(label,JSON.stringify(metrics));}
    if(process.env.NINE_ONCE==='1')break;
    if(cfg.stage==='after'&&cfg.rows===300000&&cfg.endurance){
      const ctx=await browser.newContext({viewport:{width:1440,height:900}});await ctx.addCookies([{name:'sessionid',value:cfg.session,url:`http://127.0.0.1:${cfg.port}`}]);const p=await ctx.newPage(),retained={samples:[],ok:false};
      const started=Date.now();
      try{
        await p.goto(`http://127.0.0.1:${cfg.port}/bang-tinh/van_don_moi/`);await p.locator('.mg-cell[data-id]').first().waitFor();const cdp=await ctx.newCDPSession(p);await cdp.send('Performance.enable');
        for(let minute=0;minute<=30;minute++){
          const wait=started+minute*60000-Date.now();if(wait>0)await pause(wait);
          await p.locator('#mg-viewport').evaluate((e,f)=>e.scrollTop=(e.scrollHeight-e.clientHeight)*f,(minute%10)/10);await pause(300);
          await p.waitForFunction(()=>document.querySelectorAll('.mg-cell[data-id]').length>20,{}, {timeout:10000});
          await cdp.send('HeapProfiler.collectGarbage');const measured=await cdp.send('Performance.getMetrics'),dom=await cdp.send('Memory.getDOMCounters');
          retained.samples.push({seconds:(Date.now()-started)/1000,heap:measured.metrics.find(x=>x.name==='JSHeapUsedSize').value,dom,...await p.evaluate(()=>window.KNJSC_MASTER.diagnostics())});
          fs.writeFileSync(path.join(out,'endurance-browser.json'),JSON.stringify(retained,null,2));
        }
        retained.ok=true;
      }catch(error){retained.error=error.stack;}
      finally{retained.elapsed=(Date.now()-started)/1000;fs.writeFileSync(path.join(out,'endurance-browser.json'),JSON.stringify(retained,null,2));await ctx.close();console.log('endurance-browser',JSON.stringify({ok:retained.ok,samples:retained.samples.length,elapsed:retained.elapsed,error:retained.error}));}
      break;
    }
    if(cfg.stage==='after'&&cfg.rows===300000)break;
  }
  await browser.close();
})();
