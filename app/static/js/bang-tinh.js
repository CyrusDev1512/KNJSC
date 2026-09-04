/* Bảng tính — bàn phím, hộp lọc, dòng trống, thanh bên, ẩn cột. Nhỏ, không có
   engine công thức (ADR-009): lưới là HTML thật, HTMX lo phần trao đổi với
   máy chủ. ADR-010 thêm dòng trống, thanh bên, thanh công cụ.

   Phím trên ô:   mũi tên / Tab đi giữa các ô · Enter, F2 sửa · Esc huỷ
   Trong ô sửa:   Enter lưu (textarea: Ctrl+Enter) · Esc huỷ · Tab lưu rồi sang ô kế
   Dòng trống:    gõ rồi rời khỏi dòng (hoặc Enter) là lưu
   Cột ẩn và thanh bên thu gọn nhớ trong localStorage — không lên máy chủ. */
(function () {
  "use strict";
  var LUOI = document.getElementById("luoi-vd");
  var HOP = document.getElementById("hop-loc");
  var BO_CUC = document.getElementById("bt-bo-cuc");
  var HOP_AN_COT = document.getElementById("bt-an-cot-hop");
  if (!LUOI) return;
  var MA_BANG = LUOI.dataset.bang || "";

  function nho(khoa, gia_tri) {
    try { if (gia_tri === null) localStorage.removeItem(khoa); else localStorage.setItem(khoa, gia_tri); } catch (e) {}
  }
  function doc(khoa) { try { return localStorage.getItem(khoa); } catch (e) { return null; } }

  function oCanh(td, dr, dc) {
    var tr = td.parentElement;
    var cac = Array.prototype.slice.call(tr.children);
    var i = cac.indexOf(td);
    var hang = tr;
    while (dr > 0 && hang.nextElementSibling) { hang = hang.nextElementSibling; dr--; }
    while (dr < 0 && hang.previousElementSibling) { hang = hang.previousElementSibling; dr++; }
    // Bỏ qua cột ẩn khi đi ngang
    var j = i;
    do { j += dc; } while (hang.children[j] && hang.children[j].hidden);
    if (dc === 0) j = i;
    var muc = hang.children[Math.max(0, Math.min(j, hang.children.length - 1))];
    if (!muc) return null;
    if (muc.classList.contains("o-moi")) return muc.querySelector("input") || null;
    return muc.hasAttribute("tabindex") ? muc : null;
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

  // Cột cố định: máy chủ ước lượng `left` theo bề rộng khai sẵn, nhưng bề
  // rộng thật do trình duyệt quyết — đo lại rồi đặt đúng, không thì cột trôi
  // vài px khi cuộn. Chạy lúc tải trang, khi đổi cỡ cửa sổ và sau khi ẩn cột.
  function canhCotCoDinh() {
    var hang = LUOI.querySelector("thead tr");
    if (!hang) return;
    var trai = 0;
    Array.prototype.forEach.call(hang.children, function (th, i) {
      if (!th.classList.contains("co-dinh") || th.hidden) return;
      var rong = th.getBoundingClientRect().width;
      var cot = LUOI.querySelectorAll("tr > *:nth-child(" + (i + 1) + ")");
      Array.prototype.forEach.call(cot, function (o) { o.style.left = trai + "px"; });
      trai += rong;
    });
  }
  canhCotCoDinh();
  window.addEventListener("resize", canhCotCoDinh);
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (t && (t.tagName === "TD" || t.tagName === "TR")) canhCotCoDinh();
  });

  // ── Bàn phím trên ô ──
  document.addEventListener("keydown", function (e) {
    var td = e.target.closest && e.target.closest("td[tabindex], td.dang-sua, td.o-moi");
    if (!td || !LUOI.contains(td)) return;

    if (td.classList.contains("o-moi")) {
      if (e.key === "Enter") { e.preventDefault(); luuDongMoi(td.parentElement, "xuong"); return; }
      if (e.key === "Escape") { e.preventDefault(); xoaDongMoi(td.parentElement); return; }
      var hh = HUONG[e.key];
      if (hh && (hh[0] !== 0 || e.target.selectionStart === e.target.value.length || e.target.selectionStart === 0)) {
        var dich0 = oCanh(td, hh[0], hh[1]);
        if (dich0) { e.preventDefault(); dich0.focus(); }
      }
      return;
    }

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

  // Ô sửa hỏng (400): giữ trình sửa kèm lý do, không thay bằng ô cũ.
  // Dòng trống hỏng (400) cũng vậy: giữ giá trị đã gõ, hiện lý do.
  document.body.addEventListener("htmx:beforeSwap", function (e) {
    if (e.detail.xhr && e.detail.xhr.status === 400) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });

  // ── Dòng trống cuối lưới ──
  function coGiGo(tr) {
    return Array.prototype.some.call(tr.querySelectorAll("input"), function (i) { return i.value.trim() !== ""; });
  }
  function luuDongMoi(tr, sau) {
    if (!tr || !tr.classList.contains("dong-moi") || tr.dataset.dangLuu === "1") return;
    if (!coGiGo(tr)) return;
    tr.dataset.dangLuu = "1";
    tr.dataset.sauKhiLuu = sau || "";
    tr.dispatchEvent(new CustomEvent("luu-dong", { bubbles: true }));
  }
  function xoaDongMoi(tr) {
    Array.prototype.forEach.call(tr.querySelectorAll("input"), function (i) { i.value = ""; });
    tr.classList.remove("dong-moi-loi");
    var loi = tr.querySelector(".o-loi-chu");
    if (loi) loi.remove();
  }
  // Rời khỏi dòng trống (con trỏ sang chỗ khác) thì lưu
  document.addEventListener("focusout", function (e) {
    var tr = e.target.closest && e.target.closest("tr.dong-moi");
    if (!tr || !LUOI.contains(tr)) return;
    var toi = e.relatedTarget;
    if (toi && tr.contains(toi)) return;
    setTimeout(function () {
      if (tr.contains(document.activeElement)) return;
      luuDongMoi(tr, "");
    }, 60);
  });
  // Sau khi dòng trống thành dòng thật: HTMX trả `<tr>` thật + `<tr>` trống mới;
  // đưa con trỏ vào ô đầu của dòng trống mới nếu vừa nhấn Enter
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (!t || t.tagName !== "TR") return;
    var yeu_cau = e.detail.requestConfig && e.detail.requestConfig.elt;
    var sau = yeu_cau && yeu_cau.dataset ? yeu_cau.dataset.sauKhiLuu : "";
    if (t.classList.contains("dong-moi")) {
      delete t.dataset.dangLuu;                    // dòng bị từ chối: giữ lại để sửa
      var o_loi = t.querySelector("td.o-loi input") || t.querySelector("input");
      if (o_loi) o_loi.focus();
      return;
    }
    var trong = t.nextElementSibling;
    if (sau === "xuong" && trong && trong.classList.contains("dong-moi")) {
      var dau = trong.querySelector("input");
      if (dau) dau.focus();
    }
  });

  // ── Thanh công cụ ──
  document.addEventListener("click", function (e) {
    var nut = e.target.closest && e.target.closest(".bt-them-dong, .bt-loc-o, .bt-an-cot, .bt-thu-ben");
    if (!nut) return;
    if (nut.classList.contains("bt-them-dong")) {
      var o = LUOI.querySelector("tr.dong-moi input");
      if (o) { o.focus(); o.scrollIntoView({ block: "nearest" }); }
      return;
    }
    if (nut.classList.contains("bt-loc-o")) {
      var td = document.activeElement && document.activeElement.closest && document.activeElement.closest("td[data-cot]");
      if (!td || !LUOI.contains(td) || td.classList.contains("o-moi")) return;
      var gia_tri = (td.textContent || "").replace(/⌕\s*$/, "").trim();
      var tham_so = new URLSearchParams(location.search);
      tham_so.delete("trang");
      tham_so.set("f_" + td.dataset.cot, gia_tri);
      location.search = tham_so.toString();
      return;
    }
    if (nut.classList.contains("bt-thu-ben")) {
      if (!BO_CUC) return;
      var thu = BO_CUC.classList.toggle("thu-gon");
      nut.textContent = thu ? "›" : "‹";
      nho("knjsc-bt-ben", thu ? "1" : null);
      return;
    }
    if (nut.classList.contains("bt-an-cot")) {
      var mo = HOP_AN_COT.hidden;
      if (mo) veHopAnCot(nut);
      HOP_AN_COT.hidden = !mo;
      nut.setAttribute("aria-expanded", mo ? "true" : "false");
    }
  });
  if (BO_CUC && doc("knjsc-bt-ben") === "1") {
    BO_CUC.classList.add("thu-gon");
    var nut_ben = BO_CUC.querySelector(".bt-thu-ben");
    if (nut_ben) nut_ben.textContent = "›";
  }

  // "Tất cả" trong thanh bên: chọn hoặc bỏ chọn cả khối
  document.addEventListener("change", function (e) {
    if (!e.target.classList || !e.target.classList.contains("bt-tat-ca")) return;
    var form = e.target.closest("form");
    Array.prototype.forEach.call(form.querySelectorAll("input[type=checkbox]:not(.bt-tat-ca)"), function (o) {
      o.checked = e.target.checked;
    });
  });

  // ── Ẩn/hiện cột, nhớ theo bảng ──
  var KHOA_AN_COT = "knjsc-bt-an-cot-" + MA_BANG;
  function cotAn() {
    try { return JSON.parse(doc(KHOA_AN_COT) || "[]"); } catch (e) { return []; }
  }
  function apAnCot() {
    var an = cotAn();
    var hang = LUOI.querySelector("thead tr");
    if (!hang) return;
    Array.prototype.forEach.call(hang.children, function (th, i) {
      var ma = th.dataset.cot;
      if (!ma) return;
      var gia_tri = an.indexOf(ma) >= 0;
      Array.prototype.forEach.call(LUOI.querySelectorAll("tr > *:nth-child(" + (i + 1) + ")"), function (o) { o.hidden = gia_tri; });
    });
    canhCotCoDinh();
  }
  function veHopAnCot(nut) {
    var an = cotAn();
    HOP_AN_COT.innerHTML = "";
    Array.prototype.forEach.call(LUOI.querySelectorAll("thead th[data-cot]"), function (th) {
      var nhan = document.createElement("label");
      nhan.className = "bt-an-cot-muc";
      var o = document.createElement("input");
      o.type = "checkbox";
      o.checked = an.indexOf(th.dataset.cot) < 0;
      o.dataset.cot = th.dataset.cot;
      o.addEventListener("change", function () {
        var moi = cotAn().filter(function (m) { return m !== th.dataset.cot; });
        if (!o.checked) moi.push(th.dataset.cot);
        nho(KHOA_AN_COT, JSON.stringify(moi));
        apAnCot();
      });
      nhan.appendChild(o);
      nhan.appendChild(document.createTextNode(" " + (th.querySelector("a") ? th.querySelector("a").textContent.replace(/[↑↓↕]\s*$/, "").trim() : th.dataset.cot)));
      HOP_AN_COT.appendChild(nhan);
    });
    var r = nut.getBoundingClientRect();
    HOP_AN_COT.style.top = (window.scrollY + r.bottom + 4) + "px";
    HOP_AN_COT.style.left = (window.scrollX + r.left) + "px";
  }
  apAnCot();
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (t && t.tagName === "TR") apAnCot();
  });
  document.addEventListener("click", function (e) {
    if (!HOP_AN_COT || HOP_AN_COT.hidden) return;
    if (HOP_AN_COT.contains(e.target) || e.target.closest(".bt-an-cot")) return;
    HOP_AN_COT.hidden = true;
    var nut = document.querySelector(".bt-an-cot");
    if (nut) nut.setAttribute("aria-expanded", "false");
  });

  // ── Hộp lọc một cột: đặt ngay dưới nút ▾ vừa bấm ──
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
