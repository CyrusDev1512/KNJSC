/* Phân công chỉ qua endpoint riêng. Không sửa JSON của ô hay snapshot cả dòng.
   Chủ dự án 28.09.2026: bỏ nút và hộp "Phân công" nhiều dòng, chỉ còn ô chọn ngay trong ô. */
(() => {
  'use strict';
  async function responseJSON(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Không thực hiện được. Kiểm tra quyền và thử tải lại.');
    return data;
  }
  // Phân công ngay trong ô (AC-21.15): bấm đúp/Enter/F2 ô "Phụ trách …" mở ô chọn đè đúng ô, như
  // "Trạng thái vận chuyển". Chọn bằng chuột là lưu; dùng phím mũi tên thì Enter mới lưu. Vẫn qua
  // endpoint phân công (quyền + CAS theo phiên bản), không ghi vào JSON của ô.
  const cellBox = document.getElementById('vd-assign-cell');
  if (!cellBox) return;
  const picker = cellBox.querySelector('select'), note = cellBox.querySelector('p');
  let target = null, serial = 0, keyed = false, saving = false;
  const close = () => {
    cellBox.hidden = true; target = null; serial++; note.textContent = '';
    document.getElementById('mg-viewport')?.focus({preventScroll: true});
  };
  const place = () => {
    const cell = target && document.getElementById(target.cell);
    if (!cell) { close(); return; }
    const box = cell.getBoundingClientRect();
    const width = Math.max(box.width, 140), left = Math.max(4, Math.min(box.left, innerWidth - width - 4));
    Object.assign(cellBox.style, {left: left + 'px', top: box.top + 'px', width: width + 'px'});
    picker.style.height = box.height + 'px';
  };
  async function save() {
    if (!target || saving) return;
    if (picker.value === target.current) { close(); return; }
    saving = true; picker.disabled = true; note.textContent = 'Đang lưu…';
    try {
      await responseJSON(await fetch(cellBox.dataset.url, {method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': cellBox.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({versions: {[target.id]: target.version},
                              changes: {[target.field]: picker.value ? Number(picker.value) : null}})}));
      close();
      window.dispatchEvent(new CustomEvent('master-refresh'));
    } catch (error) {
      note.textContent = `Chưa lưu: ${error.message}`;
    } finally { saving = false; picker.disabled = false; }
  }
  window.addEventListener('master-assignment-cell', async event => {
    const {id, field, cell} = event.detail, mine = ++serial;
    target = {id, field, cell, version: 0, current: ''}; keyed = false;
    // Khoá ô chọn tới khi tải xong: phím bấm lúc đang tải không được chọn nhầm người.
    picker.replaceChildren(new Option('Đang tải…', '')); picker.disabled = true; note.textContent = '';
    delete cellBox.dataset.ready; cellBox.hidden = false; place();
    try {
      const data = await responseJSON(await fetch(`${cellBox.dataset.url}?row=${encodeURIComponent(id)}`, {credentials: 'same-origin'}));
      if (mine !== serial) return;
      const row = data.rows[0], choices = data.fields.find(f => f.key === field)?.choices || [];
      target.version = row.version; target.current = row.current_id[field] == null ? '' : String(row.current_id[field]);
      picker.replaceChildren(new Option('— Chưa gán —', ''), ...choices.map(c => new Option(c.label, String(c.id))));
      picker.value = target.current; picker.disabled = false; cellBox.dataset.ready = '1';
      requestAnimationFrame(() => picker.focus());
    } catch (error) { if (mine === serial) note.textContent = error.message; }
  });
  picker.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(); }
    else if (event.key === 'Enter') { event.preventDefault(); event.stopPropagation(); save(); }
    else if (/^(Arrow|Page|Home|End)/.test(event.key) || event.key.length === 1) keyed = true;
  });
  picker.addEventListener('change', () => { if (!keyed) save(); });
  // Lưới lấy lại focus ngay sau bấm đúp, nên không đóng theo focusout: bấm ra ngoài, Esc, cuộn mới đóng.
  document.addEventListener('pointerdown', event => { if (!cellBox.hidden && !saving && !cellBox.contains(event.target)) close(); }, true);
  // Lưới tự cuộn cho ô vào tầm nhìn khi mở: đi theo ô; ô ra khỏi vùng vẽ thì đóng.
  document.getElementById('mg-viewport')?.addEventListener('scroll', () => { if (!cellBox.hidden) place(); }, {passive: true});
  window.addEventListener('resize', () => { if (!cellBox.hidden) place(); });
})();
