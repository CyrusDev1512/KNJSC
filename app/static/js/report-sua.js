/* Hộp sửa một lần nộp trên Báo cáo tổng hợp — chỉ Admin (ADR-050, chủ dự án duyệt mockup tương tác 10.10.2026).
   Bấm ✎ ở ô đầu một dòng lần nộp: nạp phần form `/bao-cao/<id>/sua/?khung=1&lan=N` vào <dialog id="report-sua-hop">
   (URL ghép từ mẫu `data-sua-mau` của hộp, id ở `data-lan-nop` của dòng, Lần ở `data-lan` của nút), con trỏ ở ô sửa
   đầu tiên; report-entry.js gắn ô số và Xem trước chỉ số qua sự kiện `knjsc:form-moi`. Lưu gửi bằng fetch:
   - 204: đóng hộp, báo đã lưu; có đổi số thì phát `knjsc:bao-cao-da-sua` — report-filters.js thay bảng tại chỗ (giữ
     lọc, trang, ngày đang xem, vị trí kéo ngang) rồi dòng vừa sửa sáng lên vài giây;
   - 400/409: thay nội dung hộp bằng phần form máy chủ trả (409: số mới nhất, ô người khác vừa đổi tô vàng);
   - lỗi mạng, 5xx, hết phiên, bị từ chối, báo cáo vừa bị bỏ: báo trong hộp, giữ số đã gõ, không bao giờ báo
     "Đã lưu" (CLAUDE.md, bắt buộc 13). Máy chủ không trả lời sau HET_GIO thì thôi chờ, báo như mất mạng.
   Đang lưu thì ✕, Huỷ, Escape không đóng hộp: kết quả lượt lưu luôn có chỗ hiện. Escape chỉ đóng hộp; đóng hộp thì
   focus về ✎ của đúng dòng đó (bảng có thể vừa được thay). */
(() => {
  const hop = document.getElementById('report-sua-hop');
  if (!hop) return;
  const HET_GIO = 30000;
  let idMo = null;
  let dangMo = false;
  let dangLuu = false;
  let phien = 0;   // mỗi lần mở hộp một phiên: kết quả của lượt lưu cũ không được đụng vào hộp của lần mở sau
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
    for (const dong of form.querySelectorAll('[data-dong]')) dong.disabled = ban;
    const nut = form.querySelector('button[type=submit]');
    if (nut) {
      nut.disabled = ban;
      nut.textContent = ban ? 'Đang lưu…' : 'Lưu chỉnh sửa';
    }
  };

  const nutCua = id => document.querySelector(`tr[data-lan-nop="${id}"] .report-sua`);
  const urlCua = (nut, id) => `${hop.dataset.suaMau.replace('987654321', id)}&lan=${nut.dataset.lan || ''}`;

  document.addEventListener('click', async event => {
    const nut = event.target.closest('tr[data-lan-nop] .report-sua');
    if (!nut || dangMo) return;
    const id = nut.closest('tr').dataset.lanNop;
    dangMo = true;
    try {
      const tra = await fetch(urlCua(nut, id), {credentials: 'same-origin'});
      if (!tra.ok || tra.redirected) throw new Error(String(tra.status));
      idMo = id;
      phien += 1;
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
    if (event.target.closest('[data-dong]')) { if (!dangLuu) hop.close(); return; }
    const nutLich = event.target.closest('.report-sua-lich-su');
    if (!nutLich) return;
    const lich = hop.querySelector('#report-sua-lich');
    if (!lich) return;
    const mo = lich.hidden;
    lich.hidden = !mo;
    nutLich.setAttribute('aria-expanded', String(mo));
    if (mo) lich.scrollIntoView({block: 'nearest'});
  });

  // Escape khi hộp mở chỉ đóng hộp: chặn ở chính hộp (pha nổi bọt, phím tắt bên trong hộp vẫn chạy) để phím không
  // tới phím tắt của trang (thoát chế độ mở rộng ERP ở solarpunk-shell.js); đang lưu thì giữ hộp
  hop.addEventListener('keydown', event => {
    if (event.key === 'Escape') event.stopPropagation();
  });
  hop.addEventListener('cancel', event => {
    if (dangLuu) event.preventDefault();
  });

  hop.addEventListener('close', () => {
    const nut = idMo && nutCua(idMo);
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
    if (dangLuu) return;   // đang gửi: không gửi hai lần
    const cua = phien;
    const id = form.dataset.baoCao;
    dangLuu = true;
    datBan(form, true);
    const huy = new AbortController();
    const hen = setTimeout(() => huy.abort(), HET_GIO);
    let tra = null;
    let matMang = '';
    try {
      tra = await fetch(form.action, {method: 'POST', body: new FormData(form), credentials: 'same-origin',
                                      signal: huy.signal});
    } catch (loi) {
      matMang = loi.name === 'AbortError' ? 'máy chủ không trả lời sau 30 giây' : 'không kết nối được máy chủ';
    } finally {
      clearTimeout(hen);
      dangLuu = false;
    }
    // Hộp vẫn là của lần nộp này? Chromium vẫn cho Escape lần thứ hai đóng hộp dù đang lưu, rồi mở được hộp khác
    const conHop = hop.open && cua === phien;
    if (tra && tra.status === 204) {
      const coDoi = tra.headers.get('X-Bao-Cao-Doi') !== '0';
      if (conHop) hop.close();
      if (!coDoi) { baoNoi('Không có số nào đổi; không ghi lịch sử.'); return; }
      baoNoi('Đã lưu chỉnh sửa · đã ghi lịch sử', 'da-luu');
      const suKien = new CustomEvent('knjsc:bao-cao-da-sua', {detail: {id}});
      document.dispatchEvent(suKien);
      if (suKien.detail.xong) { await suKien.detail.xong; sangDong(id); } else location.reload();
      return;
    }
    if (!conHop) {
      baoNoi(`Chưa lưu được lần sửa vừa rồi${matMang ? ': ' + matMang : ''}. Bấm ✎ để mở lại.`);
      return;
    }
    if (matMang) {
      datBan(form, false);
      baoLoi(`Chưa lưu được: ${matMang}. Số vừa gõ vẫn còn trong hộp; kiểm tra mạng rồi bấm Lưu lại.`);
      return;
    }
    if ((tra.status === 400 || tra.status === 409) && !tra.redirected) {
      datNoiDung(await tra.text());
      oDau()?.focus();
      return;
    }
    datBan(form, false);
    if (tra.redirected) baoLoi('Phiên đăng nhập đã hết. Tải lại trang, đăng nhập rồi sửa lại; số vừa gõ chưa được lưu.');
    else if (tra.status === 403) {
      baoLoi('Máy chủ từ chối lưu (403): phiên đăng nhập hay quyền vừa đổi. Tải lại trang rồi thử lại; số vừa gõ chưa được lưu.');
    } else if (tra.status === 404) {
      baoLoi('Báo cáo này không còn để sửa (có thể vừa bị bỏ). Tải lại trang để xem; số vừa gõ chưa được lưu.');
    } else baoLoi(`Chưa lưu được: máy chủ báo lỗi (${tra.status}). Số vừa gõ vẫn còn trong hộp; thử bấm Lưu lại sau ít phút.`);
  });
})();
