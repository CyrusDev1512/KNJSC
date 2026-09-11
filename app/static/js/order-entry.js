/* Chỉ dùng trên trang lên đơn. Tóm tắt do server tính, không lưu dữ liệu. */
(function () {
  'use strict';
  // Đồng hồ tham khảo từ thời gian server; không gửi giá trị này để lưu đơn.
  let clockElement, clockEpoch, clockStarted;
  const clockFormat = new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
  });
  function updateClock() {
    const input = document.querySelector('[data-order-clock]');
    if (!input) return;
    if (input !== clockElement) {
      clockElement = input;
      clockEpoch = Date.parse(input.dataset.orderClock);
      clockStarted = performance.now();
    }
    if (!Number.isFinite(clockEpoch)) return;
    const parts = Object.fromEntries(clockFormat.formatToParts(
      new Date(clockEpoch + performance.now() - clockStarted)
    ).map(part => [part.type, part.value]));
    const value = `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`;
    if (input.value !== value) input.value = value;
  }
  updateClock();
  setInterval(updateClock, 1000);
  document.addEventListener('htmx:afterSwap', updateClock);
  let timer, pending, generation = 0;
  function preview(form) {
    const version = ++generation;
    clearTimeout(timer);
    if (pending) pending.abort();
    const output = form.querySelector('[data-order-summary]');
    output.textContent = 'Đang cập nhật tóm tắt…';
    timer = setTimeout(async function () {
      pending = new AbortController();
      try {
        const response = await fetch(form.dataset.orderPreview, {
          method: 'POST', body: new FormData(form), signal: pending.signal,
          headers: {'X-CSRFToken': form.elements.csrfmiddlewaretoken.value}
        });
        if (response.redirected) throw new Error('Phiên đăng nhập đã hết.');
        const data = await response.json();
        if (version !== generation || !form.isConnected) return;
        output.textContent = response.ok
          ? `${data.lines} dòng · ${data.quantity} sản phẩm · Tổng ${data.total} ${data.currency}`
          : data.error || 'Không tính được tóm tắt.';
      } catch (error) {
        if (error.name !== 'AbortError' && version === generation)
          output.textContent = 'Không tải được tóm tắt. Kiểm tra kết nối hoặc đăng nhập lại.';
      }
    }, 350);
  }
  document.addEventListener('input', function (event) {
    const form = event.target.closest('[data-order-preview]');
    if (form && ['product', 'quantity', 'unit_price', 'currency'].includes(event.target.name)) preview(form);
  });
  document.addEventListener('click', async function (event) {
    const form = event.target.closest('[data-order-preview]');
    if (!form) return;
    if (event.target.closest('[data-add-item],[data-remove-item]')) preview(form);
    const button = event.target.closest('[data-create-product]');
    if (!button) return;
    const output = form.querySelector('[data-product-result]');
    const name = form.querySelector('[data-product-name]');
    button.disabled = true;
    output.textContent = 'Đang tạo…';
    try {
      const response = await fetch(button.dataset.createProduct, {
        method: 'POST', body: new URLSearchParams({nhan_moi: name.value}),
        headers: {'X-CSRFToken': form.elements.csrfmiddlewaretoken.value, 'Accept': 'application/json'}
      });
      if (response.redirected) throw new Error('Phiên đăng nhập đã hết.');
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      form.querySelectorAll('select[name=product]').forEach(select => select.add(new Option(data.name, data.code)));
      output.textContent = 'Đã tạo sản phẩm. Có thể chọn trong danh sách.';
      name.value = '';
    } catch (error) {
      output.textContent = error.message || 'Chưa tạo được sản phẩm.';
    } finally { button.disabled = false; }
  });
})();
