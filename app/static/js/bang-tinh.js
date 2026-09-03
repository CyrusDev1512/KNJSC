/* Bảng tính vận đơn — bàn phím và hộp lọc. Nhỏ, không có engine công thức
   (ADR-009): lưới là HTML thật, HTMX lo phần trao đổi với máy chủ.

   Phím trên ô:   mũi tên / Tab đi giữa các ô · Enter, F2 sửa · Esc huỷ
   Trong ô sửa:   Enter lưu (textarea: Ctrl+Enter) · Esc huỷ · Tab lưu rồi sang ô kế
   Cột ẩn nhớ trong localStorage của trình duyệt — không lên máy chủ. */
(function () {
  "use strict";
  var LUOI = document.getElementById("luoi-vd");
  var HOP = document.getElementById("hop-loc");
  if (!LUOI) return;

  function oCanh(td, dr, dc) {
    var tr = td.parentElement;
    var cac = Array.prototype.slice.call(tr.children);
    var i = cac.indexOf(td) + dc;
    var hang = tr;
    while (dr > 0 && hang.nextElementSibling) { hang = hang.nextElementSibling; dr--; }
    while (dr < 0 && hang.previousElementSibling) { hang = hang.previousElementSibling; dr++; }
    var muc = hang.children[Math.max(0, Math.min(i, hang.children.length - 1))];
    return muc && muc.hasAttribute("tabindex") ? muc : null;
  }

  function moSua(td) {
    if (!td.dataset.suaUrl) return;
    htmx.ajax("GET", td.dataset.suaUrl, { target: td, swap: "outerHTML" });
  }

  function huySua(td) {
    if (!td.dataset.hienUrl) return;
    htmx.ajax("GET", td.dataset.hienUrl, { target: td, swap: "outerHTML" });
  }

  var HUONG = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] };

  document.addEventListener("keydown", function (e) {
    var td = e.target.closest && e.target.closest("td[tabindex], td.dang-sua");
    if (!td || !LUOI.contains(td)) return;

    if (td.classList.contains("dang-sua")) {
      if (e.key === "Escape") { e.preventDefault(); huySua(td); return; }
      var la_textarea = e.target.tagName === "TEXTAREA";
      if (e.key === "Enter" && (!la_textarea || e.ctrlKey)) {
        e.preventDefault();
        td.querySelector("form").requestSubmit();
        return;
      }
      if (e.key === "Tab") {
        e.preventDefault();
        td.dataset.sauKhiLuu = e.shiftKey ? "trai" : "phai";
        td.querySelector("form").requestSubmit();
      }
      return;
    }

    if (e.key === "Enter" || e.key === "F2") { e.preventDefault(); moSua(td); return; }
    var h = HUONG[e.key] || (e.key === "Tab" ? [0, e.shiftKey ? -1 : 1] : null);
    if (!h) return;
    var dich = oCanh(td, h[0], h[1]);
    if (dich) { e.preventDefault(); dich.focus(); dich.scrollIntoView({ block: "nearest", inline: "nearest" }); }
  });

  // Sau khi máy chủ trả ô mới: đưa con trỏ vào ô sửa, hoặc quay về ô vừa lưu
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var td = e.detail.target;
    if (!td || td.tagName !== "TD") return;
    if (td.classList.contains("dang-sua")) {
      var o = td.querySelector("select, textarea, input:not([type=hidden])");
      if (o) { o.focus(); if (o.select && o.type !== "date") o.select(); }
      return;
    }
    var moi = td;
    if (e.detail.requestConfig && e.detail.requestConfig.elt) {
      var cu = e.detail.requestConfig.elt.closest && e.detail.requestConfig.elt.closest("td");
      var huong = cu && cu.dataset.sauKhiLuu;
      if (huong) moi = oCanh(td, 0, huong === "phai" ? 1 : -1) || td;
    }
    moi.focus();
  });

  // Ô sửa hỏng (400): giữ trình sửa kèm lý do, không thay bằng ô cũ
  document.body.addEventListener("htmx:beforeSwap", function (e) {
    if (e.detail.xhr && e.detail.xhr.status === 400) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });

  // Hộp lọc: đặt ngay dưới nút ▾ vừa bấm
  document.body.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail.target !== HOP) return;
    var nut = e.detail.requestConfig && e.detail.requestConfig.elt;
    if (nut && nut.classList.contains("nut-loc")) {
      var r = nut.getBoundingClientRect();
      HOP.style.top = (window.scrollY + r.bottom + 4) + "px";
      HOP.style.left = Math.max(8, Math.min(window.scrollX + r.left - 200, window.innerWidth - 350)) + "px";
    }
    HOP.hidden = false;
    var dau = HOP.querySelector("input:not([type=hidden])");
    if (dau && !nut.classList.contains("o-nhap")) dau.focus();
  });
  document.addEventListener("click", function (e) {
    if (!HOP || HOP.hidden) return;
    if (HOP.contains(e.target) || e.target.closest(".nut-loc")) return;
    HOP.hidden = true;
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && HOP && !HOP.hidden) HOP.hidden = true;
  });
})();
