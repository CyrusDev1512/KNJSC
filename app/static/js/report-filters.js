/* Bố cục Báo cáo tổng hợp (bản vẽ 18.09): bộ lọc ba trạng thái, toàn màn hình, chọn nhanh kỳ, tìm nhân sự.
   Tìm trong danh sách được server cấp quyền; chỉ gửi bộ lọc khi Áp dụng (Chọn nhanh kỳ gửi ngay).
   Ba chỗ sửa (chủ dự án duyệt mockup 02.10.2026): ① nút Giải thích số liệu / Ngưỡng màu mở panel ở đầu hộp bảng;
   ② kéo ngang xong thì nhích cho cột số hiện trọn sau vùng đứng yên; ③ Gộp / Không gộp chỉ đổi phần bảng, không tải
   lại trang, giữ đúng ngày đang xem. Đầu trang gọn (chủ dự án duyệt mockup 07.10.2026): ④ hàng nút, hàng chip, hàng
   tên bảng lên thanh trên cùng; Gộp / Không gộp, Ngưỡng màu, Giải thích số liệu, Toàn màn hình, Xuất Excel vào menu
   ⋯. Bảng dữ liệu dạng báo cáo cũng nạp tệp này nhưng không có `#report-view` và menu ⋯: phần của riêng Báo cáo
   tổng hợp đều xét hai thứ đó trước. */
