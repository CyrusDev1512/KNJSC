/* Lỗi mạng nói tiếng Việt và không im lặng — AC-10.12 (săn lỗi 06.10.2026).
 *
 * Nạp đầu tiên ở cả bốn khung trang (base.html, base_tran.html, crm/base_crm.html, crm/base_bang_tinh.html):
 * 1. `fetch` hỏng vì mạng (TypeError "Failed to fetch") đổi thành lời tiếng Việt — mọi chỗ đang hiện
 *    `error.message` (lưới, chứng từ, phản hồi vận đơn, Lên đơn) tự có lời dễ hiểu. Huỷ yêu cầu (AbortError) giữ nguyên.
 * 2. Yêu cầu HTMX không gửi được (mất mạng, quá hạn) hay máy chủ trả lỗi 5xx thì hiện một ô báo ở đáy màn hình.
 *    Trước đây HTMX gửi hỏng là im lặng: bấm Lưu đơn lúc mất mạng mà không ai biết đơn chưa lưu.
 */
(function () {
  'use strict';
  var MAT_MANG = 'Mất kết nối mạng — thay đổi chưa được gửi lên máy chủ. Dữ liệu trên màn hình vẫn giữ; ' +
    'kiểm tra mạng rồi thử lại.';

  if (window.fetch && !window.fetch.__loiMang) {
    var goc = window.fetch.bind(window);
    var boc = function () {
      return goc.apply(null, arguments).catch(function (loi) {
        if (loi && loi.name === 'TypeError') {
          var moi = new TypeError(MAT_MANG);
          moi.matMang = true;
          throw moi;
        }
        throw loi;
      });
    };
    boc.__loiMang = true;
    window.fetch = boc;
  }

  function bao(chu) {
    var o = document.querySelector('.loi-mang-noi');
    if (!o) {
      o = document.createElement('div');
      o.className = 'loi-mang-noi';
      o.setAttribute('role', 'alert');
      o.style.cssText = 'position:fixed;left:50%;bottom:96px;transform:translateX(-50%);z-index:9999;' +
        'max-width:min(560px,calc(100vw - 32px));padding:12px 40px 12px 16px;border-radius:12px;' +
        'background:var(--critical-soft,#fdecea);color:var(--critical-ink,#7a1c12);' +
        'border:1px solid var(--critical,#c0392b);box-shadow:0 6px 24px rgba(0,0,0,.18);font:inherit;line-height:1.45';
      var dong = document.createElement('button');
      dong.type = 'button';
      dong.textContent = '×';
      dong.setAttribute('aria-label', 'Đóng thông báo');
      dong.style.cssText = 'position:absolute;top:6px;right:8px;border:0;background:none;font-size:20px;cursor:pointer;color:inherit';
      dong.onclick = function () { o.remove(); };
      o.appendChild(document.createElement('span'));
      o.appendChild(dong);
      document.body.appendChild(o);
    }
    o.firstChild.textContent = chu;
  }

  function tat() {
    var o = document.querySelector('.loi-mang-noi');
    if (o) o.remove();
  }

  // Phần tử có yêu cầu hỏng (form Lên đơn…): chỉ khi chính nó gửi lại thành công mới tắt lời báo. Yêu cầu khác của
  // trang (tra khách theo số điện thoại chạy ngầm) thành công không có nghĩa thay đổi đã lưu — trước đây nó xoá lời báo
  // và người dùng tưởng đơn đã lưu
  var hong = null;
  function phanTu(e) { return e.detail && e.detail.elt; }
  document.addEventListener('htmx:sendError', function (e) { hong = phanTu(e); bao(MAT_MANG); });
  document.addEventListener('htmx:timeout', function (e) { hong = phanTu(e); bao(MAT_MANG); });
  document.addEventListener('htmx:responseError', function (e) {
    var ma = e.detail && e.detail.xhr ? e.detail.xhr.status : 0;
    if (ma >= 500) {
      hong = phanTu(e);
      bao('Máy chủ đang gặp lỗi (mã ' + ma + '). Dữ liệu trên màn hình vẫn giữ; thử lại sau ít phút, ' +
        'lặp lại thì báo quản trị.');
    }
  });
  // Không tự tắt khi có mạng lại: người dùng vẫn phải bấm gửi lại. Tắt khi họ đóng, khi chính phần tử đó gửi lại thành
  // công, hoặc khi phần tử đó không còn trên trang (đã bị thay bằng kết quả mới)
  document.addEventListener('htmx:afterRequest', function (e) {
    if (!e.detail || !e.detail.successful) return;
    if (!hong || phanTu(e) === hong || !hong.isConnected) { hong = null; tat(); }
  });
})();
