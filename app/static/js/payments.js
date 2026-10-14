/* Ảnh chỉ tải sau khi mở Ref. Không lưu nội dung hoặc ảnh vào localStorage. */
(() => {
  'use strict';
  const base = '/chung-tu-thanh-toan/';
  const viewer = document.createElement('dialog');
  viewer.className = 'payment-dialog';
  viewer.setAttribute('aria-label', 'Ảnh chứng từ thanh toán');
  document.body.append(viewer);
  let current = null, generation = 0, opener = null;
  const element = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  // Hết phiên, đổi mật khẩu, mã bảo mật lệch, đổi người: không gọi là mất quyền, không xoá chữ đang gõ (ADR-053)
  let sessionLost = false;
  async function json(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store', ...options});
    const isJson = (response.headers.get('Content-Type') || '').includes('application/json');
    const data = isJson ? await response.json().catch(() => null) : null;
    const session = window.KNJSC_SESSION?.sessionError(response, data)
      || (response.redirected ? Object.assign(new Error('Phiên đăng nhập đã hết — thay đổi chưa được lưu.'), {session: true, code: 'het_phien'}) : null);
    if (session) { sessionLost = true; throw session; }
    if (!response.ok) throw new Error(data?.error || 'Không tải được chứng từ.');
    if (!data) throw new Error('Phản hồi của máy chủ không hợp lệ — chưa lưu. Thử lại.');
    sessionLost = false;
    return data;
  }
  function showError(box, e) {
    box.textContent = e.message;
    if (e.session && window.KNJSC_SESSION) box.append(' ', window.KNJSC_SESSION.help(e));
  }
  function close() {
    generation++;
    current = null;
    viewer.close();
    viewer.replaceChildren();
    opener?.focus({preventScroll: true});
  }
  viewer.addEventListener('cancel', event => { event.preventDefault(); close(); });
  function button(text, action) {
    const node = element('button', text, 'nut');
    node.type = 'button';
    node.addEventListener('click', action);
    return node;
  }
  async function open(id) {
    if (!viewer.open) opener = document.activeElement;
    const version = ++generation;
    current = null;
    viewer.replaceChildren(element('p', 'Đang tải chứng từ…'), button('Đóng', close));
    if (!viewer.open) viewer.showModal();
    try {
      const doc = await json(`${base}${id}/`);
      if (version !== generation) return;
      current = doc;
      const header = element('header');
      const exit = button('×', close);
      exit.setAttribute('aria-label', 'Đóng ảnh chứng từ');
      header.append(element('h2', doc.reference), exit);
      const stage = element('div', undefined, 'payment-image-stage');
      const images = element('div', undefined, 'payment-images');
      const download = element('a', 'Tải ảnh', 'nut');
      function showImage(image) {
        const img = element('img');
        img.alt = `Chứng từ ${doc.reference}`;
        img.src = image.url;
        img.addEventListener('error', () => { stage.replaceChildren(element('p', 'Không tải được ảnh hoặc quyền đã thay đổi.')); });
        stage.replaceChildren(img);
        download.href = image.url + '?download=1';
      }
      doc.images.forEach((image, index) => images.append(button(`Ảnh ${index + 1}`, () => showImage(image))));
      viewer.replaceChildren(header, element('p', doc.note || ''), images, stage);
      if (!doc.deleted && doc.images.length) {
        showImage(doc.images[0]);
        viewer.append(button('Phóng to / Thu vừa', () => stage.classList.toggle('zoom')), download);
      } else stage.append(element('p', 'Chứng từ đã xóa. Khôi phục để xem ảnh.'));
      if (doc.can_manage) renderEdit(doc);
      exit.focus();
    } catch (error) {
      if (version !== generation) return;
      const note = element('p');
      showError(note, error);
      viewer.replaceChildren(note, button('Đóng', close));
    }
  }
  function renderEdit(doc) {
    const details = element('details');
    details.append(element('summary', 'Quản lý chứng từ'));
    const form = element('form');
    const input = (name, title, value, type = 'text') => {
      const label = element('label', title);
      const field = element('input', undefined, 'o-nhap');
      field.type = type; field.name = name; field.value = value || '';
      label.append(field); form.append(label); return field;
    };
    input('reference', 'Ref', doc.reference).required = true;
    input('transfer_date', 'Ngày chuyển khoản', doc.transfer_date, 'date');
    input('note', 'Ghi chú', doc.note).maxLength = 1000;
    const upload = input('images', 'Bổ sung ảnh', '', 'file');
    upload.accept = 'image/jpeg,image/png'; upload.multiple = true;
    doc.images.forEach((image, index) => {
      const field = input('remove', `Gỡ ảnh ${index + 1}`, image.id, 'checkbox');
      field.value = image.id;
    });
    const error = element('p', '', 'payment-error'); error.setAttribute('role', 'alert');
    async function submit(action) {
      const data = new FormData(form);
      data.set('version', doc.version); data.set('action', action);
      // File input rỗng không phải một ảnh gửi lên.
      if (!upload.files.length) data.delete('images');
      try {
        await json(`${base}${doc.id}/sua/`, {method: 'POST', body: data, headers: csrf()});
        document.dispatchEvent(new CustomEvent('payment-changed', {detail: {record: doc.record}}));
        window.dispatchEvent(new CustomEvent('master-refresh'));
        await open(doc.id);
      } catch (e) { showError(error, e); }
    }
    form.addEventListener('submit', event => {event.preventDefault(); submit('edit');});
    if (!doc.deleted) form.append(button('Lưu thay đổi', () => {if (form.reportValidity()) submit('edit');}));
    form.append(button(doc.deleted ? 'Khôi phục' : 'Xóa chứng từ', () => {
      if (doc.deleted || confirm('Xóa mềm chứng từ này? Ảnh gốc vẫn được giữ.')) submit(doc.deleted ? 'restore' : 'delete');
    }), error);
    details.append(form); viewer.append(details); pasteImages(form);
  }
  function csrf() {
    return {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''};
  }
  function pasteImages(form) {
    form.addEventListener('paste', event => {
      const files = [...(event.clipboardData?.files || [])];
      if (!files.length) return;
      event.preventDefault();
      const input = form.querySelector('[name=images]'), transfer = new DataTransfer();
      [...input.files, ...files].forEach(file => transfer.items.add(file));
      input.files = transfer.files;
    });
  }
  // Giữ thao tác hyperlink tách khỏi chọn/sửa của lưới.
  document.addEventListener('pointerdown', event => {
    if (event.target.closest('[data-payment-id], .mg-cell .payment-link')) event.stopPropagation();
  }, true);
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-payment-id]');
    if (link) { event.preventDefault(); event.stopPropagation(); open(link.dataset.paymentId); }
    const exit = event.target.closest('[data-payment-close]');
    if (exit) exit.closest('dialog').close();
  }, true);
  setInterval(async () => {
    if (!current || document.hidden || sessionLost) return;
    const id = current.id, version = generation;
    try { await json(`${base}${id}/`); }
    catch (e) {
      if (generation !== version) return;
      if (e.session) {
        // Giữ nguyên hộp và form đang gõ; chỉ báo ở đầu hộp. Lượt hỏi dừng tới khi một yêu cầu khác về hợp lệ
        let box = viewer.querySelector(':scope > .payment-error');   // ô lỗi của form nằm trong <details> có thể đang gập
        if (!box) {
          box = element('p', '', 'payment-error'); box.setAttribute('role', 'alert');
          viewer.prepend(box);
        }
        showError(box, e);
        return;
      }
      current = null;
      viewer.replaceChildren(element('p', e.message), button('Đóng', close));
    }
  }, 8000);
  const createForm = document.querySelector('#payment-create-form');
  if (createForm) {
    pasteImages(createForm);
    let searchGeneration = 0;
    async function search() {
      const version = ++searchGeneration;
      const data = await json(base + 'don/?q=' + encodeURIComponent(document.querySelector('#payment-row-search').value));
      if (version !== searchGeneration) return;
      const select = document.querySelector('#payment-record');
      select.replaceChildren(...data.rows.map(row => {
        const option = element('option', row.label); option.value = row.id; return option;
      }));
    }
    document.querySelector('[data-payment-create]').addEventListener('click', () => {
      document.querySelector('#payment-create').showModal();
      search().catch(e => showError(createForm.querySelector('.payment-error'), e));
    });
    let timer;
    document.querySelector('#payment-row-search').addEventListener('input', () => {
      clearTimeout(timer); timer = setTimeout(() => search().catch(e => showError(createForm.querySelector('.payment-error'), e)), 250);
    });
    createForm.addEventListener('submit', async event => {
      event.preventDefault();
      const submit = createForm.querySelector('[type=submit]'); submit.disabled = true;
      try {
        const doc = await json(createForm.action, {method: 'POST', body: new FormData(createForm)});
        document.querySelector('#payment-create').close();
        createForm.reset(); createForm.elements.operation.value = crypto.randomUUID();
        await open(doc.id);
      } catch (e) {showError(createForm.querySelector('.payment-error'), e);}
      finally {submit.disabled = false;}
    });
  }
})();
