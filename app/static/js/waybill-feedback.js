/* Phân công chỉ qua endpoint riêng. Không sửa JSON của ô hay snapshot cả dòng. */
(() => {
  'use strict';
  document.getElementById('vd-open-filters')?.addEventListener('click', () => {
    document.getElementById('bt-bo-cuc')?.classList.remove('thu-gon');
    document.getElementById('tim')?.focus();
  });
  const dialog = document.getElementById('vd-assignment');
  if (!dialog) return;
  const form = document.getElementById('vd-assignment-form');
  const fields = document.getElementById('vd-assignment-fields');
  const status = document.getElementById('vd-assignment-status');
  const save = document.getElementById('vd-assignment-save');
  const reload = document.getElementById('vd-assignment-reload');
  let ids = [], versions = {}, loading = false;
  async function responseJSON(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Không thực hiện được. Kiểm tra quyền và thử tải lại.');
    return data;
  }
  async function load() {
    if (loading) return;
    loading = true; save.disabled = true; reload.disabled = true;
    status.textContent = 'Đang tải phân công…'; fields.replaceChildren(); versions = {};
    try {
      const params = new URLSearchParams();
      ids.forEach(id => params.append('row', id));
      const data = await responseJSON(await fetch(dialog.dataset.url + '?' + params, {credentials: 'same-origin'}));
      data.rows.forEach(row => { versions[row.id] = row.version; });
      document.getElementById('vd-assignment-info').textContent = `Đang phân công ${data.rows.length} dòng.`;
      data.fields.forEach(field => {
        const label = document.createElement('label');
        label.textContent = field.label;
        const select = document.createElement('select');
        select.className = 'o-nhap'; select.name = field.key;
        select.append(new Option('Giữ nguyên', '__keep__'), new Option('Bỏ phân công', '__clear__'));
        field.choices.forEach(choice => select.append(new Option(choice.label, String(choice.id))));
        label.append(select);
        const current = document.createElement('small');
        const values = new Set(data.rows.map(row => row.current[field.key] || 'Chưa gán'));
        current.textContent = values.size === 1 ? `Hiện tại: ${[...values][0]}` : 'Hiện tại: nhiều người khác nhau';
        label.append(current); fields.append(label);
      });
      status.textContent = ''; save.disabled = false;
      fields.querySelector('select')?.focus();
    } catch (error) { status.textContent = error.message; }
    finally { loading = false; reload.disabled = false; }
  }
  function open(rowIds) {
    ids = [...new Set(rowIds.filter(Boolean))];
    if (!dialog.open) dialog.showModal();
    if (!ids.length) {
      status.textContent = 'Chọn ít nhất một dòng có dữ liệu trên lưới rồi mở Phân công.';
      fields.replaceChildren(); save.disabled = true; reload.disabled = true;
      document.getElementById('vd-assignment-info').textContent = '';
      return;
    }
    load();
  }
  document.getElementById('vd-assign-selected')?.addEventListener('click', () => {
    open([...document.querySelectorAll('#luoi-vd td.o-chon[data-dong], #luoi-vd td.o-hien[data-dong]')].map(cell => cell.dataset.dong));
  });
  document.addEventListener('dblclick', event => {
    const cell = event.target.closest('[data-assignment-row]');
    if (cell) { event.preventDefault(); event.stopImmediatePropagation(); open([cell.dataset.assignmentRow]); }
  }, true);
  document.addEventListener('keydown', event => {
    const cell = event.target.closest('[data-assignment-row]');
    if (cell && event.key === 'Enter') { event.preventDefault(); event.stopImmediatePropagation(); open([cell.dataset.assignmentRow]); }
  }, true);
  dialog.querySelector('[data-assignment-close]').addEventListener('click', () => dialog.close());
  reload.addEventListener('click', load);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (save.disabled || loading) return;
    const changes = {};
    fields.querySelectorAll('select').forEach(select => {
      if (select.value !== '__keep__') changes[select.name] = select.value === '__clear__' ? null : Number(select.value);
    });
    if (!Object.keys(changes).length) { status.textContent = 'Chọn ít nhất một trường cần thay đổi.'; return; }
    save.disabled = true; reload.disabled = true; status.textContent = 'Đang lưu…';
    try {
      await responseJSON(await fetch(dialog.dataset.url, {method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({versions, changes})}));
      status.textContent = 'Đã lưu phân công. Đang cập nhật bảng…';
      window.location.reload();
    } catch (error) {
      status.textContent = `Chưa lưu: ${error.message} Bấm “Tải lại phân công” để kiểm tra trước khi thử lại.`;
      reload.disabled = false;
    }
  });
})();