(() => {
  const root = document.documentElement;
  const normalize = text => text.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().trim();
  const view = document.getElementById('report-view');
  const workspace = document.getElementById('report-workspace');
  const panel = document.getElementById('report-filter-panel');
  const filterToggle = document.getElementById('report-toggle-filters');
  const focusToggle = document.getElementById('report-toggle-focus');
  // Menu ⋯ trên thanh trên cùng: chỉ Báo cáo tổng hợp
  const them = document.querySelector('.report-them');
  const themNut = document.getElementById('report-them-nut');
  const themMenu = document.getElementById('report-them-menu');
  const giamChuyenDong = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Chip trên thanh trên cùng bị cắt khi chật: mờ dần ở mép để thấy còn nữa (`data-tran`, CSS). Đo lại cùng lúc với
  // khung bảng — các lần đó cũng là lúc thanh trên đổi bề rộng hay đổi chip
  const danhDauChipTran = () => {
    const chips = document.querySelector('.bc-dau .report-chips');
    if (chips) chips.toggleAttribute('data-tran', chips.scrollWidth > chips.clientWidth + 1);
  };
  // Nút Menu nổi (thanh menu dưới đang thu: nút cố định ở giữa đáy màn hình) được đè lên mép dưới hộp bảng nhưng không
  // được đè phần điều khiển của hàng phân trang (mockup 07.10.2026). Tính như khi hộp đứng sát đáy vùng nội dung (bảng
  // vừa khít, hay trang cuộn tới cuối): phần tử nào nằm ngang dưới nút thì chừa đủ để nó lên trên nút, cộng 4 px. Chỗ
  // chừa là lề dưới của hộp (`--report-nhuong`, CSS) nên trang cuộn tới cuối vẫn hở, và bảng ngắn lại đúng chừng đó
  const chuaNutMenu = (vung, day) => {
    const nut = document.getElementById('sp-dock-expand');
    const hop = view && view.querySelector('.report-results');
    if (!nut || !hop) return 0;
    const n = nut.getBoundingClientRect();
    if (!n.width || !n.height) return 0;   // thanh menu đang mở, hay toàn màn hình: không có nút nổi
    const h = hop.getBoundingClientRect();
    let chua = 0;
    for (const o of hop.querySelectorAll(':scope>.phan-trang>span,:scope>.phan-trang>label,:scope>.phan-trang .trang-nut>*')) {
      const r = o.getBoundingClientRect();
      if (!r.width || r.right <= n.left || r.left >= n.right) continue;
      const duoi = vung.bottom - day - (h.bottom - r.bottom);
      if (duoi > n.top) chua = Math.max(chua, Math.ceil(duoi - n.top) + 4);
    }
    return chua;
  };
  // Khung bảng vừa khít màn hình (chủ dự án 03.10.2026): cao tới đáy vùng nội dung `main.noi-dung` (sát thanh menu
  // dưới đáy) tính từ chỗ khung đứng khi trang ở đầu; bộ lọc cao vừa vùng nội dung và cuộn riêng (CSS). Không đủ
  // chỗ (khung nằm thấp) thì cao bằng cả vùng nội dung. Đo lại khi tải, đổi cỡ cửa sổ, thu/mở bộ lọc, đổi Gộp / Không gộp.
  const vuaManHinh = () => {
    danhDauChipTran();
    const main = document.querySelector('main.noi-dung');
    const vung = main ? main.getBoundingClientRect() : {top: 0, bottom: window.innerHeight};
    const cuon = main ? main.scrollTop : window.scrollY;
    const day = main ? parseFloat(getComputedStyle(main).paddingBottom) || 0 : 0;
    const cao = vung.bottom - vung.top;
    // Bộ lọc cao từ chỗ nó đứng khi trang ở đầu tới đáy vùng nội dung, như khung bảng: đáy bộ lọc thẳng đáy hộp kết
    // quả, kéo bộ lọc tới cuối là thấy nút Áp dụng mà không phải cuộn cả trang (lỗi 04.10.2026: bộ lọc cao bằng cả
    // vùng nội dung nhưng đứng dưới hàng chip, đáy lọt dưới thanh menu 71 px). Đo đỉnh lưới bộ lọc + kết quả, không đo
    // chính bộ lọc: bộ lọc `sticky`, trang đã cuộn thì nó đứng ở `top` chứ không ở chỗ thật
    if (workspace) {
      const trenLoc = workspace.getBoundingClientRect().top - vung.top + cuon;
      root.style.setProperty('--report-panel-fit', Math.max(200, Math.floor(cao - trenLoc - day)) + 'px');
    }
    const khung = document.querySelector('.report-table-scroll');
    if (!khung) return;
    const tren = khung.getBoundingClientRect().top - vung.top + cuon;
    // Chừa chỗ cho phần dưới khung trong cùng hộp kết quả (hàng phân trang) và mép dưới của hộp: phân trang luôn
    // nhìn thấy và bấm được — không chừa thì nút trang 2 nằm đúng mép bị che, bấm không trúng (lỗi 03.10.2026)
    let duoiKhung = 0;
    for (let e = khung.nextElementSibling; e; e = e.nextElementSibling) duoiKhung += e.getBoundingClientRect().height;
    const hop = getComputedStyle(khung.parentElement);
    duoiKhung += (parseFloat(hop.paddingBottom) || 0) + (parseFloat(hop.borderBottomWidth) || 0);
    let nhuong = 0;
    if (view) {
      nhuong = chuaNutMenu(vung, day);
      root.style.setProperty('--report-nhuong', nhuong + 'px');
    }
    let vua = cao - tren - day - duoiKhung - nhuong;
    // Khung nằm thấp (Bảng dữ liệu có phần thông tin, bộ lọc ngang ở trên; màn hình thấp): cuộn trang tới khung
    // thì bảng cao bằng cả vùng nội dung, không co lại còn một mẩu
    if (vua < 240) vua = cao - day - duoiKhung - nhuong - (main ? parseFloat(getComputedStyle(main).paddingTop) || 0 : 0);
    root.style.setProperty('--report-fit', Math.max(240, Math.floor(vua)) + 'px');
  };
  vuaManHinh();
  window.addEventListener('resize', vuaManHinh);
  // TL-74 (Báo cáo tổng hợp): thanh menu dưới thu sau lần đo đầu (solarpunk-shell.js chạy sau tệp này), bấm Thu gọn /
  // Menu, bật tắt Mở rộng ERP đều đổi cỡ vùng nội dung mà cửa sổ không đổi — đo lại theo cỡ `main`. Quan sát viền
  // ngoài: nó là phần màn hình còn lại sau thanh trên và thanh menu, không theo nội dung, nên đo lại không gây vòng lặp
  // (thanh cuộn hiện ra không đổi viền ngoài). Thu/mở bộ lọc trượt 0,2 s: đo lại khi trượt xong vì hàng phân trang dịch
  // ngang — nút Menu nổi có thể thôi đè hay bắt đầu đè
  const vungNoiDung = document.querySelector('main.noi-dung');
  if (view && vungNoiDung && 'ResizeObserver' in window) {
    new ResizeObserver(() => vuaManHinh()).observe(vungNoiDung, {box: 'border-box'});
  }
  if (view && workspace) {
    workspace.addEventListener('transitionend', event => {
      if (event.target === workspace && event.propertyName === 'grid-template-columns') vuaManHinh();
    });
  }
  // Dòng TỔNG CỘNG (mỗi loại tiền một dòng, ADR-046) dính ngay dưới hàng tiêu đề của chính bảng đó, dòng thứ i
  // lùi thêm i × --total-h. Mỗi bảng tự đo và đo lại mỗi khi bảng đổi cỡ — khung giãn 0,2 s sau Toàn màn hình
  // hay thu bộ lọc, phông tải muộn — chứ không chỉ khi đổi cỡ cửa sổ (TL-69). Chạy cho mọi bảng báo cáo trên
  // trang, kể cả Bảng dữ liệu dạng báo cáo (cùng khối bảng, không có khung bộ lọc). Đo hai lượt (đọc hết rồi mới
  // ghi) để không bắt trình duyệt dàn trang lại sau mỗi bảng; `ganBang` chạy lại sau khi đổi Gộp / Không gộp.
  const doBang = tables => {
    const so = tables.map(table => {
      const total = table.querySelector('.report-total');
      return [table, table.tHead ? table.tHead.getBoundingClientRect().height : null,
              total ? total.getBoundingClientRect().height : null];
    });
    for (const [table, head, total] of so) {
      if (head !== null) table.style.setProperty('--head-h', head + 'px');
      if (total !== null) table.style.setProperty('--total-h', total + 'px');
    }
  };
  const observer = 'ResizeObserver' in window ? new ResizeObserver(entries => doBang(entries.map(entry => entry.target))) : null;
  const ganBang = () => {
    const tables = [...document.querySelectorAll('.report-table')];
    doBang(tables);
    if (observer) {
      observer.disconnect();
      tables.forEach(table => observer.observe(table));
    }
  };
  ganBang();
  if (!observer) window.addEventListener('resize', () => doBang([...document.querySelectorAll('.report-table')]));
  // Chuyển trang thay vùng bảng (phan-trang.js, AC-10.19): gắn lại đo chiều cao dòng dính cho bảng mới
  document.addEventListener('knjsc:vung-moi', () => { ganBang(); vuaManHinh(); });

  // ② Kéo ngang: chỉ cột đầu, Nhân sự, Loại tiền đứng yên. Đã kéo thì hiện bóng mép (`data-keo`); kéo xong thì
  // nhích cho cột số đầu tiên sau vùng đứng yên hiện trọn — theo hướng đang kéo, để mũi tên phải vẫn tiến tiếp.
  // Nghe ở `document` (sự kiện cuộn không nổi bọt nhưng bắt được ở pha capture) nên phủ cả Bảng dữ liệu và khung
  // bảng mới sau khi đổi Gộp / Không gộp. Lần cuộn do chính nó gây ra nhận ra bằng giá trị đích.
  const viTriNgang = new WeakMap();
  const khoiDangXem = khung => {
    const kb = khung.getBoundingClientRect();
    const main = document.querySelector('main.noi-dung');
    const mb = main ? main.getBoundingClientRect() : {top: 0, bottom: window.innerHeight};
    const giua = (Math.max(kb.top, mb.top, 0) + Math.min(kb.bottom, mb.bottom, window.innerHeight)) / 2;
    const khoi = [...khung.querySelectorAll('.report-block')];
    return khoi.find(b => { const r = b.getBoundingClientRect(); return r.top <= giua && r.bottom >= giua; })
      || khoi.find(b => b.getBoundingClientRect().bottom > giua) || khoi[khoi.length - 1];
  };
  const nhich = khung => {
    const truoc = viTriNgang.get(khung) || {left: 0, dich: null};
    const left = khung.scrollLeft;
    const xong = () => viTriNgang.set(khung, {left, dich: null});
    // Vừa nhích xong. Sai 2 px: đích ở mép phải có khi chỉ tới được 569 khi tính ra 570 (bề rộng lẻ) — không thì
    // lần sau tưởng là kéo lùi rồi giật bảng ngược về cột trước
    if (truoc.dich !== null && Math.abs(left - truoc.dich) < 2) return xong();
    if (Math.abs(left - truoc.left) < 1) return xong();                           // chỉ cuộn dọc
    const khoi = khoiDangXem(khung);
    const bang = khoi && khoi.querySelector('.report-table');
    if (!bang || !bang.tHead) return xong();
    const ths = [...bang.tHead.rows[0].cells];
    const yen = ths.filter(th => th.classList.contains('report-identity') && !th.classList.contains('report-troi'));
    if (!yen.length) return xong();
    const mep = Math.max(...yen.map(th => th.getBoundingClientRect().right));
    const vat = ths.find(th => {
      if (th.classList.contains('report-identity')) return false;
      const r = th.getBoundingClientRect();
      return r.left < mep - 1 && r.right > mep + 1;
    });
    if (!vat) return xong();
    const r = vat.getBoundingClientRect();
    const toiDa = khung.scrollWidth - khung.clientWidth;
    const dich = Math.max(0, Math.min(toiDa, Math.round(left > truoc.left ? left + (r.right - mep) : left - (mep - r.left))));
    if (Math.abs(dich - left) < 1) return xong();
    viTriNgang.set(khung, {left: dich, dich});
    khung.scrollTo({left: dich, behavior: giamChuyenDong.matches ? 'auto' : 'smooth'});
  };
  const coScrollEnd = 'onscrollend' in window;
  const henNhich = new WeakMap();
  document.addEventListener('scroll', event => {
    const khung = event.target;
    if (!(khung instanceof Element) || !khung.classList.contains('report-table-scroll')) return;
    khung.toggleAttribute('data-keo', khung.scrollLeft > 0);
    if (!coScrollEnd) {
      clearTimeout(henNhich.get(khung));
      henNhich.set(khung, setTimeout(() => nhich(khung), 160));
    }
  }, {capture: true, passive: true});
  if (coScrollEnd) {
    document.addEventListener('scrollend', event => {
      const khung = event.target;
      if (khung instanceof Element && khung.classList.contains('report-table-scroll')) nhich(khung);
    }, {capture: true, passive: true});
  }
  for (const khung of document.querySelectorAll('.report-table-scroll')) khung.toggleAttribute('data-keo', khung.scrollLeft > 0);

  // ④ Menu ⋯ trên thanh trên cùng: nút mở/đóng hộp kiểu disclosure (không role=menu, Tab đi qua các mục như thường).
  // Đóng khi bấm ra ngoài, khi focus rơi ra ngoài (Tab đi tiếp — bắt `focusin` ở ngoài chứ không `focusout`: bấm lề
  // hay nhãn trong menu cũng làm mất focus, Safari không focus nút khi bấm), khi chọn một mục, và Escape. Menu đóng mà
  // focus đang trong nó (mục vừa bấm bị ẩn theo) thì focus về ⋯. Việc của từng mục chạy ở bộ nghe của mục đó.
  const dongMenu = (traFocus = true) => {
    if (!themMenu || themMenu.hidden) return;
    const trongMenu = themMenu.contains(document.activeElement);
    themMenu.hidden = true;
    themNut.setAttribute('aria-expanded', 'false');
    if (traFocus && trongMenu) themNut.focus({preventScroll: true});
  };
  if (them && themNut && themMenu) {
    themNut.addEventListener('click', () => {
      if (!themMenu.hidden) { dongMenu(false); return; }
      themMenu.hidden = false;
      themNut.setAttribute('aria-expanded', 'true');
    });
    document.addEventListener('click', event => {
      if (themMenu.hidden) return;
      if (!them.contains(event.target)) dongMenu(false);
      else if (event.target.closest('.report-them-muc')) dongMenu();
    });
    document.addEventListener('focusin', event => { if (!them.contains(event.target)) dongMenu(false); });
    // Escape khi menu mở: đăng ký trước Escape của panel và bố cục (cùng pha capture) và chặn lan, để Escape của
    // khung ERP (thoát Mở rộng ERP, solarpunk-shell.js) không chạy theo
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || event.defaultPrevented || event.isComposing || themMenu.hidden) return;
      dongMenu(false);
      themNut.focus({preventScroll: true});
      event.preventDefault();
      event.stopPropagation();
    }, true);
  }

  // ① Panel ở đầu hộp bảng (Giải thích số liệu, Ngưỡng màu): nút `[data-mo-ra]` đảo `hidden` và `aria-expanded`. Từ
  // 07.10.2026 nút là mục của menu ⋯: chọn thì menu đóng; panel vừa mở thì cuộn vào tầm nhìn và focus nút Đóng của nó,
  // vừa đóng thì focus về ⋯. Nút Đóng (`data-dong`) đóng panel qua đúng mục menu. Escape khi focus đang trong panel,
  // trên nút của nó, hay trên ⋯ (menu đóng, panel mở từ menu) thì đóng panel và trả focus về nút — nút nằm trong menu
  // đang đóng thì về ⋯ — đăng ký sau Escape của menu, trước phím Escape của bố cục (cùng pha capture) nên được xét
  // trước ngăn kéo và toàn màn hình.
  const datPanel = (nut, mo) => {
    const noi = document.getElementById(nut.getAttribute('aria-controls'));
    if (!noi) return;
    noi.hidden = !mo;
    nut.setAttribute('aria-expanded', String(mo));
  };
  // Chỗ trả focus: chính nút, hay ⋯ khi nút nằm trong menu đang đóng
  const veNut = nut => (nut && !nut.closest('[hidden]') ? nut : themNut || nut);
  document.addEventListener('click', event => {
    const dong = event.target.closest('button[data-dong]');
    if (dong) {
      const nutPanel = document.querySelector(`button[data-mo-ra][aria-controls="${dong.dataset.dong}"]`);
      if (nutPanel) datPanel(nutPanel, false);
      veNut(nutPanel)?.focus({preventScroll: true});
      return;
    }
    const nut = event.target.closest('button[data-mo-ra]');
    if (!nut) return;
    const mo = nut.getAttribute('aria-expanded') !== 'true';
    datPanel(nut, mo);
    if (!themMenu || !themMenu.contains(nut)) return;
    dongMenu(false);
    const noi = document.getElementById(nut.getAttribute('aria-controls'));
    if (mo && noi) {
      noi.scrollIntoView({block: 'nearest', behavior: giamChuyenDong.matches ? 'auto' : 'smooth'});
      (noi.querySelector('[data-dong]') || noi).focus({preventScroll: true});
    } else themNut.focus({preventScroll: true});
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || event.isComposing) return;
    const dang = document.activeElement;
    const dangMo = [...document.querySelectorAll('button[data-mo-ra][aria-expanded="true"]')];
    const nut = dangMo.find(n => {
      const noi = document.getElementById(n.getAttribute('aria-controls'));
      return n === dang || (noi && noi.contains(dang));
    }) || (themNut && dang === themNut ? dangMo.find(n => themMenu.contains(n)) : undefined);
    if (!nut) return;
    datPanel(nut, false);
    veNut(nut)?.focus({preventScroll: true});
    event.preventDefault();
    event.stopPropagation();
  }, true);

  let veLaiBoLoc = () => {};
  if (view && workspace && panel && filterToggle && focusToggle) {
    const storageKey = 'knjsc-report-layout';
    const narrowQuery = window.matchMedia('(max-width:900px)');
    const narrow = () => narrowQuery.matches;
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
    const render = () => {
      // Số bộ lọc đang áp đọc lại mỗi lần vẽ: đổi Gộp / Không gộp tại chỗ cũng đổi số này (chip Gộp)
      const active = Number(workspace.dataset.active || 0);
      // Hẹp: chỉ có mở (ngăn kéo) hoặc đóng. Rộng: mở hoặc thanh dọc.
      const shown = narrow() ? (state.filters === 'open' ? 'open' : 'closed') : state.filters;
      const open = shown === 'open';
      const focusTrong = !open && panel.contains(document.activeElement);
      workspace.dataset.filters = shown;
      // Bộ lọc vừa đóng khi focus đang ở trong: màn hẹp về nút "Lọc", màn rộng về nút mở ở thanh dọc (nút lọc trên
      // thanh trên cùng chỉ hiện ở màn hẹp)
      if (focusTrong) (narrow() ? filterToggle : document.getElementById('report-panel-expand') || filterToggle).focus({preventScroll: true});
      filterToggle.setAttribute('aria-expanded', String(open));
      // Nút lọc chỉ hiện ở màn hẹp (chip ẩn): "Lọc (n)" cho biết đang áp mấy bộ lọc
      if (label) label.textContent = open ? 'Thu gọn bộ lọc' : (active ? `Lọc (${active})` : 'Lọc');
      root.classList.toggle('sp-report-focus', state.focus);
      // Tái sử dụng khung tập trung ERP; không đổi lựa chọn mở rộng ERP của người dùng.
      root.classList.toggle('sp-erp-table-focus', state.focus);
      focusToggle.setAttribute('aria-pressed', String(state.focus));
      // Mục Toàn màn hình của menu ⋯: đổi chữ, giữ icon
      const nhanFocus = focusToggle.querySelector('b');
      const phuFocus = focusToggle.querySelector('small');
      if (nhanFocus) nhanFocus.textContent = state.focus ? 'Thoát toàn màn hình' : 'Toàn màn hình';
      else focusToggle.textContent = state.focus ? 'Thoát toàn màn hình' : 'Toàn màn hình';
      if (phuFocus) phuFocus.textContent = state.focus ? 'Hoặc bấm Esc' : 'Esc để thoát';
      vuaManHinh();
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
    veLaiBoLoc = render;
    filterToggle.addEventListener('click', () => setFilters(workspace.dataset.filters === 'open' ? 'rail' : 'open'));
    document.getElementById('report-panel-collapse')?.addEventListener('click', () => setFilters('rail'));
    document.getElementById('report-panel-expand')?.addEventListener('click', () => {
      setFilters('open');
      // Nút ở thanh dọc vừa ẩn theo: focus sang nút thu ‹ của bộ lọc (màn rộng)
      if (!narrow()) document.getElementById('report-panel-collapse')?.focus({preventScroll: true});
    });
    document.getElementById('report-backdrop')?.addEventListener('click', () => setFilters('rail'));
    focusToggle.addEventListener('click', () => setFocus(!state.focus));
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || event.defaultPrevented || event.isComposing) return;
      // Hộp đang mở (dialog, menu thanh dưới) tự lo Escape của nó. Trừ ô Sản phẩm (`details.report-multi`): nó mở sẵn
      // khi đang lọc theo sản phẩm, không phải hộp nổi — trước đây làm Escape không thoát được gì (TL-75)
      if (document.querySelector('dialog[open], details[open]:not(.report-multi)')) return;
      // Escape: đóng ngăn kéo trước, thoát toàn màn hình sau. Mục Toàn màn hình nằm trong menu ⋯ đang đóng: focus về ⋯
      if (narrow() && workspace.dataset.filters === 'open') { setFilters('rail'); filterToggle.focus({preventScroll: true}); }
      else if (state.focus) { setFocus(false); veNut(focusToggle).focus({preventScroll: true}); }
      else return;
      event.preventDefault();
      event.stopPropagation();
    }, true);
    narrowQuery.addEventListener('change', event => { if (event.matches && state.filters === 'open') state.filters = 'rail'; render(); });
  }
  // ③ Gộp / Không gộp (chỉ Báo cáo tổng hợp, `#report-view`; từ 07.10.2026 là hai mục của menu ⋯ trên thanh trên
  // cùng): tải trang của chế độ kia bằng fetch rồi chỉ thay phần đổi theo chế độ — khung bảng, phân trang, chip; cập
  // nhật link Xuất Excel, hai mục menu (`aria-current`, `href`), ô `next` của form ngưỡng, số bộ lọc. Chip, link Excel
  // và mục menu nằm trên thanh trên cùng, ngoài `#report-view`, nên đọc cả trang tải về. Chọn mục thì menu đóng, focus
  // về ⋯ ngay, không đợi tải. Panel đang mở và số đang gõ dở giữ nguyên.
  // Không dùng hx-push-url: htmx sẽ chép cả trang báo cáo (số liệu kinh doanh) vào localStorage. Lỗi, bị chuyển
  // hướng (hết phiên) hay trang trả về lạ thì tải cả trang như trước. Giữ đúng ngày đang xem và vị trí kéo ngang.
  // Bảng dữ liệu không có `#report-view`: bấm Gộp vẫn tải cả trang.
  if (view && document.querySelector('a[data-che-do]')) {
    let luot = 0;
    let dangTai = null;
    let hienTai = location.pathname + location.search;
    const tren = khung => {
      const main = document.querySelector('main.noi-dung');
      return Math.max(khung.getBoundingClientRect().top, main ? main.getBoundingClientRect().top : 0, 0);
    };
    const dayDinh = (bang, moc) => Math.max(moc, ...[bang.tHead.rows[0], ...bang.querySelectorAll('.report-total')]
      .map(tr => tr.firstElementChild.getBoundingClientRect().bottom));
    // Ngày đang xem: khối ngày đầu tiên còn lộ (Không gộp), hay dòng đầu tiên dưới phần dính (Gộp). Khối toàn kỳ
    // giống hệt ở hai chế độ nên đang xem nó thì trả null — giữ nguyên chỗ cuộn
    const ngayDangXem = khung => {
      const dinh = tren(khung);
      const khoi = [...khung.querySelectorAll('.report-block')].find(b => b.getBoundingClientRect().bottom > dinh + 40);
      if (!khoi || khoi.classList.contains('report-block-period')) return null;
      if (khoi.dataset.ngay) return khoi.dataset.ngay;
      const bang = khoi.querySelector('.report-table');
      if (!bang) return null;
      const duoi = dayDinh(bang, dinh);
      const dong = [...bang.querySelectorAll('tbody tr[data-ngay]')].find(tr => tr.getBoundingClientRect().bottom > duoi + 4);
      return dong ? dong.dataset.ngay : null;
    };
    const toiNgay = (khung, ngay) => {
      const dinh = tren(khung);
      const khoi = khung.querySelector(`.report-block[data-ngay="${ngay}"]`);
      if (khoi) {
        khung.scrollTop += khoi.getBoundingClientRect().top - dinh;
        return;
      }
      const dong = khung.querySelector(`tr[data-ngay="${ngay}"]`);
      if (!dong) return;
      const bang = dong.closest('.report-table');
      const cs = getComputedStyle(bang);
      const phanDinh = parseFloat(cs.getPropertyValue('--head-h')) +
        bang.querySelectorAll('.report-total').length * parseFloat(cs.getPropertyValue('--total-h'));
      khung.scrollTop += dong.getBoundingClientRect().top - dinh - phanDinh;
    };
    const chepThuocTinh = (cu, moi, ten) => {
      if (!cu || !moi) return;
      if (moi.hasAttribute(ten)) cu.setAttribute(ten, moi.getAttribute(ten)); else cu.removeAttribute(ten);
    };
    const doiCheDo = async (url, ghiLichSu, veDau = false) => {
      const khung = view.querySelector('.report-table-scroll');
      if (!khung) { location.assign(url); return; }
      const id = ++luot;
      if (dangTai) dangTai.abort();
      const huy = new AbortController();
      dangTai = huy;
      const ngay = ngayDangXem(khung);
      const doc = khung.scrollTop;
      const ngang = khung.scrollLeft;
      khung.setAttribute('aria-busy', 'true');
      let trang;
      let moi;
      try {
        const tra = await fetch(url, {credentials: 'same-origin', signal: huy.signal});
        if (!tra.ok || tra.redirected) throw new Error('tai-ca-trang');
        trang = new DOMParser().parseFromString(await tra.text(), 'text/html');
        moi = trang.getElementById('report-view');
        if (!moi || !moi.querySelector('.report-table-scroll')) throw new Error('tai-ca-trang');
      } catch (loi) {
        if (loi.name !== 'AbortError') location.assign(url);
        return;
      }
      if (id !== luot) return;   // đã có lượt mới hơn
      dangTai = null;
      const khungMoi = moi.querySelector('.report-table-scroll');
      khung.replaceWith(khungMoi);
      const phanTrang = view.querySelector('.report-results>.phan-trang');
      const phanTrangMoi = moi.querySelector('.report-results>.phan-trang');
      if (phanTrang && phanTrangMoi) phanTrang.replaceWith(phanTrangMoi);
      else if (phanTrang) phanTrang.remove();
      else if (phanTrangMoi) khungMoi.after(phanTrangMoi);
      const chips = document.getElementById('report-chips');
      const chipsMoi = trang.getElementById('report-chips');
      if (chips && chipsMoi) chips.replaceWith(chipsMoi);
      vuaManHinh();   // chip đổi: thanh trên có thể đổi chỗ, chip có thể thôi tràn
      chepThuocTinh(document.getElementById('report-xuat'), trang.getElementById('report-xuat'), 'href');
      chepThuocTinh(view.querySelector('#report-nguong input[name=next]'), moi.querySelector('#report-nguong input[name=next]'), 'value');
      chepThuocTinh(workspace, moi.querySelector('#report-workspace'), 'data-active');
      const huyHieu = view.querySelector('.panel-rail .huy-hieu');
      const huyHieuMoi = moi.querySelector('.panel-rail .huy-hieu');
      if (huyHieu && huyHieuMoi) {
        huyHieu.textContent = huyHieuMoi.textContent;
        chepThuocTinh(huyHieu, huyHieuMoi, 'hidden');
      }
      for (const a of document.querySelectorAll('a[data-che-do]')) {
        const b = trang.querySelector(`a[data-che-do="${a.dataset.cheDo}"]`);
        chepThuocTinh(a, b, 'aria-current');
        chepThuocTinh(a, b, 'href');
      }
      if (ghiLichSu) history.pushState({baoCaoGop: true}, '', url);
      hienTai = location.pathname + location.search;
      veLaiBoLoc();
      ganBang();
      khungMoi.scrollLeft = ngang;
      if (veDau) khungMoi.scrollTop = 0;   // sang trang khác: xem từ dòng đầu trang mới
      else if (ngay) toiNgay(khungMoi, ngay); else khungMoi.scrollTop = doc;
      khungMoi.toggleAttribute('data-keo', khungMoi.scrollLeft > 0);
    };
    document.addEventListener('click', event => {
      const muc = event.target.closest('a[data-che-do][href]');
      if (!muc || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      dongMenu();
      if (muc.getAttribute('aria-current') === 'true') return;   // đang ở cách này rồi
      doiCheDo(muc.href, true);
    });
    // Chuyển trang (thanh phân trang dùng chung phát `knjsc:phan-trang`, AC-10.19): cùng đường đổi bảng tại chỗ như Gộp
    view.addEventListener('knjsc:phan-trang', event => {
      if (!event.target.closest('.report-results')) return;
      event.preventDefault();
      doiCheDo(event.detail.url, true, true);
    });
    // Back / Forward giữa hai chế độ: đổi bảng tại chỗ, không thêm mục lịch sử; chỉ đổi phần # thì bỏ qua
    window.addEventListener('popstate', () => {
      const dich = location.pathname + location.search;
      if (dich !== hienTai) doiCheDo(location.href, false);
    });
  }
  // Chọn nhanh kỳ (ADR-038): điền hai ô ngày rồi gửi bộ lọc ngay. Ô ẩn `ky` nhớ nút vừa bấm để máy chủ chỉ
  // tô một nút khi hai nút cùng khoảng (ngày 01: Hôm nay = Tháng này); sửa tay ô ngày thì bỏ `ky`.
  const filters = document.querySelector('.report-filters');
  const fromInput = document.getElementById('tu');
  const toInput = document.getElementById('den');
  const presetKey = document.getElementById('ky');
  if (filters && fromInput && toInput) {
    const presets = filters.querySelectorAll('.report-preset');
    for (const button of presets) {
      button.addEventListener('click', () => {
        fromInput.value = button.dataset.tu;
        toInput.value = button.dataset.den;
        if (presetKey) presetKey.value = button.dataset.key;
        for (const other of presets) other.classList.toggle('is-active', other === button);
        if (typeof filters.requestSubmit === 'function') filters.requestSubmit(); else filters.submit();
      });
    }
    if (presetKey) for (const input of [fromInput, toInput]) input.addEventListener('input', () => { presetKey.value = ''; });
  }
  // Chọn nhiều sản phẩm (ADR-042): ô tìm nhanh lọc danh sách, Chọn tất cả / Bỏ chọn, nhãn tóm tắt.
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
  // Bảng dữ liệu dạng báo cáo (ADR-042 đợt 4) không có ô Nguồn: chỉ còn tìm nhân sự
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
