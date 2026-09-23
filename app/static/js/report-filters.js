/* Bố cục Báo cáo tổng hợp (bản vẽ 18.09): bộ lọc ba trạng thái, toàn màn hình, chọn nhanh kỳ, tìm nhân sự.
   Tìm trong danh sách được server cấp quyền; chỉ gửi bộ lọc khi Áp dụng (Chọn nhanh kỳ gửi ngay). */
(() => {
  const root = document.documentElement;
  const normalize = text => text.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().trim();
  const view = document.getElementById('report-view');
  const workspace = document.getElementById('report-workspace');
  const panel = document.getElementById('report-filter-panel');
  const filterToggle = document.getElementById('report-toggle-filters');
  const focusToggle = document.getElementById('report-toggle-focus');
  if (view && workspace && panel && filterToggle && focusToggle) {
    const storageKey = 'knjsc-report-layout';
    const narrowQuery = window.matchMedia('(max-width:900px)');
    const narrow = () => narrowQuery.matches;
    const active = Number(workspace.dataset.active || 0);
    // Rộng: mặc định mở. Hẹp: ngăn kéo mặc định đóng, chỉ mở khi người dùng bấm.
    const state = {filters: narrow() ? 'rail' : 'open', focus: false};
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || '{}');
      if (saved.filters === 'open' || saved.filters === 'rail') state.filters = saved.filters;
      else if (saved.hidden === true) state.filters = 'rail';   // khoá cũ {hidden, focus}
      state.focus = saved.focus === true;
    } catch (_) {}
    if (narrow() && state.filters === 'open') state.filters = 'rail';
    const persist = () => {
      try { sessionStorage.setItem(storageKey, JSON.stringify({filters: state.filters, focus: state.focus})); } catch (_) {}
    };
    const label = filterToggle.querySelector('span');
    const headHeight = () => {
      const head = view.querySelector('.report-table thead');
      if (head) view.style.setProperty('--head-h', Math.round(head.getBoundingClientRect().height) + 'px');
    };
    const render = () => {
      // Hẹp: chỉ có mở (ngăn kéo) hoặc đóng. Rộng: mở hoặc thanh dọc.
      const shown = narrow() ? (state.filters === 'open' ? 'open' : 'closed') : state.filters;
      const open = shown === 'open';
      if (!open && panel.contains(document.activeElement)) filterToggle.focus({preventScroll: true});
      workspace.dataset.filters = shown;
      filterToggle.setAttribute('aria-expanded', String(open));
      if (label) label.textContent = open ? 'Thu gọn bộ lọc' : (narrow() && active ? `Bộ lọc (${active})` : 'Mở bộ lọc');
      root.classList.toggle('sp-report-focus', state.focus);
      // Tái sử dụng khung tập trung ERP; không đổi lựa chọn mở rộng ERP của người dùng.
      root.classList.toggle('sp-erp-table-focus', state.focus);
      focusToggle.setAttribute('aria-pressed', String(state.focus));
      focusToggle.textContent = state.focus ? 'Thoát toàn màn hình' : 'Toàn màn hình';
      headHeight();
    };
    const setFilters = value => { state.filters = value; persist(); render(); };
    const setFocus = value => {
      const grid = view.querySelector('.report-table-scroll');
      const position = grid ? [grid.scrollLeft, grid.scrollTop] : null;
      state.focus = value;
      if (value && state.filters === 'open') state.filters = 'rail';   // toàn màn hình: nhường chỗ cho bảng
      persist(); render();
      if (grid && position) { grid.scrollLeft = position[0]; grid.scrollTop = position[1]; }
    };
    filterToggle.hidden = focusToggle.hidden = false;
    render();
    filterToggle.addEventListener('click', () => setFilters(workspace.dataset.filters === 'open' ? 'rail' : 'open'));
    document.getElementById('report-panel-collapse')?.addEventListener('click', () => setFilters('rail'));
    document.getElementById('report-panel-expand')?.addEventListener('click', () => setFilters('open'));
    document.getElementById('report-backdrop')?.addEventListener('click', () => setFilters('rail'));
    focusToggle.addEventListener('click', () => setFocus(!state.focus));
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || event.defaultPrevented || event.isComposing) return;
      if (document.querySelector('dialog[open], details[open]')) return;
      // Escape: đóng ngăn kéo trước, thoát toàn màn hình sau.
      if (narrow() && workspace.dataset.filters === 'open') { setFilters('rail'); filterToggle.focus({preventScroll: true}); }
      else if (state.focus) { setFocus(false); focusToggle.focus({preventScroll: true}); }
      else return;
      event.preventDefault();
      event.stopPropagation();
    }, true);
    narrowQuery.addEventListener('change', event => { if (event.matches && state.filters === 'open') state.filters = 'rail'; render(); });
    window.addEventListener('resize', headHeight);
  }
  // Chọn nhanh kỳ (ADR-038): điền hai ô ngày rồi gửi bộ lọc ngay.
  const filters = document.querySelector('.report-filters');
  const fromInput = document.getElementById('tu');
  const toInput = document.getElementById('den');
  if (filters && fromInput && toInput) {
    const presets = filters.querySelectorAll('.report-preset');
    for (const button of presets) {
      button.addEventListener('click', () => {
        fromInput.value = button.dataset.tu;
        toInput.value = button.dataset.den;
        for (const other of presets) other.classList.toggle('is-active', other === button);
        if (typeof filters.requestSubmit === 'function') filters.requestSubmit(); else filters.submit();
      });
    }
  }
  // Chọn nhiều sản phẩm (ADR-040): ô tìm nhanh lọc danh sách, Chọn tất cả / Bỏ chọn, nhãn tóm tắt.
  const multi = document.getElementById('report-multi-sp');
  if (multi) {
    const boxes = [...multi.querySelectorAll('input[type=checkbox]')];
    const summary = multi.querySelector('.report-multi-tom-tat');
    const tomTat = () => {
      const chon = boxes.filter(b => b.checked);
      summary.textContent = chon.length === 0 ? 'Tất cả' : chon.length === 1 ? chon[0].parentElement.textContent.trim() : `${chon.length} sản phẩm`;
    };
    multi.addEventListener('change', tomTat);
    multi.querySelector('.report-multi-tim').addEventListener('input', event => {
      const term = normalize(event.target.value);
      for (const box of boxes) box.parentElement.hidden = Boolean(term) && !normalize(box.parentElement.textContent).includes(term);
    });
    for (const nut of multi.querySelectorAll('[data-chon]')) {
      nut.addEventListener('click', () => {
        for (const box of boxes) if (!box.parentElement.hidden) box.checked = nut.dataset.chon === 'all';
        tomTat();
      });
    }
  }
  const search = document.getElementById('report-person-search');
  const select = document.getElementById('report-person');
  if (!search || !select) return;
  const source = document.getElementById('nguon');
  const team = document.getElementById('report-team');
  // Bảng dữ liệu dạng báo cáo (ADR-040 đợt 4) không có ô Nguồn: chỉ còn tìm nhân sự
  const initialSource = source ? source.value : '';
  if (source) source.addEventListener('change', () => {
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
