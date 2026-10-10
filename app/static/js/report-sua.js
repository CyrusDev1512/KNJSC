/* Hộp sửa một lần nộp trên Báo cáo tổng hợp — chỉ Admin (ADR-050, chủ dự án duyệt mockup tương tác 10.10.2026).
   Bấm ✎ ở ô đầu một dòng lần nộp: nạp phần form `/bao-cao/<id>/sua/?khung=1` vào <dialog id="report-sua-hop">, con
   trỏ ở ô sửa đầu tiên; report-entry.js gắn ô số và Xem trước chỉ số qua sự kiện `knjsc:form-moi`. Lưu gửi bằng fetch:
   - 204: đóng hộp, báo đã lưu; có đổi số thì phát `knjsc:bao-cao-da-sua` — report-filters.js thay bảng tại chỗ (giữ
     lọc, trang, ngày đang xem, vị trí kéo ngang) rồi dòng vừa sửa sáng lên vài giây;
   - 400/409: thay nội dung hộp bằng phần form máy chủ trả (409: số mới nhất, ô người khác vừa đổi tô vàng);
   - lỗi mạng, 5xx, hết phiên: báo trong hộp, giữ số đã gõ, không bao giờ báo "Đã lưu" (CLAUDE.md, bắt buộc 13).
   Escape chỉ đóng hộp; đóng hộp thì focus về ✎ của đúng dòng đó (bảng có thể vừa được thay). */
