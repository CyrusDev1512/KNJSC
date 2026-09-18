/* Gợi ý mã nhân sự theo họ tên trên màn tạo tài khoản (ADR-037).
   Chỉ điền khi ô mã còn trống và Admin chưa gõ tay; mã cuối cùng vẫn do máy chủ kiểm. */
(() => {
  'use strict';
  const form = document.getElementById('nhan-su-form');
  if (!form || !form.dataset.goiYMa) return;
  const name = form.querySelector('[name=full_name]');
  const code = form.querySelector('[name=staff_code]');
  if (!name || !code || code.disabled) return;
  let manual = code.value.trim() !== '';
  code.addEventListener('input', () => { manual = code.value.trim() !== ''; });
  name.addEventListener('change', async () => {
    if (manual || !name.value.trim()) return;
    try {
      const response = await fetch(form.dataset.goiYMa + '?ho_ten=' + encodeURIComponent(name.value.trim()),
        { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
      if (!response.ok) return;
      const data = await response.json();
      if (!manual && data.ma) code.value = data.ma;
    } catch (error) {
      /* Mạng lỗi thì Admin gõ tay; máy chủ vẫn tự gợi ý khi lưu */
    }
  });
})();
