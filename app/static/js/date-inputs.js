/* Ngày hiển thị D/M/Y; hợp đồng JS, FormData và HTMX vẫn nhận ISO.
   Không thay múi giờ lưu trữ và không phụ thuộc locale của trình duyệt. */
(() => {
  'use strict';
  const nativeValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  const enhanced = new WeakSet();
  const pad = n => String(n).padStart(2, '0');
  function canonical(raw, time = false) {
    raw = String(raw || '').trim();
    if (!raw) return '';
    const match = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2})(\.\d{1,3})?)?)?$/);
    if (!match || (time && match[4] === undefined) || (!time && match[4] !== undefined)) return null;
    const [, d, m, y, h = '00', min = '00', sec = '00', fraction = ''] = match;
    const day = new Date(0); day.setUTCFullYear(+y, +m - 1, +d);
    if (+y < 1 || day.getUTCFullYear() !== +y || day.getUTCMonth() !== +m - 1 || day.getUTCDate() !== +d || +h > 23 || +min > 59 || +sec > 59) return null;
    return `${y}-${pad(m)}-${pad(d)}` + (time ? `T${pad(h)}:${min}` + (match[6] ? `:${sec}${fraction}` : '') : '');
  }
  function display(value, time) {
    let text = String(value ?? '');
    if (time && /(?:Z|[+-]\d{2}:\d{2})$/.test(text)) {
      const parsed = new Date(text);
      if (!Number.isNaN(parsed.getTime())) {
        const shifted = new Date(parsed.getTime() + 7 * 3600000);
        text = shifted.toISOString().replace(/Z$/, '');
      }
    }
    return text.replace(/^(\d{4})-(\d{2})-(\d{2})(?:T| )?/, (_, y, m, d) => `${d}/${m}/${y}${time ? ' ' : ''}`);
  }
  function enhance(input) {
    if (!(input instanceof HTMLInputElement) || enhanced.has(input) || input.hasAttribute('data-date-native')) return;
    if (!['date', 'datetime-local'].includes(input.type) && !input.hasAttribute('data-date-time')) return;
    enhanced.add(input);
    const time = input.type === 'datetime-local' || input.hasAttribute('data-date-time');
    const zoned = input.hasAttribute('data-date-time');
    const initial = nativeValue.get.call(input) || input.getAttribute('value') || '';
    let original = initial, originalDisplay = display(initial, time);
    input.type = 'text'; input.dataset.dateFormat = time ? 'datetime' : 'date';
    input.placeholder = time ? 'DD/MM/YYYY HH:mm' : 'DD/MM/YYYY';
    input.inputMode = 'text';
    function validate() {
      const raw = nativeValue.get.call(input), value = canonical(raw, time);
      let error = value === null ? `Nhập ngày hợp lệ theo ${input.placeholder}.` : '';
      if (!error && value && input.min && value < input.min) error = `Ngày không được trước ${display(input.min, time)}.`;
      if (!error && value && input.max && value > input.max) error = `Ngày không được sau ${display(input.max, time)}.`;
      input.setCustomValidity(error);
    }
    Object.defineProperty(input, 'value', {
      configurable: true,
      get() {
        const raw = nativeValue.get.call(this);
        if (zoned && raw === originalDisplay) return original;
        const iso = canonical(raw, time);
        return iso === null ? raw : (zoned && iso ? new Date(iso + '+07:00').toISOString() : iso);
      },
      set(value) {
        original = String(value ?? ''); originalDisplay = display(original, time);
        nativeValue.set.call(this, originalDisplay); validate();
      }
    });
    input.value = initial;
    input.addEventListener('input', validate);
    input.addEventListener('change', validate);
    // Giữ lịch chọn ngày; ô hiển thị không bị hệ điều hành đổi sang M/D/Y.
    if (input.parentNode && !input.readOnly && !input.disabled) {
      const wrap = document.createElement('span'); wrap.className = 'kn-date-control';
      input.before(wrap); wrap.append(input);
      const picker = document.createElement('input'); picker.type = time ? 'datetime-local' : 'date';
      picker.setAttribute('data-date-native', ''); picker.className = 'kn-date-native';
      picker.tabIndex = -1; picker.setAttribute('aria-hidden', 'true');
      picker.min = input.min; picker.max = input.max; picker.step = input.step || (time ? 'any' : '1');
      const button = document.createElement('button'); button.type = 'button';
      button.className = 'kn-date-picker'; button.textContent = '▦';
      button.setAttribute('aria-label', 'Chọn ngày trên lịch'); button.title = 'Chọn ngày trên lịch';
      button.addEventListener('click', () => {
        picker.value = canonical(nativeValue.get.call(input), time) || '';
        if (picker.showPicker) { try { picker.showPicker(); } catch (_) { input.focus(); } }
        else { picker.focus(); picker.click(); }
      });
      picker.addEventListener('change', () => {
        input.value = zoned && picker.value ? new Date(picker.value + '+07:00').toISOString() : picker.value;
        input.dispatchEvent(new Event('input', {bubbles:true}));
        input.dispatchEvent(new Event('change', {bubbles:true})); input.focus();
      });
      wrap.append(button, picker);
    }
  }
  function scan(root) {
    if (root.matches?.('input')) enhance(root);
    root.querySelectorAll?.('input[type="date"],input[type="datetime-local"],input[data-date-time]').forEach(enhance);
  }
  function fields(form) { return Array.from(form?.elements || []).filter(e => enhanced.has(e) && e.name && !e.disabled); }
  document.addEventListener('formdata', event => {
    const names = new Map();
    for (const input of fields(event.target)) {
      if (!names.has(input.name)) names.set(input.name, []);
      names.get(input.name).push(input.value);
    }
    for (const [name, values] of names) { event.formData.delete(name); for (const value of values) event.formData.append(name, value); }
  }, true);
  document.addEventListener('htmx:configRequest', event => {
    for (const input of fields(event.detail.elt?.closest('form'))) event.detail.parameters[input.name] = input.value;
  });
  document.addEventListener('reset', event => queueMicrotask(() => {
    for (const input of fields(event.target)) input.value = input.defaultValue;
  }), true);
  window.KNDate = {enhance, canonical, display};
  scan(document);
  new MutationObserver(changes => {
    for (const change of changes) for (const node of change.addedNodes) if (node.nodeType === 1) scan(node);
  }).observe(document.body, {subtree:true, childList:true});
})();
