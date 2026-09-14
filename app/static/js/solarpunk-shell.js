/* Menu nhóm dùng details nguyên bản: Tab, Enter và Space hoạt động không cần JS. */
(() => {
  const groups = [...document.querySelectorAll('.sp-dock-group')];
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
