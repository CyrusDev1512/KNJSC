/* Tìm trong danh sách được server cấp quyền; chỉ gửi bộ lọc khi Áp dụng. */
(() => {
  const root = document.documentElement;
  const view = document.getElementById('report-view');
  const workspace = document.getElementById('report-workspace');
  const panel = document.getElementById('report-filter-panel');
  const filterToggle = document.getElementById('report-toggle-filters');
  const focusToggle = document.getElementById('report-toggle-focus');
  if (view && workspace && panel && filterToggle && focusToggle) {
    const storageKey = 'knjsc-report-layout';
    let normalHidden = false;
    let focused = false;
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || '{}');
      normalHidden = saved.hidden === true;
      focused = saved.focus === true;
    } catch (_) {}
    const persist = () => {
      try { sessionStorage.setItem(storageKey, JSON.stringify({hidden:normalHidden, focus:focused})); } catch (_) {}
    };
    const setPanel = open => {
      if (!open && panel.contains(document.activeElement)) filterToggle.focus({preventScroll:true});
      panel.hidden = !open;
      workspace.classList.toggle('report-filters-hidden', !open);
      filterToggle.setAttribute('aria-expanded', String(open));
      filterToggle.textContent = open ? 'Ẩn bộ lọc' : 'Hiện bộ lọc';
    };
    const setFocus = active => {
      const grid = view.querySelector('.report-table-scroll');
      const position = grid ? [grid.scrollLeft, grid.scrollTop] : null;
      focused = active;
      root.classList.toggle('sp-report-focus', active);
      // Tái sử dụng khung tập trung ERP; không đổi lựa chọn mở rộng ERP của người dùng.
      root.classList.toggle('sp-erp-table-focus', active);
      focusToggle.setAttribute('aria-pressed', String(active));
      focusToggle.textContent = active ? 'Thoát toàn màn hình' : 'Toàn màn hình';
      setPanel(active ? false : !normalHidden);
      if (grid && position) { grid.scrollLeft = position[0]; grid.scrollTop = position[1]; }
      persist();
    };
    filterToggle.hidden = focusToggle.hidden = false;
    setFocus(focused);
    filterToggle.addEventListener('click', () => {
      const open = panel.hidden;
      setPanel(open);
      if (!focused) normalHidden = !open;
      persist();
    });
    focusToggle.addEventListener('click', () => setFocus(!focused));
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || event.defaultPrevented || event.isComposing || !focused) return;
      if (document.querySelector('dialog[open], details[open]')) return;
      if (!panel.hidden) {
        setPanel(false);
        filterToggle.focus({preventScroll:true});
      } else {
        setFocus(false);
        focusToggle.focus({preventScroll:true});
      }
      event.preventDefault();
      event.stopPropagation();
    }, true);
  }
  const search = document.getElementById('report-person-search');
  const select = document.getElementById('report-person');
  if (!search || !select) return;
  const source = document.getElementById('nguon');
  const team = document.getElementById('report-team');
  const initialSource = source.value;
  source.addEventListener('change', () => {
    // Danh mục phụ thuộc nguồn: không gửi ID của nguồn cũ sang nguồn mới.
    const changed = source.value !== initialSource;
    select.value = '';
    team.value = '';
    search.value = '';
    select.disabled = team.disabled = search.disabled = changed;
    for (const option of select.options) option.hidden = false;
    document.getElementById('report-person-count').textContent = changed
      ? 'Bấm Áp dụng để tải danh sách team và nhân sự của nguồn mới.'
      : 'Chỉ hiển thị nhân sự có dữ liệu trong phạm vi của bạn.';
  });
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().trim();
  search.addEventListener('input', () => {
    const term = normalize(search.value);
    let count = 0;
    for (const option of select.options) {
      const matches = !option.value || normalize(option.textContent).includes(term);
      // Không âm thầm bỏ lựa chọn đang áp dụng khi tìm người khác.
      option.hidden = !matches && !option.selected;
      if (option.value && matches) count++;
    }
    document.getElementById('report-person-count').textContent = `${count} nhân sự khớp tìm kiếm. Chọn nhân sự rồi bấm Áp dụng.`;
  });
})();
