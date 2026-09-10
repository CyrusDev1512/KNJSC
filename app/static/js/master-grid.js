/* Lưới master độc lập. DOM là cửa sổ nhìn; mọi thao tác lưu dùng ID dòng/mã cột. */
(() => {
  'use strict';
  const root = document.getElementById('master-grid');
  if (!root) return;
  const $ = id => document.getElementById(id), config = JSON.parse($('mg-config').textContent);
  const viewport = $('mg-viewport'), canvas = $('mg-canvas'), editor = $('mg-editor'), reader = $('mg-reader');
  const ROW = 28, HEADER = 54, BLOCK = 100, MAX = 2000, CACHE = 10;
  const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const key = `kn-master:${config.user}:${config.table}`;
  let preferences = {};
  try { preferences = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) {}
  if(!preferences||typeof preferences!=='object'||Array.isArray(preferences))preferences={};
  const heights=Object.create(null), geometry=new window.KNJSCRowGeometry();
  let working=new window.KNJSCWorkingCopy();
  const same=window.KNJSCWorkingCopy.same;
  for(const [id,h] of Object.entries(preferences.rowHeights||{})){
    if(/^[1-9]\d*$/.test(id)&&Number.isSafeInteger(Number(id))&&typeof h==='number'&&Number.isFinite(h)&&h>28)heights[id]=Math.max(28,Math.min(400,Math.round(h)));
  }
  preferences.rowHeights=heights;
  const state = {columns: [], visible: [], cache: new Map(), pending: new Map(), total: 0,
    version: '', generation: 0, selection: null, anchor: null, current: null, draft: null,
    retry: null, busy: false, ready: false, poll: '', lastError: '', editMode:false, conflicts:[], retryCount:0, composing:false, accessEpoch:0};
  let saveTimer=0, firstQueued=0;
  let query = new URLSearchParams(location.search), scheduled = false, drag = null, resizing = null, frame = 0, rowResize = null, rowFrame = 0;
  const message = (text = '', error = false) => {
    $('mg-message').textContent = text; $('mg-message').hidden = !text;
    $('mg-message').classList.toggle('mg-error', error);
  };
  const status = text => { $('bt-trang-thai').textContent = text; };
  function persist() { try { localStorage.setItem(key, JSON.stringify(preferences));return true; } catch (_) {return false;} }
  function updateGeometry(change) {
    const anchor=geometry.at(viewport.scrollTop),offset=viewport.scrollTop-geometry.top(anchor);
    change();layout();
    const next=Math.min(anchor,Math.max(0,geometry.total-1));
    viewport.scrollTop=geometry.top(next)+Math.max(0,Math.min(offset,geometry.height(next)-1));
  }
  async function json(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { const error = new Error(data.error || 'Không tải được dữ liệu. Kiểm tra kết nối hoặc quyền truy cập.'); error.status = response.status; error.cell = data.cell; error.conflicts=data.conflicts||[]; throw error; }
    if(response.redirected || !response.headers.get('Content-Type')?.includes('application/json'))throw Error('Phiên đăng nhập hoặc phản hồi không hợp lệ. Nội dung chưa được xác nhận lưu.');
    return data;
  }
  function layout() {
    const order = preferences.order || [], byCode = new Map(state.columns.map(c => [c.code, c]));
    const arranged = [...new Set([...order, ...state.columns.map(c => c.code)])].filter(c => byCode.has(c));
    state.visible = arranged.filter(c => !(preferences.hidden || []).includes(c)).map(code => ({...byCode.get(code), width: Math.max(72, Math.min(640, preferences.widths?.[code] || byCode.get(code).width))}));
    let x = 46, frozen = 46, lastPinned = null;
    for (const c of state.visible) {
      c.x = x; x += c.width;
      // Chừa tối thiểu một dải 64px cho phần cuộn; ở desktop hẹp vẫn giữ đủ
      // ba cột nhận diện khách, còn điện thoại tự giảm số cột ghim để lưới dùng được.
      c.pin = c.frozen && frozen + c.width <= Math.max(230, viewport.clientWidth - 64);
      if (c.pin) { c.pinX = frozen; frozen += c.width; lastPinned = c; }
    }
    for (const c of state.visible) c.pinEdge = c === lastPinned;
    state.width = Math.max(x, viewport.clientWidth); state.frozen = frozen;
    canvas.style.width = state.width + 'px'; canvas.style.height = Math.max(HEADER + geometry.top(state.total), viewport.clientHeight) + 'px';
  }
  function rowAt(index) { return state.cache.get(Math.floor(index / BLOCK))?.rows[index % BLOCK]; }
  function repaint() { if (!scheduled) { scheduled = true; requestAnimationFrame(() => { scheduled = false; render(); }); } }
  function invalidate(clearSelection = true) {
    finishRowResize(false);
    state.generation++; state.pending.forEach(p => p.controller.abort()); state.pending.clear(); state.cache.clear(); state.version = '';
    updateGeometry(()=>geometry.reset(state.total));
    if (clearSelection) { state.selection = state.anchor = state.current = null; reader.hidden = true; }
    repaint();
  }
  async function loadBlock(number) {
    if (number < 0) return;
    if (state.cache.has(number)) { const b = state.cache.get(number); state.cache.delete(number); state.cache.set(number, b); return b; }
    if (state.pending.has(number)) return state.pending.get(number).promise;
    const generation = state.generation, controller = new AbortController();
    const params = new URLSearchParams(query); params.delete('trang'); params.delete('moi_trang');
    params.set('offset', number * BLOCK); if (state.version) params.set('version', state.version);
    const promise = fetch(config.dataUrl + '?' + params, {signal: controller.signal}).then(json).then(data => {
      if (generation !== state.generation) return;
      if (state.version && state.version !== data.version) { invalidate(); return; }
      state.version = data.version; state.total = data.total; state.columns = data.columns; state.ready = true;
      updateGeometry(()=>{
        if(geometry.total!==data.total)geometry.reset(data.total);
        data.rows.forEach((row,i)=>{if(rowResize?.id!==row.id)geometry.set(number*BLOCK+i,heights[row.id]||ROW);});
      });
      working.observe(data.rows);
      state.cache.set(number, data);
      if(state.current&&Math.floor(state.current.r/BLOCK)===number&&state.currentId&&rowAt(state.current.r)?.id!==state.currentId){state.current=state.anchor=state.selection=null;state.currentId=null;}
      while (state.cache.size > CACHE) state.cache.delete(state.cache.keys().next().value);
      layout(); repaint(); return data;
    }).catch(error => {
      if (error.name === 'AbortError' || generation !== state.generation) return;
      if (error.status === 409) { message('Dữ liệu đã thay đổi; vùng chọn cũ được bỏ. Đang cập nhật vùng đang xem.'); invalidate(); return; }
      if (error.status === 403 || error.status === 404) clearAccess(error.message);
      state.lastError = error.message; message(error.message, true);
      const retry=element('button','nut','Tải lại vùng đang xem');retry.onclick=()=>{state.lastError='';message();invalidate();};$('mg-message').append(retry);
      throw error;
    }).finally(() => { if (generation === state.generation) state.pending.delete(number); });
    state.pending.set(number, {controller, promise}); return promise;
  }
  function element(tag, className, text) { const e = document.createElement(tag); e.className = className; if (text !== undefined) e.textContent = text; return e; }
  function position(e, x, y, w, h) { Object.assign(e.style, {left:x+'px', top:y+'px', width:w+'px', height:h+'px'}); }
  function syncAttributes(target, source) {
    for(const attr of [...target.attributes])if(!source.hasAttribute(attr.name))target.removeAttribute(attr.name);
    for(const attr of source.attributes)if(target.getAttribute(attr.name)!==attr.value)target.setAttribute(attr.name,attr.value);
  }
  function updateBody(body, fragment) {
    // Giữ chính node ô giữa hai lần bấm để trình duyệt nhận dblclick.
    // Chỉ giữ các hàng/cột trong cửa sổ cuộn, không tăng DOM theo dữ liệu.
    const oldRows=new Map([...body.children].map(row=>[row.getAttribute('aria-rowindex'),row]));
    const keep=new Set();
    for(const fresh of [...fragment.children]){
      const rowKey=fresh.getAttribute('aria-rowindex'),previous=rowKey&&oldRows.get(rowKey);
      if(!previous){body.append(fresh);keep.add(fresh);continue;}
      syncAttributes(previous,fresh);
      const key=cell=>cell.dataset.code||(cell.hasAttribute('data-row-resize')?'#row-resize':'#row-number');
      const oldCells=new Map([...previous.children].map(cell=>[key(cell),cell])),visible=new Set();
      for(const next of [...fresh.children]){
        const existing=oldCells.get(key(next));
        if(existing){syncAttributes(existing,next);if(existing.textContent!==next.textContent)existing.textContent=next.textContent;visible.add(existing);}
        else{previous.append(next);visible.add(next);}
      }
      for(const cell of [...previous.children])if(!visible.has(cell))cell.remove();
      [...visible].forEach((cell,i)=>{if(previous.children[i]!==cell)previous.insertBefore(cell,previous.children[i]||null);});
      keep.add(previous);
    }
    for(const row of [...body.children])if(!keep.has(row))row.remove();
    [...keep].forEach((row,i)=>{if(body.children[i]!==row)body.insertBefore(row,body.children[i]||null);});
  }
  function selected(r, c) { const s = state.selection; return s && r >= s.r1 && r <= s.r2 && c >= s.c1 && c <= s.c2; }
  function render() {
    if (!state.ready) { if (!state.lastError) loadBlock(0).catch(() => {}); return; }
    layout();
    const top = viewport.scrollTop, left = viewport.scrollLeft;
    const start = Math.max(0, geometry.at(Math.max(0,top-HEADER))-8), end = Math.min(state.total, geometry.at(top+viewport.clientHeight)+9);
    const cols = state.visible.map((c, i) => ({...c, i})).filter(c => c.pin || (c.x + c.width > left - 160 && c.x < left + viewport.clientWidth + 160));
    const fragment = document.createDocumentFragment();
    const head = element('div', 'mg-head'); head.setAttribute('role', 'row');
    position(head, 0, top, state.width, HEADER);
    const corner = element('button', 'mg-corner', '▦'); corner.dataset.all = '1'; corner.title = 'Chọn toàn bộ kết quả'; position(corner, left, 0, 46, HEADER); head.append(corner);
    for (const c of cols) {
      const h = element('div', 'mg-heading' + (c.pin ? ' mg-pinned' : '') + (c.pinEdge ? ' mg-pinned-edge' : ''));
      h.dataset.column = c.i; h.dataset.code = c.code; h.setAttribute('role','columnheader');
      position(h, c.pin ? left+c.pinX : c.x, 0, c.width, HEADER);
      const letter = element('button','mg-letter', columnLetter(c.i)); letter.dataset.selectColumn = c.i; letter.title = 'Chọn cột';
      const name = element('button','mg-column-name',c.name + (query.get('sap') === c.code ? (query.get('chieu') === 'giam' ? ' ↓' : ' ↑') : '')); name.dataset.sort = c.code;
      const filter = element('button','mg-filter-icon','▾'); filter.dataset.filter = c.code; filter.setAttribute('aria-label','Lọc '+c.name);
      const handle = element('span','mg-resize'); handle.dataset.resize = c.code; handle.setAttribute('role','separator'); handle.setAttribute('aria-label','Đổi độ rộng '+c.name);
      h.append(letter,name,filter,handle);head.append(h);
    }
    // Giữ node header qua chọn ô/nạp khối để focus và nhấn chuột không bị
    // mất giữa pointerdown/pointerup. Chỉ đổi cây nút khi cấu trúc cột đổi.
    const headerKey=JSON.stringify(cols.map(c=>[c.code,c.i,c.width,c.pin,c.pinEdge,c.name]).concat([[query.get('sap'),query.get('chieu')]]));
    const previousHead=canvas.querySelector(':scope > .mg-head');
    if(previousHead){
      previousHead.style.cssText=head.style.cssText;
      if(previousHead.dataset.key!==headerKey)previousHead.replaceChildren(...head.children);
      else [...previousHead.children].forEach((child,i)=>child.style.cssText=head.children[i].style.cssText);
      previousHead.dataset.key=headerKey;
    }else{head.dataset.key=headerKey;canvas.prepend(head);}
    let body=canvas.querySelector(':scope > .mg-body');
    if(!body){body=element('div','mg-body');canvas.append(body);}
    for (let r = start; r < end; r++) {
      const row = rowAt(r), line = element('div','mg-row');line.setAttribute('role','row');line.setAttribute('aria-rowindex',r+2);
      const rowHeight=geometry.height(r);
      position(line,0,HEADER+geometry.top(r),state.width,rowHeight);
      const number = element('button','mg-number',String(r+1)); number.dataset.selectRow=r;number.setAttribute('aria-selected',!!(state.selection&&r>=state.selection.r1&&r<=state.selection.r2));position(number,left,0,46,rowHeight);line.append(number);
      if(row){
        const handle=element('div','mg-row-resize');handle.dataset.rowResize=r;handle.dataset.id=row.id;handle.tabIndex=0;
        handle.setAttribute('role','separator');handle.setAttribute('aria-orientation','horizontal');handle.setAttribute('aria-label','Chiều cao hàng '+(r+1));
        handle.setAttribute('aria-valuemin','28');handle.setAttribute('aria-valuemax','400');handle.setAttribute('aria-valuenow',rowHeight);
        handle.title='Kéo chỉnh chiều cao · ↑/↓ 4 px · Home về 28 px';position(handle,left,rowHeight-7,46,7);line.append(handle);
      }
      for (const c of cols) {
        const value = row ? cellValue(row,c.code) : null;
        const cell = element('div','mg-cell '+(value?.class || '')+(rowHeight>ROW?' mg-wrap':'')+(c.pin?' mg-pinned':'')+(c.pinEdge?' mg-pinned-edge':'')+(selected(r,c.i)?' mg-selected':'')+(state.current?.r===r&&state.current?.c===c.i?' mg-current':''),row ? (value?.display ?? value?.value ?? '') : '…');
        cell.dataset.r=r;cell.dataset.c=c.i;cell.dataset.code=c.code;
        if(row) {cell.dataset.id=row.id;cell.id=`mg-${row.id}-${c.code}`;}
        cell.setAttribute('role','gridcell');cell.setAttribute('aria-colindex',c.i+2);cell.setAttribute('aria-selected',!!selected(r,c.i));
        if(selected(r,c.i))for(const [side,on] of Object.entries({top:r===state.selection.r1,bottom:r===state.selection.r2,left:c.i===state.selection.c1,right:c.i===state.selection.c2}))if(on)cell.classList.add('mg-edge-'+side);
        if(value&&!value.editable) cell.setAttribute('aria-readonly','true');
        position(cell,c.pin?left+c.pinX:c.x,0,c.width,rowHeight);line.append(cell);
      }
      fragment.append(line);
    }
    if (!state.total) { const empty=element('p','mg-empty','Chưa có vận đơn khớp bộ lọc.'); position(empty,left+24,HEADER+35,Math.max(120,viewport.clientWidth-48),60);fragment.append(empty); }
    updateBody(body,fragment);
    viewport.setAttribute('aria-rowcount',state.total+1);viewport.setAttribute('aria-colcount',state.visible.length+1);
    const s=state.selection;
    $('mg-count').textContent=state.total.toLocaleString('vi-VN')+' dòng khớp bộ lọc';
    $('mg-selection').textContent=s?`${columnLetter(s.c1)}${s.r1+1}:${columnLetter(s.c2)}${s.r2+1} · ${((s.r2-s.r1+1)*(s.c2-s.c1+1)).toLocaleString('vi-VN')} ô được chọn`:'';
    $('mg-undo').disabled=!working.undo.length;
    $('mg-redo').disabled=!working.redo.length;
    refreshStatus();
    for(let b=Math.floor(start/BLOCK);b<=Math.floor(Math.max(start,end-1)/BLOCK)&&state.total;b++) if(!state.cache.has(b)&&!state.lastError) loadBlock(b).catch(()=>{});
  }
  function columnLetter(i) { let s='';for(i++;i;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s;return s; }
  function choose(r,c,extend=false) {
    if(dirty()||!state.total||!state.visible.length)return;
    r=Math.max(0,Math.min(state.total-1,r));c=Math.max(0,Math.min(state.visible.length-1,c));
    state.current={r,c};state.currentId=rowAt(r)?.id;if(!extend||!state.anchor)state.anchor={r,c};
    const a=state.anchor;state.selection={r1:Math.min(a.r,r),r2:Math.max(a.r,r),c1:Math.min(a.c,c),c2:Math.max(a.c,c)};
    reader.hidden=true;viewport.focus({preventScroll:true});repaint();
  }
  function selectAll() { if(!state.total||!state.visible.length||dirty())return;choose(0,0);state.selection={r1:0,r2:state.total-1,c1:0,c2:state.visible.length-1};repaint(); }
  function ensureVisible() {
    const cur=state.current;if(!cur)return;const c=state.visible[cur.c],h=geometry.height(cur.r),y=HEADER+geometry.top(cur.r);
    if(y<viewport.scrollTop+HEADER)viewport.scrollTop=y-HEADER;
    if(h>viewport.clientHeight-HEADER)viewport.scrollTop=y-HEADER;
    else if(y+h>viewport.scrollTop+viewport.clientHeight)viewport.scrollTop=y+h-viewport.clientHeight;
    if(!c.pin) {if(c.x<viewport.scrollLeft+state.frozen)viewport.scrollLeft=c.x-state.frozen;if(c.x+c.width>viewport.scrollLeft+viewport.clientWidth)viewport.scrollLeft=c.x+c.width-viewport.clientWidth;}
  }
  function floatAt(panel, box) {
    panel.hidden=false;const w=Math.min(440,innerWidth-24),h=Math.min(320,innerHeight-24);
    panel.style.width=w+'px';panel.style.maxHeight=h+'px';
    panel.style.left=Math.max(12,Math.min(box?.left||12,innerWidth-w-12))+'px';
    panel.style.top=Math.max(12,Math.min(box?.bottom||90,innerHeight-h-12))+'px';
  }
  function showReader(cell) {
    if(!cell||state.draft||drag||(cell.scrollWidth<=cell.clientWidth&&cell.scrollHeight<=cell.clientHeight))return;
    const row=rowAt(+cell.dataset.r),c=state.visible[+cell.dataset.c];if(!row)return;
    reader.querySelector('strong').textContent=c.name;reader.querySelector('div').textContent=cellValue(row,c.code).display;
    floatAt(reader,cell.getBoundingClientRect());
  }
  async function edit(automatic=false) {
    if(dirty()||!state.current)return;
    const cur={...state.current}, generation=state.generation;
    const block=await loadBlock(Math.floor(cur.r/BLOCK));if(generation!==state.generation||!block)return;
    const row=block.rows[cur.r%BLOCK],c=state.visible[cur.c];if(!row||!c)return;
    if(state.current?.r!==cur.r||state.current?.c!==cur.c)return;
    if(automatic&&(c.assignment||c.detail||!cellValue(row,c.code).editable))return;
    reader.hidden=true;
    if(c.assignment){window.dispatchEvent(new CustomEvent('master-assignment',{detail:{ids:[row.id]}}));return;}
    if(c.detail){const d=$('vd-detail');d.showModal();$('vd-detail-body').textContent='Đang tải chi tiết…';await htmx.ajax('GET',row.detail_url,{target:'#vd-detail-body',swap:'innerHTML'});return;}
    const value=cellValue(row,c.code);if(!value.editable){message('Ô này chỉ đọc.');return;}
    state.draft={id:row.id,column:c.code,old:value.value,cur};
    editor.querySelector('strong').textContent=c.name;
    let input;
    if(c.type==='choice'||c.options?.length){input=element('select','o-nhap');input.append(new Option('—',''));for(const v of c.options)input.append(new Option(v,v));}
    else {input=element(c.type==='long_text'?'textarea':'input','o-nhap');if(c.type==='date')input.type='date';else if(c.type==='datetime')input.type='datetime-local';else if(['integer','decimal','money'].includes(c.type))input.inputMode='decimal';}
    input.name='value';input.setAttribute('aria-label',c.name);input.value=value.value??'';
    $('mg-input').replaceChildren(input);
    floatAt(editor,$(`mg-${row.id}-${c.code}`)?.getBoundingClientRect());input.focus();
    if(input.select)input.select();refreshStatus();repaint();
  }
  function cellValue(row,column) {
    const original=row.cells[column],value=working.value(row.id,column,original.value);
    const style={...original.style};let classes=original.class||'';
    for(const prop of ['fs','c','bg']){
      const mapped=config.styleClasses?.[prop]||{};
      classes=classes.split(' ').filter(c=>!Object.values(mapped).includes(c)).join(' ');
      style[prop]=working.value(row.id,column,style[prop]??null,prop);
      if(mapped[style[prop]])classes+=' '+mapped[style[prop]];
    }
    return {...original,value,style,class:classes,display:same(value,original.value)?original.display:String(value??'')};
  }
  function refreshStatus() {
    const currentChanged=state.draft&&!same(editor.elements.value?.value,state.draft.old);
    const count=working.count;
    status(state.conflicts.length?'Xung đột':state.busy?'Đang lưu':state.saveError?'Lỗi lưu':count||currentChanged||state.retry?'Chưa lưu':'Đã lưu');
    $('mg-conflict-button').textContent=`Xung đột (${state.conflicts.length})`;
    $('mg-save').disabled=state.busy||!(count||currentChanged||state.retry);
    $('mg-save').title=count?`${count} ô chờ lưu, gồm cả ô ngoài bộ lọc đang xem`:'Lưu dữ liệu (Ctrl+S)';
  }
  function finishEditor(discard=false) {
    if(!state.draft)return true;if(state.composing)return false;
    const d=state.draft;
    if(!discard){try{const changed=working.stage([{id:d.id,column:d.column,old:d.old,value:editor.elements.value.value}]);if(changed&&state.errorStatus===400)state.saveError=false;}
      catch(error){message(error.message,true);return false;}}
    state.draft=null;editor.hidden=true;refreshStatus();repaint();scheduleSave();return true;
  }
  function cancelEdit() {if(finishEditor(true)){viewport.focus({preventScroll:true});repaint();}}
  function dirty() {return !finishEditor();}
  function rememberHeight(index,id) {
    const h=geometry.height(index);if(h===ROW)delete heights[id];else heights[id]=h;
    if(!persist())message('Không ghi nhớ được chiều cao trên máy này; tùy chọn chỉ giữ trong lần mở bảng.',true);
  }
  function applyRowResize() {
    rowFrame=0;if(!rowResize)return;
    const d=rowResize;
    updateGeometry(()=>geometry.set(d.index,d.before+(d.y-d.start)/d.scale));repaint();
  }
  function finishRowResize(commit) {
    if(!rowResize)return;
    cancelAnimationFrame(rowFrame);rowFrame=0;
    if(commit)applyRowResize();
    const d=rowResize;rowResize=null;
    if(commit)rememberHeight(d.index,d.id);else updateGeometry(()=>geometry.set(d.index,d.before));
    try{if(d.handle.hasPointerCapture(d.pointer))d.handle.releasePointerCapture(d.pointer);}catch(_){}
    root.classList.remove('mg-resizing-row');repaint();
  }
  async function navigate(params,push=true) {
    if(dirty())return false;
    for(const k of ['trang','moi_trang','offset','version','q'])params.delete(k);
    query=params;const url=config.filterUrl+(params.size?'?'+params:'');
    if(push)history.pushState({},'',url);
    $('mg-search').elements.tim.value=params.get('tim')||'';
    document.querySelectorAll('[data-query-link]').forEach(a=>{const u=new URL(a.href);u.search=params.toString();a.href=u.href;});
    viewport.scrollTop=viewport.scrollLeft=0;state.lastError='';state.ready=false;invalidate();
    // HTML chỉ cho điều khiển lọc/chip, không chứa dữ liệu dòng.
    const gen=state.generation;
    fetch(url,{headers:{'X-Master-Filters':'1'}}).then(r=>r.text()).then(html=>{
      if(gen!==state.generation)return;const doc=new DOMParser().parseFromString(html,'text/html');
      for(const id of ['mg-filters','mg-chips']){const e=doc.getElementById(id);if(e)$(id).innerHTML=e.innerHTML;}
    }).catch(()=>{});
    repaint();return true;
  }
  async function rangeCells() {
    const s=state.selection;if(!s)return [];
    if((s.r2-s.r1+1)*(s.c2-s.c1+1)>MAX)throw Error(`Vùng chọn vượt ${MAX} ô. Lọc nhỏ hơn hoặc dùng Tải Excel để lấy toàn bộ kết quả.`);
    const gen=state.generation, result=[];
    for(let r=s.r1;r<=s.r2;r++){
      const b=await loadBlock(Math.floor(r/BLOCK));if(gen!==state.generation||!b)throw Error('Dữ liệu đã đổi; chọn lại vùng cần thao tác.');
      const row=b.rows[r%BLOCK];if(!row)throw Error('Dòng không còn trong kết quả.');
      for(let c=s.c1;c<=s.c2;c++){const col=state.visible[c],v=cellValue(row,col.code);result.push({id:row.id,column:col.code,old:v.value,value:v.value,style:v.style,editable:v.editable,r,c});}
    }return result;
  }
  async function submit(cells,kind='edit') {
    try{const changed=working.stage(cells);if(changed&&state.errorStatus===400)state.saveError=false;state.kind=kind;refreshStatus();repaint();scheduleSave();return true;}
    catch(error){message(error.message,true);return false;}
  }
  async function undo(redo=false) {
    if(dirty())return;working.travel(redo);state.kind=redo?'redo':'undo';refreshStatus();repaint();scheduleSave();
  }
  function scheduleSave(){
    if(state.saveError||state.conflicts.length||!working.count)return;
    firstQueued ||= Date.now();clearTimeout(saveTimer);
    saveTimer=setTimeout(()=>saveAll(false),Math.max(0,Math.min(500,2000-(Date.now()-firstQueued))));
  }
  function updateRows(rows){
    const byId=new Map(rows.map(r=>[r.id,r]));
    for(const block of state.cache.values())block.rows=block.rows.map(r=>byId.get(r.id)||r);
    // Request đã bắt đầu trước lượt lưu không được ghi đè kết quả vừa xác nhận.
    state.generation++;state.pending.forEach(p=>p.controller.abort());state.pending.clear();state.version='';
    repaint();
  }
  async function saveAll(explicit=true) {
    if(explicit&&!finishEditor())return;
    if(state.busy||state.conflicts.length)return;
    clearTimeout(saveTimer);firstQueued=0;
    if(!working.pending().length&&!state.retry){refreshStatus();return;}
    state.busy=true;state.saveError=false;status('Đang lưu');message();closeMore();repaint();
    const accessEpoch=state.accessEpoch;
    try{
        const cells=working.pending();
        const payload=state.retry?.payload||{operation:crypto.randomUUID(),cells,kind:state.kind||'edit'};state.kind='edit';
        state.retry={payload};working.hold(payload.cells);
        const data=await fetch(config.saveUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify(payload)}).then(json);
        if(accessEpoch!==state.accessEpoch)return;
        working.acknowledge(payload.cells,data.rows);working.observe(data.rows);state.retry=null;state.retryCount=0;
        updateRows(data.rows);state.lastError='';
    }catch(error){
      clearTimeout(saveTimer);firstQueued=0;
      if(error.status===403||error.status===404){
        state.saveError=true;
        try{error.message=await retainReadableDrafts(error.message);}
        catch(_){clearAccess(error.message);return;}
      }
      state.conflicts=error.conflicts||[];
      if(error.status&&error.status<500&&state.retry){working.release(state.retry.payload.cells);state.retry=null;}
      state.saveError=true;
      state.errorStatus=error.status||0;
      const position=error.cell?.id?`Dòng #${error.cell.id}, cột ${error.cell.column}: `:'';message(position+error.message,true);
      const retry=element('button','nut','Thử lại'),discard=element('button','nut','Bỏ bản nháp');
      retry.onclick=()=>{state.retryCount=0;saveAll();};discard.onclick=()=>{working=new window.KNJSCWorkingCopy();state.retry=null;state.conflicts=[];state.saveError=false;message();invalidate();refreshStatus();};
      if(state.conflicts.length){const open=element('button','nut','Đối chiếu xung đột');open.onclick=showConflicts;$('mg-message').append(open);}
      else $('mg-message').append(retry);
      // Không bỏ lượt chưa biết đã commit hay chưa; giải quyết biên nhận trước.
      if(!state.retry)$('mg-message').append(discard);
      if((!error.status||error.status>=500)&&state.retryCount<4){const delay=1000*2**state.retryCount++;saveTimer=setTimeout(()=>saveAll(false),delay);}
    }finally{state.busy=false;refreshStatus();repaint();if(!state.saveError)scheduleSave();}
  }
  async function retainReadableDrafts(text){
    const ids=new Set(working.pending().map(c=>c.id));
    for(const c of state.retry?.payload.cells||[])ids.add(c.id);
    if(state.draft)ids.add(state.draft.id);if(state.historyId)ids.add(state.historyId);
    for(const block of state.cache.values())block.rows.forEach(row=>ids.add(row.id));
    const visible=new Set(),all=[...ids];
    for(let i=0;i<all.length;i+=4000){
      const data=await fetch(config.scopeUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify({ids:all.slice(i,i+4000)})}).then(json);
      data.visible.forEach(id=>visible.add(id));
    }
    const lost=new Set(all.filter(id=>!visible.has(id)));
    working.release(state.retry?.payload.cells||[]);state.retry=null;
    working.forget(lost);
    if(state.draft&&lost.has(state.draft.id)){cancelEdit();$('mg-input').replaceChildren();}
    state.accessEpoch++;state.historyId=null;reader.hidden=true;reader.querySelector('div').textContent='';
    for(const id of ['mg-history','mg-conflict','mg-format']){$(id).close();$(id+'-body').replaceChildren();}
    $('vd-detail')?.close();$('vd-detail-body')?.replaceChildren();$('vd-assignment')?.close();$('vd-assignment-fields')?.replaceChildren();
    invalidate();
    return lost.size?'Có dòng đã mất quyền xem. Nháp trên dòng đó được gỡ; nháp còn quyền được giữ. Kiểm tra trước khi bấm Thử lại.':text+' Nháp vẫn được giữ vì bạn còn quyền xem.';
  }
  async function copy() {
    const cells=await rangeCells();if(!cells.length)return;
    const rows=[],table=document.createElement('table');let r=-1,tr;
    for(const cell of cells){
      if(cell.r!==r){rows.push([]);r=cell.r;tr=table.insertRow();}
      const value=String(cell.value??''),td=tr.insertCell();
      rows.at(-1).push(/[\t\n\r"]/.test(value)?'"'+value.replaceAll('"','""')+'"':value);
      // HTML clipboard gợi ý ô văn bản cho Excel; textContent không nhận HTML từ dữ liệu.
      td.setAttribute('style',(typeof cell.value==='string'?'mso-number-format:"\\@";':'')+'white-space:pre-wrap;');
      value.split(/\r\n|\r|\n/).forEach((line,index)=>{if(index)td.append(document.createElement('br'));td.append(document.createTextNode(line));});
    }
    const plain=rows.map(row=>row.join('\t')).join('\r\n');
    if(window.ClipboardItem&&navigator.clipboard.write){
      await navigator.clipboard.write([new ClipboardItem({'text/plain':new Blob([plain],{type:'text/plain'}),'text/html':new Blob([table.outerHTML],{type:'text/html'})})]);
    }else await navigator.clipboard.writeText(plain);
    message('Đã sao chép '+cells.length+' ô.');
  }
  function parseTSV(text) {
    const rows=[[]];let value='',quoted=false;
    for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'&&(quoted||value==='')){if(quoted&&text[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}
      else if(!quoted&&(c==='\t'||c==='\n'||c==='\r')){rows.at(-1).push(value);value='';if(c!=='\t'){if(c==='\r'&&text[i+1]==='\n')i++;rows.push([]);}}else value+=c;}
    if(value!==''||rows.at(-1).length)rows.at(-1).push(value);else rows.pop();return rows;
  }
  async function paste(text) {
    if(dirty()||!state.current)return;
    const data=parseTSV(text),width=Math.max(0,...data.map(r=>r.length));if(!width)return;
    const start={...state.current};
    if(data.length*width>MAX)throw Error(`Chỉ dán tối đa ${MAX} ô một lần.`);
    if(start.r+data.length>state.total||start.c+width>state.visible.length)throw Error('Vùng dán vượt cuối bảng; không tự tạo đơn hoặc cột mới.');
    if(data.some(r=>r.length!==width))throw Error('Dữ liệu dán có số cột không đồng đều.');
    const gen=state.generation,cells=[];
    for(let i=0;i<data.length;i++){const b=await loadBlock(Math.floor((start.r+i)/BLOCK));if(gen!==state.generation||!b)throw Error('Dữ liệu đã đổi, chọn lại vùng dán.');const row=b.rows[(start.r+i)%BLOCK];
      for(let j=0;j<width;j++){const c=state.visible[start.c+j],v=cellValue(row,c.code);if(!v.editable)throw Error(`Ô ${columnLetter(start.c+j)}${start.r+i+1} bị khóa; chưa dán ô nào.`);if(/^\s*=/.test(data[i][j]))throw Error('Không nhập công thức; hãy dán giá trị từ Excel.');cells.push({id:row.id,column:c.code,old:v.value,value:data[i][j]});}}
    await submit(cells,'paste');
  }
  async function removeValues(){if(dirty())return;const cells=await rangeCells(),writable=cells.filter(c=>c.editable);if(!writable.length){message(`Bỏ qua ${cells.length} ô khóa; không có nội dung được xóa.`);return;}if(await submit(writable.map(c=>({...c,value:''})),'clear')){if(cells.length>writable.length)message(`Đã xóa nội dung; bỏ qua ${cells.length-writable.length} ô khóa.`);}}
  const safe=fn=>(...args)=>Promise.resolve().then(()=>fn(...args)).catch(e=>message(e.message,true));
  async function advance(cur, dr=0, dc=0){
    let r=cur.r+dr,c=cur.c+dc;
    if(c>=state.visible.length){c=0;r++;}if(c<0){c=state.visible.length-1;r--;}
    if(r<0||r>=state.total){viewport.focus();return;}
    choose(r,c);ensureVisible();if(state.editMode)await edit(true);
  }
  editor.addEventListener('compositionstart',()=>state.composing=true);
  editor.addEventListener('compositionend',()=>state.composing=false);
  editor.addEventListener('submit',e=>{e.preventDefault();if(finishEditor())viewport.focus({preventScroll:true});});
  editor.addEventListener('input',refreshStatus);
  editor.addEventListener('change',refreshStatus);
  editor.addEventListener('keydown',e=>{
    if(e.isComposing||e.keyCode===229)return;
    if(e.key==='Escape'){e.preventDefault();cancelEdit();}
    else if(e.key==='Enter'&&(e.target.tagName!=='TEXTAREA'||e.ctrlKey)){e.preventDefault();const d=state.draft;if(d&&finishEditor()){if(state.editMode)safe(()=>advance(d.cur,1))();else viewport.focus({preventScroll:true});}}
    else if(e.key==='Tab'&&e.target===editor.elements.value){e.preventDefault();const d=state.draft;if(d&&finishEditor())safe(()=>advance(d.cur,0,e.shiftKey?-1:1))();}
  });
  $('mg-cancel').onclick=cancelEdit;reader.querySelector('button').onclick=()=>{reader.hidden=true;viewport.focus({preventScroll:true});};
  viewport.addEventListener('keydown',e=>{
    if(e.isComposing||e.keyCode===229)return;const ctrl=e.ctrlKey||e.metaKey,k=e.key.toLowerCase();
    if(rowResize){if(e.key==='Escape'){e.preventDefault();finishRowResize(false);}return;}
    const rowHandle=e.target.closest('[data-row-resize]');
    if(rowHandle){
      if(['ArrowUp','ArrowDown','Home'].includes(e.key)){
        e.preventDefault();if(dirty())return;
        const r=Number(rowHandle.dataset.rowResize),row=rowAt(r);if(!row||String(row.id)!==rowHandle.dataset.id)return;
        const h=e.key==='Home'?ROW:geometry.height(r)+(e.key==='ArrowUp'?-4:4);
        updateGeometry(()=>geometry.set(r,h));rememberHeight(r,row.id);repaint();
      }
      return;
    }
    if(ctrl&&['a','c','z','y'].includes(k)){e.preventDefault();if(k==='a')selectAll();else if(k==='c')safe(copy)();else safe(()=>undo(k==='y'||e.shiftKey))();return;}
    if(e.key==='Escape'){reader.hidden=true;$('hop-loc').hidden=true;return;}
    if(e.key==='Delete'){e.preventDefault();safe(removeValues)();return;}
    if(e.key==='F2'||e.key==='Enter'){e.preventDefault();safe(edit)();return;}
    let cur=state.current||{r:0,c:0},r=cur.r,c=cur.c,moved=true;
    if(e.key==='ArrowDown')r++;else if(e.key==='ArrowUp')r--;else if(e.key==='ArrowLeft')c--;else if(e.key==='ArrowRight')c++;
    else if(e.key==='Tab')c+=e.shiftKey?-1:1;else if(e.key==='PageDown')r=Math.max(r+1,geometry.at(geometry.top(r)+Math.max(ROW,viewport.clientHeight-HEADER)));else if(e.key==='PageUp')r=Math.min(r-1,geometry.at(Math.max(0,geometry.top(r)-Math.max(ROW,viewport.clientHeight-HEADER))));
    else if(e.key==='Home'){c=0;if(ctrl)r=0;}else if(e.key==='End'){c=state.visible.length-1;if(ctrl)r=state.total-1;}else moved=false;
    if(moved){e.preventDefault();if(e.key==='Tab'){safe(()=>advance(cur,0,e.shiftKey?-1:1))();return;}choose(r,c,e.shiftKey);ensureVisible();if(state.editMode&&!e.shiftKey)safe(()=>edit(true))();}
  });
  viewport.addEventListener('paste',e=>{e.preventDefault();safe(()=>paste(e.clipboardData.getData('text/plain')))();});
  viewport.addEventListener('pointerdown',e=>{
    if(e.button!==0)return;
    const rowHandle=e.target.closest('[data-row-resize]');
    if(rowHandle){
      e.preventDefault();if(dirty())return;
      const r=Number(rowHandle.dataset.rowResize),row=rowAt(r);if(!row||String(row.id)!==rowHandle.dataset.id)return;
      const line=rowHandle.parentElement,scale=line.getBoundingClientRect().height/geometry.height(r);
      rowResize={index:r,id:row.id,before:geometry.height(r),start:e.clientY,y:e.clientY,scale:scale||1,handle:rowHandle,pointer:e.pointerId};
      reader.hidden=true;drag=null;resizing=null;cancelAnimationFrame(frame);frame=0;
      rowHandle.focus({preventScroll:true});rowHandle.setPointerCapture(e.pointerId);root.classList.add('mg-resizing-row');return;
    }
    if(dirty())return;
    const handle=e.target.closest('[data-resize]');if(handle){e.preventDefault();const c=state.visible.find(c=>c.code===handle.dataset.resize);resizing={code:c.code,width:c.width,x:e.clientX};reader.hidden=true;return;}
    const cell=e.target.closest('[data-r]');if(cell){e.preventDefault();choose(+cell.dataset.r,+cell.dataset.c,e.shiftKey);drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false,shift:e.shiftKey};}
  });
  function extendDrag(){if(!drag)return;const rect=viewport.getBoundingClientRect();let dy=0,dx=0;if(drag.y>rect.bottom-28)dy=ROW;else if(drag.y<rect.top+HEADER+20)dy=-ROW;if(drag.x>rect.right-24)dx=24;else if(drag.x<rect.left+state.frozen+16)dx=-24;
    if(drag.moved){viewport.scrollTop+=dy;viewport.scrollLeft+=dx;const target=document.elementFromPoint(Math.min(rect.right-8,Math.max(rect.left+48,drag.x)),Math.min(rect.bottom-8,Math.max(rect.top+HEADER+2,drag.y)))?.closest('[data-r]');if(target)choose(+target.dataset.r,+target.dataset.c,true);}
    frame=requestAnimationFrame(extendDrag);
  }
  document.addEventListener('pointermove',e=>{
    if(rowResize){if(e.pointerId===rowResize.pointer){rowResize.y=e.clientY;if(!rowFrame)rowFrame=requestAnimationFrame(applyRowResize);}return;}
    if(resizing){preferences.widths||={};preferences.widths[resizing.code]=Math.max(72,Math.min(640,resizing.width+e.clientX-resizing.x));repaint();return;}
    if(drag){drag.x=e.clientX;drag.y=e.clientY;drag.moved ||= Math.abs(e.clientX-drag.startX)+Math.abs(e.clientY-drag.startY)>5;if(!frame)frame=requestAnimationFrame(extendDrag);}
  });
  document.addEventListener('pointerup',e=>{if(rowResize){if(e.pointerId===rowResize.pointer){rowResize.y=e.clientY;finishRowResize(true);}return;}if(resizing){resizing=null;persist();}if(drag){const d=drag;drag=null;cancelAnimationFrame(frame);frame=0;if(!d.moved&&!d.shift)setTimeout(()=>state.editMode?safe(()=>edit(true))():showReader(document.elementFromPoint(d.x,d.y)?.closest('[data-r]')),0);}});
  viewport.addEventListener('dblclick',e=>{if(!e.target.closest('[data-row-resize]'))safe(edit)();});
  viewport.addEventListener('click',e=>{
    if(e.target.closest('[data-all]'))selectAll();
    const col=e.target.closest('[data-select-column]');if(col&&!dirty()&&state.total){choose(0,+col.dataset.selectColumn);if(state.selection)state.selection.r2=state.total-1;repaint();}
    const row=e.target.closest('[data-select-row]');if(row&&!dirty()&&state.visible.length){choose(+row.dataset.selectRow,0);if(state.selection)state.selection.c2=state.visible.length-1;repaint();}
    const sort=e.target.closest('[data-sort]');if(sort){const p=new URLSearchParams(query);p.set('sap',sort.dataset.sort);p.set('chieu',query.get('sap')===sort.dataset.sort&&query.get('chieu')!=='giam'?'giam':'tang');navigate(p);}
    const filter=e.target.closest('[data-filter]');if(filter){const box=filter.getBoundingClientRect();$('hop-loc').hidden=false;Object.assign($('hop-loc').style,{position:'fixed',left:Math.max(8,Math.min(box.left,innerWidth-370))+'px',top:Math.min(box.bottom,innerHeight-340)+'px',maxHeight:'70vh',overflow:'auto'});htmx.ajax('GET',config.filterUrl+'loc/'+filter.dataset.filter+'/?'+query,{target:'#mg-column-filter-body',swap:'innerHTML'});}
  });
  $('mg-undo').onclick=safe(()=>undo());$('mg-redo').onclick=safe(()=>undo(true));
  $('mg-filters-button').onclick=()=>{if(dirty())return;$('mg-filters').hidden=!$('mg-filters').hidden;$('mg-filters-button').setAttribute('aria-expanded',!$('mg-filters').hidden);repaint();};
  $('mg-columns-button').onclick=()=>{
    if(dirty())return;
    const dialog=$('mg-columns'),body=$('mg-column-list');body.replaceChildren();
    for(const c of state.columns){const line=element('div','mg-column-option'),label=element('label','',c.name),check=element('input','');check.type='checkbox';check.checked=!(preferences.hidden||[]).includes(c.code);check.onchange=()=>{preferences.hidden=(preferences.hidden||[]).filter(code=>code!==c.code);if(!check.checked)preferences.hidden.push(c.code);persist();state.selection=state.current=null;repaint();};label.prepend(check);line.append(label);
      for(const [text,dir] of [['↑',-1],['↓',1]]){const button=element('button','nut',text);button.setAttribute('aria-label',text+' '+c.name);button.onclick=()=>{const order=(preferences.order||state.columns.map(c=>c.code)).slice(),i=order.indexOf(c.code),j=Math.max(0,Math.min(order.length-1,i+dir));[order[i],order[j]]=[order[j],order[i]];preferences.order=order;persist();state.selection=state.current=null;repaint();};line.append(button);}body.append(line);}
    dialog.showModal();
  };
  $('mg-assign')?.addEventListener('click',safe(async()=>{if(dirty())return;const cells=await rangeCells();window.dispatchEvent(new CustomEvent('master-assignment',{detail:{ids:[...new Set(cells.map(c=>c.id))]}}));}));
  document.addEventListener('submit',e=>{const form=e.target;if(form===editor||!form.matches('#mg-search, #mg-filters form, #hop-loc form'))return;e.preventDefault();let p=new URLSearchParams(new FormData(form));if(form.id==='mg-search'){p=new URLSearchParams(query);p.set('tim',form.elements.tim.value);}navigate(p);});
  document.addEventListener('click',e=>{
    const a=e.target.closest('a');if(a&&(a.closest('#mg-chips')||a.closest('#hop-loc'))){e.preventDefault();navigate(new URL(a.href).searchParams);return;}
    const button=e.target.closest('.loc-chon-tat-ca,.loc-bo-chon');if(button)button.closest('form').querySelectorAll('input[type=checkbox]').forEach(c=>c.checked=button.classList.contains('loc-chon-tat-ca'));
  },true);
  window.addEventListener('popstate',()=>navigate(new URLSearchParams(location.search),false));
  viewport.addEventListener('scroll',()=>{reader.hidden=true;repaint();},{passive:true});
  new ResizeObserver(()=>{layout();repaint();}).observe(viewport);
  new ResizeObserver(()=>{if(!editor.hidden){const b=editor.getBoundingClientRect();editor.style.maxWidth=(innerWidth-b.left-12)+'px';editor.style.maxHeight=(innerHeight-b.top-12)+'px';}}).observe(editor);
  window.addEventListener('resize',()=>{closeMore();reader.hidden=true;if(state.draft)floatAt(editor,editor.getBoundingClientRect());});
  document.body.addEventListener('htmx:afterSwap',()=>{document.querySelectorAll('#mg-column-filter-body [hx-target="#hop-loc"]').forEach(e=>e.setAttribute('hx-target','#mg-column-filter-body'));});
  function closeMore(){ $('mg-more').hidden=true;$('mg-more-button').setAttribute('aria-expanded','false'); }
  $('mg-more-button').onclick=()=>{
    if(dirty())return;const menu=$('mg-more'),button=$('mg-more-button'),show=menu.hidden;
    menu.hidden=!show;button.setAttribute('aria-expanded',String(show));
    if(show){const anchor=button.getBoundingClientRect();Object.assign(menu.style,{position:'fixed',right:'auto',left:Math.max(8,Math.min(anchor.right-menu.offsetWidth,innerWidth-menu.offsetWidth-8))+'px',top:Math.max(8,Math.min(anchor.bottom+6,innerHeight-menu.offsetHeight-8))+'px'});}
  };
  $('mg-save').onclick=safe(saveAll);
  $('mg-mode').onclick=()=>{
    if(dirty())return;state.editMode=!state.editMode;
    $('mg-mode').textContent='Chế độ: '+(state.editMode?'Chỉnh sửa':'Xem');$('mg-mode').setAttribute('aria-pressed',state.editMode);
  };
  function openDialog(id){closeMore();reader.hidden=true;$(id).showModal();}
  for(const id of ['mg-format','mg-history','mg-conflict'])$(id).addEventListener('close',()=>viewport.focus({preventScroll:true}));
  $('mg-format-button').onclick=safe(async()=>{
    if(dirty())return;
    const cells=await rangeCells();if(!cells.length)throw Error('Chọn ô hoặc vùng cần định dạng.');
    const locked=cells.find(c=>!c.editable);if(locked)throw Error(`Ô ${columnLetter(locked.c)}${locked.r+1} bị khóa; chưa định dạng ô nào.`);
    const body=$('mg-format-body');body.replaceChildren();
    for(const [property,label] of [['fs','Cỡ chữ'],['c','Màu chữ'],['bg','Màu nền']]){
      const field=element('label','mg-tool-field',label),select=element('select','o-nhap');select.setAttribute('aria-label',label);
      select.append(new Option('— Chọn thay đổi —',''),new Option('Về mặc định','default'));
      const values=property==='fs'?Object.keys(config.styleClasses.fs):Object.keys(config.palette);
      for(const v of values){const option=new Option(property==='fs'?v+' px':v+' '+config.palette[v],v);if(property!=='fs'){option.style.background=config.palette[v];option.style.color=['m01','m02','m09','m10'].includes(v)?'#fff':'#111';}select.append(option);}
      field.append(select);body.append(field);
      select.onchange=safe(async()=>{
        if(!select.value)return;const value=select.value==='default'?null:property==='fs'?Number(select.value):select.value;
        // Các ID cố định từ lúc mở popup; không lấy lại theo số hàng đã đổi.
        const changes=cells.map(c=>({id:c.id,column:c.column,property,old:working.value(c.id,c.column,c.style?.[property]??null,property),value}));
        if(await submit(changes,'format'))$('mg-format').close();
      });
    }
    openDialog('mg-format');
  });
  $('mg-history-button').onclick=safe(async()=>{
    if(dirty())return;if(!state.current)throw Error('Chọn một ô trong dòng cần xem lịch sử.');
    const block=await loadBlock(Math.floor(state.current.r/BLOCK)),row=block?.rows[state.current.r%BLOCK];if(!row)return;
    state.historyId=row.id;const body=$('mg-history-body');body.replaceChildren();
    body.append(element('p','','Chỉ gồm thay đổi ô/định dạng qua lưới mới; chưa gồm nhập file, phân công và chi tiết sản phẩm.'));
    const filter=element('select','o-nhap');filter.setAttribute('aria-label','Cột lịch sử');filter.append(new Option('Tất cả cột',''));
    state.columns.forEach(c=>filter.append(new Option(c.name,c.code)));body.append(filter);
    const items=element('div','mg-history-items'),back=element('button','nut','Mới hơn'),more=element('button','nut','Cũ hơn');body.append(items,back,more);let cursor=null,pageCursor=null,serial=0,trail=[];
    const load=async(reset=false,target=null)=>{
      const generation=++serial;if(reset){cursor=null;trail=[];target=null;}items.replaceChildren(element('p','','Đang tải lịch sử…'));more.disabled=back.disabled=true;
      try{
        const p=new URLSearchParams({record:row.id,column:filter.value});if(target)p.set('before',target);
        const data=await fetch(config.historyUrl+'?'+p).then(json);if(generation!==serial||state.historyId!==row.id)return;
        items.replaceChildren();if(!data.items.length)items.append(element('p','','Chưa có lịch sử khớp lựa chọn.'));
        for(const h of data.items){const item=element('section','mg-history-item');item.append(element('strong','',`${h.actor} — ${h.name} · ${new Date(h.time).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})}`),element('p','',`${state.columns.find(c=>c.code===h.column)?.name||h.column} · ${propertyName(h.property)} · ${({edit:"Sửa",paste:"Dán",clear:"Xóa nội dung",format:"Định dạng",undo:"Hoàn tác",redo:"Làm lại"})[h.kind]||"Thay đổi"} · ${h.operation.slice(0,8)}`),element('pre','',`Trước: ${h.before??'Trống'}\nSau: ${h.after??'Trống'}`));items.append(item);}
        cursor=data.next;pageCursor=target;more.hidden=!cursor;back.hidden=!trail.length;
      }catch(e){if(e.status===403||e.status===404){body.replaceChildren(element('p','',e.message));}else items.append(element('p','',e.message));}
      finally{more.disabled=back.disabled=false;}
    };
    more.onclick=()=>{trail.push(pageCursor);load(false,cursor);};back.onclick=()=>load(false,trail.pop());filter.onchange=()=>load(true);openDialog('mg-history');await load(true);
  });
  function propertyName(property){return ({value:'Nội dung',fs:'Cỡ chữ',c:'Màu chữ',bg:'Màu nền'})[property||'value']||property;}
  function showConflicts(){
    const body=$('mg-conflict-body');body.replaceChildren();
    if(!state.conflicts.length){body.append(element('p','','Không có xung đột trong phiên này.'));openDialog('mg-conflict');return;}
    const choices=new Map();body.append(element('p','','Chọn cách xử lý từng ô. Toàn lượt sẽ được kiểm lại trước khi lưu.'));
    for(const c of state.conflicts){const item=element('section','mg-history-item'),select=element('select','o-nhap');select.setAttribute('aria-label',`Giải quyết ${c.column} dòng ${c.id}`);select.append(new Option('— Chọn cách xử lý —',''),new Option('Dùng giá trị hiện tại','server'),new Option('Gửi lại giá trị của tôi','mine'));
      item.append(element('strong','',`Dòng #${c.id} · ${c.name||c.column} · ${propertyName(c.property)}`),element('pre','',`Lúc bắt đầu: ${c.old??'Trống'}\nCủa tôi: ${working.value(c.id,c.column,c.value,c.property||'value')??'Trống'}\nHiện tại: ${c.current??'Trống'}`),select);body.append(item);
      select.onchange=()=>choices.set(window.KNJSCWorkingCopy.key(c),select.value);
    }
    const apply=element('button','nut','Áp dụng lựa chọn và lưu');body.append(apply);
    apply.onclick=()=>{
      if(state.conflicts.some(c=>!choices.get(window.KNJSCWorkingCopy.key(c)))){message('Chọn cách xử lý tất cả ô xung đột.',true);return;}
      // Nếu toàn lượt dùng giá trị hiện tại thì không có request ghi tiếp theo.
      // Cập nhật đúng ô trong cache để không hiện lại dữ liệu trước xung đột.
      const refreshed=new Map(),conflictIds=new Set(state.conflicts.map(c=>c.id));
      for(const block of state.cache.values())for(const row of block.rows)if(conflictIds.has(row.id))refreshed.set(row.id,{...row,cells:{...row.cells}});
      for(const c of state.conflicts){const row=refreshed.get(c.id),cell=row?.cells[c.column];if(!cell)continue;const prop=c.property||'value';row.cells[c.column]=prop==='value'?{...cell,value:c.current,display:String(c.current??'')}:{...cell,style:{...cell.style,[prop]:c.current}};}
      updateRows([...refreshed.values()]);
      working.resolve(state.conflicts,choices);state.conflicts=[];state.saveError=false;state.retry=null;message();$('mg-conflict').close();saveAll(false);
    };openDialog('mg-conflict');
  }
  $('mg-conflict-button').onclick=showConflicts;
  window.addEventListener('beforeunload',e=>{
    if(working.count||state.retry||state.busy||(state.draft&&!same(editor.elements.value?.value,state.draft.old))){e.preventDefault();e.returnValue='';}
  });
  window.addEventListener('online',()=>{if(state.retry&&!state.busy&&!state.conflicts.length){state.retryCount=0;saveAll(false);}});
  document.addEventListener('pointerdown',e=>{
    if(!editor.contains(e.target))finishEditor();
    if(!e.target.closest('.mg-more-wrap'))closeMore();
  },true);
  document.addEventListener('click',e=>{
    const button=e.target.closest('[data-master-close]');
    if(button){const id=button.dataset.masterClose;
      if(id==='editor'){if(finishEditor())viewport.focus({preventScroll:true});}
      else if($(id).tagName==='DIALOG')$(id).close();
      else{$(id).hidden=true;if(id==='mg-filters')$('mg-filters-button').setAttribute('aria-expanded','false');}
    }
    if(e.target.closest('#mg-more a,#mg-assign'))closeMore();
  });
  document.addEventListener('keydown',e=>{
    if(e.isComposing||e.keyCode===229)return;
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();safe(saveAll)();return;}
    if(e.key==='Escape'){closeMore();$('mg-filters').hidden=true;$('mg-filters-button').setAttribute('aria-expanded','false');$('hop-loc').hidden=true;}
  },true);
  async function refresh(){state.lastError='';invalidate();}
  window.addEventListener('master-refresh',refresh);
  window.KNJSC_MASTER={refresh,selectedRows:async()=>[...new Set((await rangeCells()).map(c=>c.id))],diagnostics:()=>({cache:state.cache.size,cells:canvas.querySelectorAll('.mg-cell').length,total:state.total,generation:state.generation})};
  function clearAccess(text){
    const hadDraft=!!state.draft||!!state.retry;
    state.draft=state.retry=state.historyId=null;editor.hidden=reader.hidden=true;
    $('mg-input').replaceChildren();reader.querySelector('div').textContent='';
    working=new window.KNJSCWorkingCopy();state.conflicts=[];state.saveError=true;clearTimeout(saveTimer);
    state.accessEpoch++;
    for(const id of ['mg-history','mg-conflict','mg-format']){$(id).close();$(id+'-body').replaceChildren();}
    $('vd-detail')?.close();$('vd-detail-body')?.replaceChildren();$('vd-assignment')?.close();$('vd-assignment-fields')?.replaceChildren();
    invalidate();state.total=0;state.ready=true;state.lastError=text;
    canvas.replaceChildren();message(text,true);if(hadDraft)status('Chưa lưu');repaint();
  }
  async function poll(){
    if(document.hidden||state.busy)return;
    try{
      const data=await fetch(config.filterUrl+'moi-nhat/').then(json),stamp=JSON.stringify(data);
      const ids=new Set(working.pending().map(c=>c.id));
      if(state.draft)ids.add(state.draft.id);if(state.historyId)ids.add(state.historyId);
      for(const block of state.cache.values())block.rows.forEach(r=>ids.add(r.id));
      if(ids.size){const check=await fetch(config.scopeUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify({ids:[...ids]})}).then(json),visible=new Set(check.visible),lost=new Set([...ids].filter(id=>!visible.has(id)));
        if(lost.size){
          const interrupted=working.pending().some(c=>lost.has(c.id))||state.retry?.payload.cells.some(c=>lost.has(c.id));
          if(interrupted){clearTimeout(saveTimer);firstQueued=0;state.saveError=true;state.errorStatus=403;working.release(state.retry?.payload.cells||[]);state.retry=null;}
          working.forget(lost);if(state.draft&&lost.has(state.draft.id)){cancelEdit();$('mg-input').replaceChildren();}state.conflicts=state.conflicts.filter(c=>!lost.has(c.id));
          for(const id of ['mg-history','mg-conflict','mg-format']){$(id).close();$(id+'-body').replaceChildren();}state.historyId=null;reader.hidden=true;invalidate();message('Có dòng đã ra ngoài quyền xem; phần sửa trên dòng đó không được lưu. Nháp còn quyền được giữ.',true);
          if(interrupted&&working.count){const retry=element('button','nut','Thử lại');retry.onclick=()=>{state.retryCount=0;saveAll();};$('mg-message').append(retry);}refreshStatus();}
        if(lost.size){reader.querySelector('div').textContent='';$('vd-detail')?.close();$('vd-detail-body')?.replaceChildren();$('vd-assignment')?.close();$('vd-assignment-fields')?.replaceChildren();}
      }
      if(state.poll&&state.poll!==stamp)invalidate(false);state.poll=stamp;
    }catch(e){if(e.status===403||e.status===404){clearAccess('Quyền xem đã thay đổi.');}}
  }
  setInterval(poll,8000);
  window.addEventListener('blur',()=>{finishRowResize(false);drag=null;resizing=null;cancelAnimationFrame(frame);frame=0;});
  document.addEventListener('pointercancel',()=>{finishRowResize(false);drag=null;resizing=null;cancelAnimationFrame(frame);frame=0;});
  viewport.addEventListener('lostpointercapture',e=>{if(rowResize&&e.pointerId===rowResize.pointer)finishRowResize(false);});
  repaint();poll();
})();
