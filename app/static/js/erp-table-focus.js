/* Chế độ tập trung chỉ thay đổi bố cục; bảng KN ERP vẫn hoàn toàn chỉ đọc. */
(() => {
  const root = document.documentElement;
  const area = document.getElementById('erp-table-focus');
  const enter = document.getElementById('erp-focus-enter');
  const exit = document.getElementById('erp-focus-exit');
  const tools = document.getElementById('erp-focus-tools');
  const native = document.getElementById('erp-native-fullscreen');
  const bar = document.getElementById('erp-focus-bar');
  if (!area || !enter || !exit || !tools || !native || !bar) return;

  let returnFocus = enter;
  function setTools(open) {
    root.classList.toggle('sp-erp-table-tools', open);
    tools.setAttribute('aria-expanded', String(open));
  }
  function setFocus(active) {
    root.classList.toggle('sp-erp-table-focus', active);
    bar.hidden = !active;
    enter.setAttribute('aria-pressed', String(active));
    if (!active) setTools(false);
  }
  enter.addEventListener('click', () => {
    returnFocus = document.activeElement || enter;
    setFocus(true);
    exit.focus({preventScroll: true});
  });
  exit.addEventListener('click', async () => {
    if (document.fullscreenElement && document.exitFullscreen) {
      try { await document.exitFullscreen(); } catch (_) {}
    }
    setFocus(false);
    returnFocus?.focus?.({preventScroll: true});
  });
  tools.addEventListener('click', () => setTools(tools.getAttribute('aria-expanded') !== 'true'));

  if (!area.requestFullscreen) {
    native.disabled = true;
    native.title = 'Trình duyệt này không hỗ trợ toàn màn hình';
  } else {
    native.addEventListener('click', async () => {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else await area.requestFullscreen();
      } catch (_) {
        native.disabled = true;
        native.title = 'Không thể ẩn thanh trình duyệt; chế độ Tập trung vẫn hoạt động';
      }
    });
    document.addEventListener('fullscreenchange', () => {
      native.textContent = document.fullscreenElement ? 'Thoát toàn màn hình' : 'Toàn màn hình trình duyệt';
    });
  }

  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || !root.classList.contains('sp-erp-table-focus')) return;
    const dialog = document.querySelector('dialog[open]');
    if (dialog) { dialog.close(); event.preventDefault(); return; }
    const openLayer = document.querySelector('.sp-dock-group[open], details[open]');
    if (openLayer) { openLayer.open = false; event.preventDefault(); return; }
    if (root.classList.contains('sp-erp-table-tools')) { setTools(false); event.preventDefault(); return; }
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen(); event.preventDefault(); return;
    }
    setFocus(false);returnFocus?.focus?.({preventScroll: true});event.preventDefault();
  });
})();
