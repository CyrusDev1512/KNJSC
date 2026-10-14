/* Hết phiên ở KN CRM — ADR-053 (sửa một điều khoản của ADR-030), TL-02, TL-18.
 *
 * Nạp ngay sau loi-mang.js ở hai khung KN CRM (crm/base_bang_tinh.html, crm/base_crm.html), trước htmx và lưới.
 * 1. Mọi fetch và htmx cùng nguồn mang mã người mở trang (header X-KNJSC-User). Người đang đăng nhập khác người đó thì
 *    máy chủ trả 409 `nguoi_dung_doi` trước mọi view (core.middleware.PageOwnerMiddleware): nháp của A không lưu dưới tên B.
 * 2. Yêu cầu ghi lấy mã CSRF mới trong cookie lúc gửi — header và cả tham số `csrfmiddlewaretoken` (Django đọc tham số
 *    trước header): đăng nhập lại đúng người ở tab khác rồi bấm Thử lại/Lưu là lưu được. Không tự gửi lại bao giờ.
 * 3. htmx gặp trang đăng nhập/đổi mật khẩu, 409 đổi người, 403: không chuyển trang, không dán gì; lời báo ghi vào chính
 *    chỗ đích (chỗ có ô nhập thì chèn ở đầu, không đụng chữ đang gõ), kèm cách làm tiếp; lời nổi khi đích không nằm
 *    trong hộp thoại đang mở. Không ghi gì vào localStorage.
 */
