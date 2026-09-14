/* Chỉ đổi khung hiển thị. Không dựng lại lưới hoặc nhân bản sự kiện lưu/lọc. */
(() => {
  const root = document.documentElement;
  const trigger = document.getElementById('bt-toan-man-nut');
  const bar = document.querySelector('.sp-focus-bar');
  const status = document.getElementById('bt-trang-thai');
  if (!trigger || !bar || !status) return;
  if (!document.querySelector('#mg-viewport, #luoi-vd')) { trigger.hidden = true; return; }
  const anchor = document.createComment('Vị trí trạng thái lưu trong header');
  status.before(anchor);
  const tools = document.getElementById('sp-focus-tools');
  const exit = document.getElementById('sp-focus-exit');
  const native = document.getElementById('sp-native-fullscreen');
  const nativeAnchor = document.createComment('Vị trí toàn màn hình trình duyệt');
  native?.before(nativeAnchor);
  let previousFocus;
  function toolMode(open) {
    root.classList.toggle('sp-tools-open', open);
    tools.setAttribute('aria-expanded', String(open));
    window.dispatchEvent(new Event('resize'));
  }
  function setFocus(on) {
    if (on) previousFocus = document.activeElement;
    root.classList.toggle('sp-grid-focus', on);
    bar.hidden = !on;
    trigger.setAttribute('aria-pressed', String(on));
    if (on) {
      document.getElementById('sp-focus-status-slot').append(status);
      if (native) tools.after(native);
      tools.focus({preventScroll:true});
    } else {
      anchor.after(status);
      if (native) nativeAnchor.after(native);
      toolMode(false);
      (previousFocus?.isConnected ? previousFocus : trigger).focus({preventScroll:true});
    }
    window.dispatchEvent(new Event('resize'));
  }
  trigger.addEventListener('click', () => setFocus(true));
  exit.addEventListener('click', () => setFocus(false));
  tools.addEventListener('click', () => toolMode(!root.classList.contains('sp-tools-open')));
  document.getElementById('sp-native-fullscreen')?.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (root.requestFullscreen) await root.requestFullscreen();
      else throw new Error('unsupported');
    } catch (_) {
      // Focus vẫn dùng được nếu trình duyệt từ chối Fullscreen API.
      setFocus(true);
    }
  });
  const visible = el => el && !el.hidden && el.getClientRects().length > 0;
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || !root.classList.contains('sp-grid-focus')) return;
    // Kiểm tra trước handler của lưới: một Esc chỉ xử lý lớp đang mở.
    const editing = document.querySelector('td.dang-sua, td.o-cat, .mg-resizing-row');
    const layers = [...document.querySelectorAll('dialog[open], #mg-editor, #mg-reader, #hop-loc, #mg-more, #mg-filters, #bt-khac-hop, #bt-an-cot-hop, .bt-bang-mau, #bt-ctx')];
    if (editing || layers.some(visible)) return;
    if (root.classList.contains('sp-tools-open')) {
      toolMode(false); tools.focus({preventScroll:true});
    } else setFocus(false);
    event.preventDefault();
  }, true);
})();
