/* Chuyển trang không tải lại cả trang — AC-10.19 (chủ dự án 07.10.2026).
 *
 * Thanh phân trang dùng chung (`components/phan_trang.html`) nằm trong một vùng `data-vung-trang="<tên>"` thì bấm số
 * trang hay đổi "Mỗi trang" chỉ tải trang mới bằng fetch rồi thay đúng vùng đó: đầu trang, thanh menu, bộ lọc đang mở
 * giữ nguyên, không nháy trắng. URL đổi theo (pushState) nên F5, gửi link, Back/Forward vẫn đúng.
 * Không dùng hx-push-url: htmx sẽ chép cả trang (số liệu kinh doanh) vào localStorage.
 *
 * Báo cáo tổng hợp tự nhận sự kiện `knjsc:phan-trang` (report-filters.js, giữ đúng ngày đang xem). Vùng không đánh dấu,
 * lỗi mạng, hết phiên hay trang trả về lạ thì tải cả trang như trước — không bao giờ kẹt ở trang cũ.
 * Sau khi thay vùng: htmx xử lý lại phần tử mới và phát `knjsc:vung-moi` để script khác gắn lại (bảng báo cáo).
 */
(function () {
  'use strict';
  var luot = 0;
  var dangTai = null;

  function chon(goc, ten) { return goc.querySelector('[data-vung-trang="' + ten + '"]'); }

  // Tải `url` một lần rồi thay mọi vùng có tên trong `cacTen` (Back/Forward trên trang hai bảng thay cả hai)
  function thayVung(cacTen, url, ghiLichSu) {
    if (!window.fetch || !window.DOMParser || !cacTen.every(function (t) { return chon(document, t); })) {
      location.assign(url);
      return;
    }
    var id = ++luot;
    if (dangTai) dangTai.abort();
    var huy = new AbortController();
    dangTai = huy;
    cacTen.forEach(function (t) { chon(document, t).setAttribute('aria-busy', 'true'); });
    fetch(url, {credentials: 'same-origin', signal: huy.signal, headers: {'X-Phan-Trang': '1'}})
      .then(function (tra) {
        if (!tra.ok || tra.redirected) throw new Error('tai-ca-trang');
        return tra.text();
      })
      .then(function (html) {
        if (id !== luot) return;
        dangTai = null;
        var doc = new DOMParser().parseFromString(html, 'text/html');
        if (!cacTen.every(function (t) { return chon(doc, t) && chon(document, t); })) throw new Error('tai-ca-trang');
        var cacMoi = cacTen.map(function (t) {
          var moi = document.importNode(chon(doc, t), true);
          chon(document, t).replaceWith(moi);
          return moi;
        });
        if (ghiLichSu) history.pushState({vungTrang: cacTen[0]}, '', url);
        cacMoi.forEach(function (moi) {
          if (window.htmx) window.htmx.process(moi);
          document.dispatchEvent(new CustomEvent('knjsc:vung-moi', {detail: {vung: moi}}));
        });
        // Đầu vùng đã cuộn khuất (đang ở cuối danh sách dài) thì kéo lên để thấy dòng đầu trang mới
        if (ghiLichSu && cacMoi[0].getBoundingClientRect().top < 0) cacMoi[0].scrollIntoView({block: 'start'});
      })
      .catch(function (loi) {
        if (loi && loi.name === 'AbortError') return;
        location.assign(url);
      });
  }

  function di(phanTu, url) {
    // Ai nhận sự kiện (Báo cáo tổng hợp) thì gọi preventDefault và tự đổi bảng
    var su = new CustomEvent('knjsc:phan-trang', {bubbles: true, cancelable: true, detail: {url: url, el: phanTu}});
    if (!phanTu.dispatchEvent(su)) return;
    var vung = phanTu.closest('[data-vung-trang]');
    if (!vung) { location.assign(url); return; }
    thayVung([vung.getAttribute('data-vung-trang')], url, true);
  }

  // Pha capture ở document: chạy trước `onchange` nội tuyến của ô "Mỗi trang" (đường dự phòng khi tệp này không nạp)
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('.phan-trang a[href]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    e.stopPropagation();
    di(a, a.href);
  }, true);
  document.addEventListener('change', function (e) {
    var o = e.target.closest && e.target.closest('.phan-trang select');
    if (!o) return;
    var chon = o.selectedOptions[0];
    if (!chon || !chon.dataset.href) return;
    e.stopPropagation();
    di(o, new URL(chon.dataset.href, location.href).href);
  }, true);

  // Back / Forward: tải lại đúng các vùng của trang theo URL mới. Trang không có vùng nào thì để script khác lo
  window.addEventListener('popstate', function () {
    var cacTen = [];
    document.querySelectorAll('[data-vung-trang]').forEach(function (v) {
      var ten = v.getAttribute('data-vung-trang');
      if (cacTen.indexOf(ten) < 0) cacTen.push(ten);
    });
    if (cacTen.length) thayVung(cacTen, location.href, false);
  });
})();