(function () {
  'use strict';
  var me = document.currentScript, d = (me && me.dataset) || {};
  var USER = d.nguoi || '', CODE = d.ma || '', LOGIN = d.dangNhap || '/dang-nhap/', PWD = d.doiMatKhau || '/doi-mat-khau/';
  var COOKIE = d.csrfCookie || 'csrftoken';
  var EXPIRED = 'Phiên đăng nhập đã hết — thay đổi chưa được lưu. Dữ liệu trên màn hình vẫn giữ: đừng tải lại hay đóng ' +
    'trang; đăng nhập lại ở tab mới (đúng tài khoản này) rồi bấm Thử lại hoặc Lưu.';
  var PWD_TEXT = 'Tài khoản phải đổi mật khẩu trước khi lưu — thay đổi chưa được lưu, dữ liệu trên màn hình vẫn giữ. ' +
    'Đổi mật khẩu ở tab mới rồi bấm Thử lại hoặc Lưu.';
  var CSRF_TEXT = 'Mã bảo mật của trang không còn khớp — thay đổi chưa được lưu, dữ liệu trên màn hình vẫn giữ. ' +
    'Bấm Thử lại; vẫn lỗi thì đăng nhập lại ở tab mới.';
  var DENIED = 'Bạn không có quyền với thao tác này — dữ liệu trên màn hình vẫn giữ.';

  function csrfToken() {
    // Hai cookie trùng tên (domain mẹ và host-only) thì Django lấy cái sau cùng — lấy y như vậy
    var found = '';
    document.cookie.split('; ').forEach(function (c) { if (c.indexOf(COOKIE + '=') === 0) found = c.slice(COOKIE.length + 1); });
    try { return decodeURIComponent(found); } catch (e) { return found; }
  }
  function toURL(u) { try { return new URL(u, location.href); } catch (e) { return null; } }
  function sameOrigin(u) { var x = toURL(u); return !!x && x.origin === location.origin; }
  function pathOf(u) { var x = u ? toURL(u) : null; return x ? x.pathname : ''; }
  function mark(error, code) { error.session = true; error.code = code; return error; }

  // Lỗi phiên của một phản hồi fetch (`data`: JSON đã đọc, có thể null); không phải lỗi phiên thì null
  function sessionError(response, data) {
    if (response.redirected) {
      var p = pathOf(response.url);
      if (p === PWD) return mark(new Error(PWD_TEXT), 'doi_mat_khau');
      if (p === LOGIN) return mark(new Error(EXPIRED), 'het_phien');
    }
    // Chỉ phản hồi lỗi: phản hồi 200 cũng có thể mang khoá `code` (mã sản phẩm vừa tạo là "csrf")
    if (response.status === 403 && data && data.code === 'csrf') return mark(new Error(data.error || CSRF_TEXT), 'csrf');
    if (response.status === 409 && data && data.code === 'nguoi_dung_doi') return mark(new Error(data.error), 'nguoi_dung_doi');
    return null;
  }
  // Cách làm tiếp. Đổi người thì chỉ lời dẫn: trang đăng nhập đưa thẳng người đang đăng nhập về lưới (ADR-030)
  function help(error) {
    var box = document.createElement('span');
    box.className = 'het-phien-cach';
    if (error && error.code === 'nguoi_dung_doi') {
      box.textContent = 'Đăng xuất tài khoản đang dùng ở tab khác, đăng nhập lại bằng tài khoản ' +
        (CODE || 'đã mở trang này') + ' rồi bấm Thử lại.';
      return box;
    }
    var a = document.createElement('a');
    a.className = 'nut nut-nho'; a.target = '_blank'; a.rel = 'noopener';
    if (error && error.code === 'doi_mat_khau') { a.href = PWD; a.textContent = 'Đổi mật khẩu (tab mới)'; }
    else {
      a.href = LOGIN + '?het_phien=1&next=' + encodeURIComponent(location.pathname + location.search);
      a.textContent = 'Đăng nhập lại (tab mới)';
    }
    box.appendChild(a);
    return box;
  }

  // (1)(2) fetch: bọc sau loi-mang.js
  if (window.fetch && !window.fetch.__hetPhien) {
    var goc = window.fetch;
    var boc = function (input, init) {
      init = init || {};
      var laRequest = typeof Request !== 'undefined' && input instanceof Request;
      if (!USER || !sameOrigin(laRequest ? input.url : String(input))) return goc(input, init);
      var headers = new Headers(init.headers || (laRequest ? input.headers : undefined));
      headers.set('X-KNJSC-User', USER);
      var method = String(init.method || (laRequest ? input.method : 'GET')).toUpperCase();
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(method)) {
        var token = csrfToken();
        if (token) {
          headers.set('X-CSRFToken', token);
          var body = init.body;
          if (body && typeof body.has === 'function' && typeof body.set === 'function' && body.has('csrfmiddlewaretoken')) {
            body.set('csrfmiddlewaretoken', token);
          }
        }
      }
      return goc(input, Object.assign({}, init, {headers: headers}));
    };
    boc.__hetPhien = true;
    window.fetch = boc;
  }

  // (1)(2) htmx
  document.addEventListener('htmx:configRequest', function (e) {
    // Phần tử bị tách khỏi trang trước khi phản hồi về (ô tìm của hộp lọc bị thay) thì htmx:beforeOnLoad không nổi lên
    // document và htmx sẽ theo HX-Redirect chuyển cả trang: nghe thêm ngay trên phần tử, một lần cho mỗi phần tử
    var elt = e.detail && e.detail.elt;
    if (elt && !elt.__hetPhien) { elt.__hetPhien = true; elt.addEventListener('htmx:beforeOnLoad', beforeOnLoad); }
    if (!USER) return;
    var c = e.detail;
    c.headers['X-KNJSC-User'] = USER;
    if (String(c.verb).toLowerCase() === 'get') return;
    var token = csrfToken();
    if (!token) return;
    c.headers['X-CSRFToken'] = token;
    if (c.parameters && c.parameters.csrfmiddlewaretoken !== undefined) c.parameters.csrfmiddlewaretoken = token;
  });

  // (3) phản hồi htmx
  function header(xhr, ten) { try { return xhr.getResponseHeader(ten) || ''; } catch (e) { return ''; } }
  function readJSON(xhr) {
    if (header(xhr, 'Content-Type').indexOf('application/json') < 0) return null;
    try { return JSON.parse(xhr.responseText); } catch (e) { return null; }
  }
  function htmxError(xhr) {
    var dich = header(xhr, 'HX-Redirect'), p = pathOf(dich || xhr.responseURL || '');
    if (p === PWD) return mark(new Error(PWD_TEXT), 'doi_mat_khau');
    if (p === LOGIN) return mark(new Error(EXPIRED), 'het_phien');
    if (xhr.status === 409 || xhr.status === 403) {
      var data = readJSON(xhr);
      if (data && (data.code === 'nguoi_dung_doi' || data.code === 'csrf')) return mark(new Error(data.error || CSRF_TEXT), data.code);
      if (xhr.status === 403) { var x = new Error(DENIED); x.code = 'tu_choi'; return x; }
    }
    return null;
  }
  function noteIn(target, error) {
    if (!target || target === document.body || target === document.documentElement || !target.isConnected) return;
    var p = document.createElement('div');
    p.className = 'bao bao-xau het-phien-o'; p.setAttribute('role', 'alert');
    p.textContent = error.message + ' ';
    if (error.session) p.appendChild(help(error));
    if (target.querySelector('input, select, textarea')) {
      var cu = target.querySelector(':scope > .het-phien-o');
      if (cu) cu.remove();
      target.insertBefore(p, target.firstChild);
    } else target.replaceChildren(p);
    if (p.scrollIntoView) p.scrollIntoView({block: 'nearest'});
  }
  var hong = null;   // phần tử có yêu cầu hỏng: chỉ khi chính nó gửi lại thành công mới tắt lời nổi (như loi-mang.js)
  function notify(error, elt) {
    var o = document.querySelector('.het-phien-noi');
    if (!o) {
      o = document.createElement('div');
      o.className = 'het-phien-noi'; o.setAttribute('role', 'alert');
      o.style.cssText = 'position:fixed;left:50%;bottom:152px;transform:translateX(-50%);z-index:9999;' +
        'max-width:min(560px,calc(100vw - 32px));padding:12px 40px 12px 16px;border-radius:12px;' +
        'background:var(--critical-soft,#fdecea);color:var(--critical-ink,#7a1c12);' +
        'border:1px solid var(--critical,#c0392b);box-shadow:0 6px 24px rgba(0,0,0,.18);font:inherit;line-height:1.45';
      var dong = document.createElement('button');
      dong.type = 'button'; dong.textContent = '×'; dong.setAttribute('aria-label', 'Đóng thông báo');
      dong.style.cssText = 'position:absolute;top:6px;right:8px;border:0;background:none;font-size:20px;cursor:pointer;color:inherit';
      dong.onclick = function () { o.remove(); };
      o.appendChild(document.createElement('span'));
      o.appendChild(dong);
      document.body.appendChild(o);
    }
    var chu = o.firstChild;
    chu.textContent = error.message + ' ';
    if (error.session) chu.appendChild(help(error));
    hong = elt || null;
  }
  function beforeOnLoad(e) {
    if (e.__hetPhien) return;              // đã xử lý ở chính phần tử, sự kiện nổi lên document thì bỏ qua
    e.__hetPhien = true;
    var xhr = e.detail && e.detail.xhr;
    if (!xhr) return;
    var error = htmxError(xhr);
    if (!error) return;
    e.preventDefault();                    // không theo HX-Redirect, không dán trang đăng nhập, không swap
    var target = e.detail.target, dlg = target && target.closest && target.closest('dialog');
    noteIn(target, error);
    if (!(dlg && dlg.open)) notify(error, e.detail.elt);
  }
  document.addEventListener('htmx:beforeOnLoad', beforeOnLoad);
  document.addEventListener('htmx:afterRequest', function (e) {
    if (!e.detail || !e.detail.successful) return;
    if (!hong || e.detail.elt === hong || !hong.isConnected) {
      hong = null;
      var o = document.querySelector('.het-phien-noi');
      if (o) o.remove();
    }
  });

  window.KNJSC_SESSION = {user: USER, code: CODE, login: LOGIN, pwd: PWD, expiredText: EXPIRED, pwdText: PWD_TEXT,
    csrfText: CSRF_TEXT, csrfToken: csrfToken, sessionError: sessionError, help: help, notify: notify};
})();
