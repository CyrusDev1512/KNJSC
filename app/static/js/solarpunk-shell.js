/* Menu nhóm dùng details nguyên bản: Tab, Enter và Space hoạt động không cần JS. */
(() => {
  const root = document.documentElement;
  const fullscreen = document.getElementById('sp-erp-fullscreen');
  if (fullscreen) {
    const storageKey = 'knjsc-erp-immersive';
    const setImmersive = (active, persist = true) => {
      root.classList.toggle('sp-erp-immersive', active);
      fullscreen.setAttribute('aria-pressed', String(active));
      fullscreen.setAttribute('aria-label', active ? 'Thu gọn giao diện ERP' : 'Mở rộng giao diện ERP');
      fullscreen.title = active ? 'Thu gọn giao diện ERP' : 'Mở rộng giao diện ERP';
      if (persist) try { localStorage.setItem(storageKey, active ? '1' : '0'); } catch (_) {}
    };
    setImmersive(root.classList.contains('sp-erp-immersive'), false);
    fullscreen.addEventListener('click', () => {
      const active = root.classList.contains('sp-erp-immersive');
      setImmersive(!active);
    });
    window.addEventListener('storage', event => {
      if (event.key === storageKey) setImmersive(event.newValue === '1', false);
    });
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || event.defaultPrevented || !root.classList.contains('sp-erp-immersive')) return;
      if (root.classList.contains('sp-erp-table-focus')) return;
      setImmersive(false);
      fullscreen.focus({preventScroll: true});
      event.preventDefault();
    });
  }
})();

(() => {
  const groups = [...document.querySelectorAll('.sp-dock-group')];
  const collapse = document.getElementById('sp-dock-collapse');
  const expand = document.getElementById('sp-dock-expand');
  const storageKey = 'knjsc-erp-dock-collapsed';
  function setDockCollapsed(collapsed, persist = true) {
    groups.forEach(group => { group.open = false; });
    document.documentElement.classList.toggle('sp-dock-collapsed', collapsed);
    if (collapse) collapse.setAttribute('aria-expanded', String(!collapsed));
    if (expand) {
      expand.hidden = !collapsed;
      expand.setAttribute('aria-expanded', String(!collapsed));
    }
    if (persist) try { localStorage.setItem(storageKey, collapsed ? '1' : '0'); } catch (_) {}
  }
  if (collapse && expand) {
    let collapsed = false;
    try { collapsed = localStorage.getItem(storageKey) === '1'; } catch (_) {}
    setDockCollapsed(collapsed, false);
    collapse.addEventListener('click', () => { setDockCollapsed(true); expand.focus(); });
    expand.addEventListener('click', () => { setDockCollapsed(false); collapse.focus(); });
  }
  groups.forEach(group => {
    if (group.querySelector('[aria-current="page"]')) group.classList.add('sp-current');
    group.addEventListener('toggle', () => {
      if (group.open) groups.forEach(other => { if (other !== group) other.open = false; });
    });
  });
  document.addEventListener('click', event => {
    groups.forEach(group => { if (!group.contains(event.target)) group.open = false; });
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const open = groups.find(group => group.open);
    if (open) { open.open = false; open.querySelector('summary').focus(); event.preventDefault(); }
  });
  document.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target?.id !== 'sp-report-reader') return;
    const path = event.detail.pathInfo?.requestPath;
    document.querySelectorAll('.sp-history-link').forEach(link => {
      if (link.getAttribute('href') === path) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
    if (matchMedia('(max-width:800px)').matches && event.detail.requestConfig?.elt?.matches('.sp-history-link')) {
      event.detail.target.scrollIntoView({block:'start'});
    }
  });
})();
