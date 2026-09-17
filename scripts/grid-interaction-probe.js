/* App-local measurement harness, test-only synthetic actions, no customer data. */
(()=>{
 const $=id=>document.getElementById(id),v=$('mg-viewport');
 const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const key=(el,k,extra={})=>el.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true,...extra}));
 const input=text=>{const el=$('mg-input').querySelector('[name=value]');if(!el)throw Error('Editor chưa mở');el.value=text;el.dispatchEvent(new Event('input',{bubbles:true}));};
 const summary=a=>{const b=[...a].sort((a,b)=>a-b);return {n:b.length,p50:b[Math.floor(b.length*.5)],p95:b[Math.floor(b.length*.95)],max:Math.max(...b)};};
 let made=0;const create=document.createElement.bind(document);document.createElement=(...args)=>{made++;return create(...args);};
 $('probe-release').onclick=async()=>{await fetch('/release');await frame();$('probe-output').value=$('bt-trang-thai').textContent;};
 $('probe-fail').onclick=async()=>{await fetch('/fail');await fetch('/release');await frame();$('probe-output').value=$('bt-trang-thai').textContent;};
 $('probe-run').onclick=async()=>{try{
 await fetch('/reset');
 const cell=document.querySelector('.mg-cell[data-r="0"][data-code="ten_khach"]');
 cell.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));
 document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0}));await frame();
 key(v,'F2');await frame();input('Đang lưu A');key($('mg-input').querySelector('[name=value]'),'Enter');key(v,'s',{ctrlKey:true});await frame();
 if($('bt-trang-thai').textContent!=='Đang lưu')throw Error('Chưa có request lưu đang chờ');
 const selection=[],typing=[],opened=[],createdAt=made;
 for(let i=0;i<40;i++){
 let started=performance.now();key(v,i%2?'ArrowUp':'ArrowDown');await frame();selection.push(performance.now()-started);
 const current=document.querySelector('.mg-current');if(!current||current.dataset.r!==String(i%2?0:1))throw Error('Chọn sai ô khi lưu');
 started=performance.now();key(v,'F2');await frame();opened.push(performance.now()-started);
 started=performance.now();input('Nhập tiếng Việt '+i);await frame();typing.push(performance.now()-started);
 if($('mg-input').querySelector('[name=value]').value!=='Nhập tiếng Việt '+i)throw Error('Mất chữ trong editor');
 key($('mg-input').querySelector('[name=value]'),'Escape');await frame();
 }
 // Newer edit of same cell must survive acknowledgement of A.
 key(v,'F2');await frame();input('Nháp mới B');key($('mg-input').querySelector('[name=value]'),'Enter');await frame();
 const result={stage:new URL(location.href).searchParams.get('stage')||'after',viewport:[innerWidth,innerHeight],total:10000,save:'held response',selection:summary(selection),openEditor:summary(opened),typing:summary(typing),created:made-createdAt,status:$('bt-trang-thai').textContent};
 if(result.status!=='Đang lưu')throw Error('Lưu chậm chặn hoặc sai trạng thái');
 await fetch('/release');await frame();
 result.newerDraftPreserved=document.querySelector('.mg-cell[data-r="0"][data-code="ten_khach"]').textContent==='Nháp mới B';
 if(!result.newerDraftPreserved)throw Error('Phản hồi cũ làm mất nháp B');
 $('probe-output').value=JSON.stringify(result);await fetch('/result',{method:'POST',body:JSON.stringify(result)});
 }catch(e){$('probe-output').value='FAIL '+e.stack;}};
})();