(() => {
  const hop = document.getElementById('report-sua-hop');
  if (!hop) return;
  let urlMo = null;
  let dangMo = false;
  let henBao = null;

  const baoNoi = (chu, loai) => {
    document.querySelector('.report-sua-bao')?.remove();
    clearTimeout(henBao);
    const bao = document.createElement('div');
    bao.className = 'report-sua-bao';
    bao.setAttribute('role', 'status');
    bao.innerHTML = loai === 'da-luu'
      ? '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 6.5 12 13 4.5"/></svg>'
      : '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/><path d="M8 7.2v3.6M8 5v.1"/></svg>';
    bao.append(document.createTextNode(chu));
    document.body.append(bao);
    henBao = setTimeout(() => bao.remove(), 3200);
  };

  // Báo lỗi trong hộp mà không đụng số đang gõ
  const baoLoi = chu => {
    const vung = hop.querySelector('#report-sua-loi');
    if (!vung) { baoNoi(chu); return; }
    vung.replaceChildren();
    const bao = document.createElement('div');
    bao.className = 'bao bao-xau';
    bao.setAttribute('role', 'alert');
    const noi = document.createElement('span');
    noi.textContent = chu;
    bao.append(noi);
    vung.append(bao);
  };

  const oDau = () => hop.querySelector('form[data-khung] .truong.vua-doi .o-nhap:not([readonly])')
    || hop.querySelector('form[data-khung] .bm-ngang input:not([type=hidden]):not([readonly]), form[data-khung] .bm-ngang select');

  const datNoiDung = html => {
    hop.innerHTML = html;
    const form = hop.querySelector('form[data-khung]');
    if (form) form.dispatchEvent(new CustomEvent('knjsc:form-moi', {bubbles: true}));
    return form;
  };

  const datBan = (form, ban) => {
    if (!form) return;
    form.toggleAttribute('aria-busy', ban);
    const nut = form.querySelector('button[type=submit]');
    if (nut) {
      nut.disabled = ban;
      nut.textContent = ban ? 'Đang lưu…' : 'Lưu chỉnh sửa';
    }
  };

  const nutCua = url => [...document.querySelectorAll('.report-sua[data-sua-url]')].find(n => n.dataset.suaUrl === url);

  document.addEventListener('click', async event => {
    const nut = event.target.closest('.report-sua[data-sua-url]');
    if (!nut || dangMo) return;
    dangMo = true;
    try {
      const tra = await fetch(nut.dataset.suaUrl, {credentials: 'same-origin'});
      if (!tra.ok || tra.redirected) throw new Error(String(tra.status));
      urlMo = nut.dataset.suaUrl;
      datNoiDung(await tra.text());
      hop.showModal();
      oDau()?.focus();
    } catch (_) {
      baoNoi('Không mở được hộp sửa. Tải lại trang rồi thử lại.');
    } finally {
      dangMo = false;
    }
  });

  hop.addEventListener('click', event => {
    if (event.target.closest('[data-dong]')) { hop.close(); return; }
    const nutLich = event.target.closest('.report-sua-lich-su');
    if (!nutLich) return;
    const lich = hop.querySelector('#report-sua-lich');
    if (!lich) return;
    const mo = lich.hidden;
    lich.hidden = !mo;
    nutLich.setAttribute('aria-expanded', String(mo));
    if (mo) lich.scrollIntoView({block: 'nearest'});
  });

  // Escape khi hộp mở chỉ đóng hộp: không để phím đi tiếp tới các phím tắt của trang (thoát toàn màn hình, đóng panel)
  window.addEventListener('keydown', event => {
    if (event.key === 'Escape' && hop.open) event.stopPropagation();
  }, true);

  hop.addEventListener('close', () => {
    const nut = urlMo && nutCua(urlMo);
    if (nut) nut.focus({preventScroll: true});
  });

  const sangDong = id => {
    const dong = document.querySelector(`tr[data-lan-nop="${id}"]`);
    if (!dong) return;
    dong.classList.add('report-vua-sua');
    dong.scrollIntoView({block: 'nearest', inline: 'nearest'});
    setTimeout(() => dong.classList.remove('report-vua-sua'), 2600);
    const nut = dong.querySelector('.report-sua');
    if (nut && !hop.open) nut.focus({preventScroll: true});
  };

  hop.addEventListener('submit', async event => {
    const form = event.target.closest('form[data-khung]');
    if (!form) return;
    event.preventDefault();
    if (form.hasAttribute('aria-busy')) return;   // đang gửi: không gửi hai lần
    datBan(form, true);
    let tra;
    try {
      tra = await fetch(form.action, {method: 'POST', body: new FormData(form), credentials: 'same-origin'});
    } catch (_) {
      datBan(form, false);
      baoLoi('Chưa lưu được: không kết nối được máy chủ. Số vừa gõ vẫn còn trong hộp; kiểm tra mạng rồi bấm Lưu lại.');
      return;
    }
    if (tra.status === 204) {
      const coDoi = tra.headers.get('X-Bao-Cao-Doi') !== '0';
      const id = (form.action.match(/\/bao-cao\/(\d+)\/sua\//) || [])[1];
      hop.close();
      if (!coDoi) { baoNoi('Không có số nào đổi; không ghi lịch sử.'); return; }
      baoNoi('Đã lưu chỉnh sửa · đã ghi lịch sử', 'da-luu');
      const suKien = new CustomEvent('knjsc:bao-cao-da-sua', {detail: {id}});
      document.dispatchEvent(suKien);
      if (suKien.detail.xong) { await suKien.detail.xong; sangDong(id); } else location.reload();
      return;
    }
    if ((tra.status === 400 || tra.status === 409) && !tra.redirected) {
      datNoiDung(await tra.text());
      oDau()?.focus();
      return;
    }
    datBan(form, false);
    if (tra.redirected) baoLoi('Phiên đăng nhập đã hết. Đăng nhập lại rồi thử lại; số vừa gõ chưa được lưu.');
    else if (tra.status === 403 || tra.status === 404) baoLoi('Bạn không còn quyền sửa báo cáo này; số vừa gõ chưa được lưu.');
    else baoLoi(`Chưa lưu được: máy chủ báo lỗi (${tra.status}). Số vừa gõ vẫn còn trong hộp; thử bấm Lưu lại sau ít phút.`);
  });
})();
