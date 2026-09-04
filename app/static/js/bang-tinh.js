/* Bảng tính — phần trang: bàn phím, sửa ô, dòng trống, thanh bên, ẩn cột, chữ
   cột, kéo độ rộng, kéo thứ tự, thanh công thức, +100 dòng, trạng thái lưu,
   thanh công cụ định dạng. Không có engine công thức (ADR-009): lưới là HTML
   thật, HTMX lo phần trao đổi với máy chủ. Dáng và thao tác theo bảng tính
   KN Demo (ADR-011); chọn vùng, clipboard, kéo điền, hoàn tác: bang-tinh-o.js.

   Phím trên ô:   mũi tên / Tab đi giữa các ô · Enter, F2 hoặc gõ chữ để sửa
                  · Home đầu dòng · PageUp/PageDown 20 dòng · Ctrl+Home ô đầu
   Trong ô sửa:   Enter lưu (textarea: Ctrl+Enter) · Esc huỷ · Tab lưu rồi sang
                  ô kế · rời ô mà đã đổi thì lưu
   Dòng trống:    gõ rồi rời khỏi dòng (hoặc Enter) là lưu
   Thanh công thức: ô địa chỉ gõ B7 + Enter để nhảy; ô giá trị Enter lưu rồi
                  xuống dòng, Tab sang phải, Esc trả lại
   Cột ẩn, độ rộng, thứ tự, thanh bên nhớ trong localStorage — không lên máy chủ. */
(function () {
  "use strict";
  var LUOI = document.getElementById("luoi-vd");
  var HOP = document.getElementById("hop-loc");
  var BO_CUC = document.getElementById("bt-bo-cuc");
  var HOP_AN_COT = document.getElementById("bt-an-cot-hop");
  if (!LUOI) return;
  var MA_BANG = LUOI.dataset.bang || "";
  var DONG_DAU = parseInt(LUOI.dataset.dongDau || "2", 10);
  var DIA_CHI = document.getElementById("bt-dia-chi");
  var CONG_THUC = document.getElementById("bt-cong-thuc");
  var TRANG_THAI = document.getElementById("bt-trang-thai");
  var SO_DONG_TRONG_MAX = 2000;

  function nho(khoa, gia_tri) {
    try { if (gia_tri === null) localStorage.removeItem(khoa); else localStorage.setItem(khoa, gia_tri); } catch (e) {}
  }
  function doc(khoa) { try { return localStorage.getItem(khoa); } catch (e) { return null; } }
  function moi(sel, ham) { Array.prototype.forEach.call(LUOI.querySelectorAll(sel), ham); }

  function baoLoi(tieu_de, chu) {
    var loi = document.getElementById("bt-loi");
    if (!loi) return;
    loi.innerHTML = "";
    if (!tieu_de) return;
    var hop = document.createElement("div");
    hop.className = "bao bao-xau";
    hop.innerHTML = '<span class="bao-ic">!</span><div><b></b><p></p></div>';
    hop.querySelector("b").textContent = tieu_de;
    hop.querySelector("p").textContent = chu || "";
    loi.appendChild(hop);
    clearTimeout(baoLoi.hen);
    baoLoi.hen = setTimeout(function () { loi.innerHTML = ""; }, 6000);
  }

  // Ô kế bên: dr dòng, dc cột (bỏ qua cột ẩn; cột số dòng không có tabindex nên
  // đi sang trái hết cột thì đứng lại). Trả về ô hoặc ô nhập của dòng trống.
  function oCanh(td, dr, dc) {
    var tr = td.parentElement;
    var cac = Array.prototype.slice.call(tr.children);
    var i = cac.indexOf(td);
    var hang = tr;
    while (dr > 0 && hang.nextElementSibling) { hang = hang.nextElementSibling; dr--; }
    while (dr < 0 && hang.previousElementSibling) { hang = hang.previousElementSibling; dr++; }
    var j = i;
    do { j += dc; } while (hang.children[j] && hang.children[j].hidden);
    if (dc === 0) j = i;
    var muc = hang.children[Math.max(0, Math.min(j, hang.children.length - 1))];
    if (!muc) return null;
    if (muc.classList.contains("o-moi")) return muc.querySelector("input:not([type=hidden])") || null;
    return muc.hasAttribute("tabindex") ? muc : null;
  }
  function oTrongDong(tr) { return tr.querySelector("td[tabindex], td.o-moi"); }
  function toiO(o) {
    if (!o) return;
    var muc = o.tagName === "INPUT" ? o : (o.classList.contains("o-moi") ? o.querySelector("input:not([type=hidden])") : o);
    if (!muc) return;
    muc.focus();
    muc.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function moSua(td) {
    if (!td.dataset.suaUrl) return;
    htmx.ajax("GET", td.dataset.suaUrl, { target: td, swap: "outerHTML" });
  }
  function huySua(td) {
    if (!td.dataset.hienUrl) return;
    htmx.ajax("GET", td.dataset.hienUrl, { target: td, swap: "outerHTML" });
  }
  // Gửi ô đang sửa lên máy chủ, mỗi ô một lần dù Enter và rời ô cùng xảy ra
  function guiSua(td) {
    if (td.dataset.dangLuu === "1") return;
    td.dataset.dangLuu = "1";
    var form = td.querySelector("form");
    if (form) form.requestSubmit();
  }

  var HUONG = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] };

  // ── Cột cố định: máy chủ ước lượng `left`, trình duyệt đo lại cho đúng ──
  function canhCotCoDinh() {
    var hang = LUOI.querySelector("thead tr.bt-hang-chu");
    if (!hang) return;
    var trai = 0;
    Array.prototype.forEach.call(hang.children, function (th, i) {
      if (!th.classList.contains("co-dinh") || th.hidden) return;
      var rong = th.getBoundingClientRect().width;
      moi("tr > *:nth-child(" + (i + 1) + ")", function (o) { o.style.left = trai + "px"; });
      trai += rong;
    });
  }
  window.addEventListener("resize", canhCotCoDinh);
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (t && (t.tagName === "TD" || t.tagName === "TR")) canhCotCoDinh();
  });

  // ── Số dòng như Excel: hàng tên cột là 1, dữ liệu của trang từ DONG_DAU ──
  function danhSoDong() {
    var i = 0;
    moi("tbody tr", function (tr) {
      if (tr.classList.contains("bt-dong-rong")) return;
      var so = DONG_DAU + i++;
      var th = tr.querySelector("th.bt-so-dong");
      if (th) th.textContent = so;
      if (tr.classList.contains("dong-moi")) {
        tr.dataset.stt = so;
        tr.id = "dong-moi-" + so;
        var an = tr.querySelector("input[name=_stt]");
        if (an) an.value = so;
      }
    });
  }

  // ── Bàn phím trên ô ──
  var GO_SAN = null;          // ký tự vừa gõ trên ô hiển thị: mở sửa rồi thay nội dung bằng nó
  document.addEventListener("keydown", function (e) {
    var td = e.target.closest && e.target.closest("td[tabindex], td.dang-sua, td.o-moi");
    if (!td || !LUOI.contains(td)) return;

    if (td.classList.contains("o-moi")) {
      if (e.key === "Enter") { e.preventDefault(); luuDongMoi(td.parentElement, "xuong"); return; }
      if (e.key === "Escape") { e.preventDefault(); xoaDongMoi(td.parentElement); return; }
      var hh = HUONG[e.key];
      if (hh && (hh[0] !== 0 || e.target.selectionStart === e.target.value.length || e.target.selectionStart === 0)) {
        var dich0 = oCanh(td, hh[0], hh[1]);
        if (dich0) { e.preventDefault(); toiO(dich0); }
      }
      return;
    }

    if (td.classList.contains("dang-sua")) {
      if (e.key === "Escape") { e.preventDefault(); huySua(td); return; }
      var la_textarea = e.target.tagName === "TEXTAREA";
      if (e.key === "Enter" && (!la_textarea || e.ctrlKey)) {
        e.preventDefault();
        td.dataset.sauKhiLuu = e.shiftKey ? "len" : "xuong";
        guiSua(td);
        return;
      }
      if (e.key === "Tab") {
        e.preventDefault();
        td.dataset.sauKhiLuu = e.shiftKey ? "trai" : "phai";
        guiSua(td);
      }
      return;
    }

    if (e.key === "Enter" || e.key === "F2") { e.preventDefault(); moSua(td); return; }
    if (e.key === "Home") {
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        var dong_dau = LUOI.querySelector("tbody tr:not(.bt-dong-rong)");
        toiO(dong_dau && oTrongDong(dong_dau));
      } else {
        toiO(oTrongDong(td.parentElement));
      }
      return;
    }
    if (e.key === "PageDown" || e.key === "PageUp") {
      e.preventDefault();
      toiO(oCanh(td, e.key === "PageDown" ? 20 : -20, 0));
      return;
    }
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && td.dataset.suaUrl) {
      e.preventDefault();
      GO_SAN = { dong: td.dataset.dong, cot: td.dataset.cot, chu: e.key };
      moSua(td);
      return;
    }
    var h = HUONG[e.key] || (e.key === "Tab" ? [0, e.shiftKey ? -1 : 1] : null);
    if (!h || e.shiftKey && e.key !== "Tab") return;       // Shift+mũi tên: chọn vùng (bang-tinh-o.js)
    var dich = oCanh(td, h[0], h[1]);
    if (dich) { e.preventDefault(); toiO(dich); }
  });

  // Sau khi máy chủ trả ô mới: đưa con trỏ vào ô sửa (kèm ký tự vừa gõ), hoặc
  // về ô vừa lưu / ô kế bên theo hướng đã nhấn
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var td = e.detail.target;
    if (!td || td.tagName !== "TD") return;
    if (td.classList.contains("dang-sua")) {
      var o = td.querySelector("select, textarea, input:not([type=hidden])");
      if (!o) return;
      o.focus();
      if (GO_SAN && GO_SAN.dong === td.dataset.dong && GO_SAN.cot === td.dataset.cot && o.tagName !== "SELECT" && o.type !== "date") {
        o.value = GO_SAN.chu;
        if (o.setSelectionRange) o.setSelectionRange(o.value.length, o.value.length);
      } else if (o.select && o.type !== "date") {
        o.select();
      }
      GO_SAN = null;
      return;
    }
    var dich = td;
    if (e.detail.requestConfig && e.detail.requestConfig.elt) {
      var cu = e.detail.requestConfig.elt.closest && e.detail.requestConfig.elt.closest("td");
      var huong = cu && cu.dataset.sauKhiLuu;
      if (huong === "phai") dich = oCanh(td, 0, 1) || td;
      else if (huong === "trai") dich = oCanh(td, 0, -1) || td;
      else if (huong === "xuong") dich = oCanh(td, 1, 0) || td;
      else if (huong === "len") dich = oCanh(td, -1, 0) || td;
    }
    toiO(dich);
  });
  // Rời ô đang sửa mà đã đổi thì lưu, không đổi thì đóng — như Excel và demo
  document.addEventListener("focusout", function (e) {
    var td = e.target.closest && e.target.closest("td.dang-sua");
    if (!td || !LUOI.contains(td)) return;
    var toi = e.relatedTarget;
    if (toi && td.contains(toi)) return;
    setTimeout(function () {
      if (!document.body.contains(td) || td.contains(document.activeElement)) return;
      var o = td.querySelector("select, textarea, input:not([type=hidden])");
      if (!o) return;
      if (o.value !== (td.dataset.goc || "")) guiSua(td); else huySua(td);
    }, 120);
  });

  // Ô sửa hỏng (400): giữ trình sửa kèm lý do, không thay bằng ô cũ.
  // Dòng trống hỏng (400) cũng vậy: giữ giá trị đã gõ, hiện lý do.
  document.body.addEventListener("htmx:beforeSwap", function (e) {
    if (e.detail.xhr && e.detail.xhr.status === 400) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });

  // ── Trạng thái lưu ở thanh trên: mọi POST của lưới ──
  function datTrangThai(chu, lop) {
    if (!TRANG_THAI) return;
    TRANG_THAI.textContent = chu;
    TRANG_THAI.className = "bt-trang-thai" + (lop ? " " + lop : "");
  }
  function gioPhut() {
    var d = new Date();
    return (d.getHours() < 10 ? "0" : "") + d.getHours() + ":" + (d.getMinutes() < 10 ? "0" : "") + d.getMinutes();
  }
  function laGhi(e) {
    var cfg = e.detail && e.detail.requestConfig;
    return !!(cfg && cfg.verb && String(cfg.verb).toLowerCase() === "post");
  }
  document.body.addEventListener("htmx:beforeRequest", function (e) { if (laGhi(e)) datTrangThai("Đang lưu…", "dang-luu"); });
  document.body.addEventListener("htmx:afterRequest", function (e) {
    if (!laGhi(e)) return;
    var xhr = e.detail.xhr;
    if (e.detail.successful) datTrangThai("✓ Đã lưu " + gioPhut(), "da-luu");
    else if (xhr && xhr.status === 400) datTrangThai("⚠ Chưa lưu được — xem lý do tại ô", "loi-luu");
    else datTrangThai("⚠ Lỗi lưu — thử lại", "loi-luu");
  });

  // ── Dòng trống cuối lưới ──
  function coGiGo(tr) {
    return Array.prototype.some.call(tr.querySelectorAll("input:not([type=hidden])"), function (i) { return i.value.trim() !== ""; });
  }
  function luuDongMoi(tr, sau) {
    if (!tr || !tr.classList.contains("dong-moi") || tr.dataset.dangLuu === "1") return;
    if (!coGiGo(tr)) return;
    tr.dataset.dangLuu = "1";
    tr.dataset.sauKhiLuu = sau || "";
    tr.dispatchEvent(new CustomEvent("luu-dong", { bubbles: true }));
  }
  function xoaDongMoi(tr) {
    Array.prototype.forEach.call(tr.querySelectorAll("input:not([type=hidden])"), function (i) { i.value = ""; });
    tr.classList.remove("dong-moi-loi");
    var loi = tr.querySelector(".o-loi-chu");
    if (loi) loi.remove();
  }
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
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (!t || t.tagName !== "TR") return;
    var yeu_cau = e.detail.requestConfig && e.detail.requestConfig.elt;
    var sau = yeu_cau && yeu_cau.dataset ? yeu_cau.dataset.sauKhiLuu : "";
    if (t.classList.contains("dong-moi")) {
      delete t.dataset.dangLuu;                    // dòng bị từ chối: giữ lại để sửa
      var o_loi = t.querySelector("td.o-loi input") || t.querySelector("input:not([type=hidden])");
      if (o_loi) o_loi.focus();
      return;
    }
    var trong = t.nextElementSibling;
    if (sau === "xuong" && trong && trong.classList.contains("dong-moi")) {
      var dau = trong.querySelector("input:not([type=hidden])");
      if (dau) dau.focus();
    }
  });
  // +100 dòng: nhân bản dòng trống cuối, cho tới trần
  function themDongTrong(n) {
    var cac = LUOI.querySelectorAll("tbody tr.dong-moi");
    var mau = cac[cac.length - 1];
    if (!mau) return;
    n = Math.min(n, SO_DONG_TRONG_MAX - cac.length);
    var cuoi = mau;
    for (var i = 0; i < n; i++) {
      var tr = mau.cloneNode(true);
      tr.classList.remove("dong-moi-loi");
      delete tr.dataset.dangLuu; delete tr.dataset.sauKhiLuu;
      Array.prototype.forEach.call(tr.querySelectorAll("input:not([type=hidden])"), function (o) { o.value = ""; });
      Array.prototype.forEach.call(tr.querySelectorAll(".o-loi-chu"), function (o) { o.remove(); });
      Array.prototype.forEach.call(tr.querySelectorAll("td.o-loi"), function (o) { o.classList.remove("o-loi"); });
      mau.parentElement.appendChild(tr);
      htmx.process(tr);
      cuoi = tr;
    }
    danhSoDong();
    if (n > 0) toiO(oTrongDong(cuoi));
  }

  // ── Thanh công cụ và các hộp nổi ──
  function dongHop(tru) {
    Array.prototype.forEach.call(document.querySelectorAll(".bt-bang-mau, .bt-khac-hop"), function (h) {
      if (h === tru) return;
      h.hidden = true;
      var nut = document.querySelector('[aria-controls="' + h.id + '"]');
      if (nut) nut.setAttribute("aria-expanded", "false");
    });
  }
  function datBen(mo) {
    if (!BO_CUC) return;
    BO_CUC.classList.toggle("thu-gon", !mo);
    nho("knjsc-bt-ben", mo ? "mo" : null);
    Array.prototype.forEach.call(document.querySelectorAll(".bt-cong-cu .bt-thu-ben"), function (n) {
      n.setAttribute("aria-pressed", mo ? "true" : "false");
    });
    canhCotCoDinh();
  }
  document.addEventListener("click", function (e) {
    var nut = e.target.closest && e.target.closest(".bt-them-dong, .bt-loc-o, .bt-an-cot, .bt-thu-ben, .bt-thu-muc-moi, .bt-them-100, .bt-khac, .bt-mo-mau, .bt-goc");
    if (!nut) return;
    if (nut.classList.contains("bt-thu-muc-moi")) {
      var form = document.getElementById("bt-form-thu-muc");
      if (!form) return;
      datBen(true);
      form.hidden = !form.hidden;
      Array.prototype.forEach.call(document.querySelectorAll(".bt-thu-muc-moi"), function (n) {
        n.setAttribute("aria-expanded", form.hidden ? "false" : "true");
      });
      if (!form.hidden) form.querySelector("input[name=name]").focus();
      return;
    }
    if (nut.classList.contains("bt-them-dong")) {
      var o = LUOI.querySelector("tr.dong-moi input:not([type=hidden])");
      if (o) toiO(o);
      return;
    }
    if (nut.classList.contains("bt-them-100")) { themDongTrong(100); return; }
    if (nut.classList.contains("bt-goc")) {
      var dong_dau = LUOI.querySelector("tbody tr:not(.bt-dong-rong)");
      toiO(dong_dau && oTrongDong(dong_dau));
      LUOI.dispatchEvent(new CustomEvent("bt-chon-tat-ca"));
      return;
    }
    if (nut.classList.contains("bt-loc-o")) {
      var td = O_HIEN;
      if (!td || !LUOI.contains(td) || !td.dataset.cot || td.classList.contains("o-moi")) {
        baoLoi("Chưa chọn ô nào", "Bấm vào một ô có giá trị rồi mới lọc theo ô đó.");
        return;
      }
      var tham_so = new URLSearchParams(location.search);
      tham_so.delete("trang");
      tham_so.set("f_" + td.dataset.cot, td.dataset.goc || "");
      location.search = tham_so.toString();
      return;
    }
    if (nut.classList.contains("bt-thu-ben")) { datBen(!!(BO_CUC && BO_CUC.classList.contains("thu-gon"))); return; }
    if (nut.classList.contains("bt-an-cot")) {
      var mo = HOP_AN_COT.hidden;
      if (mo) veHopAnCot(nut);
      HOP_AN_COT.hidden = !mo;
      nut.setAttribute("aria-expanded", mo ? "true" : "false");
      return;
    }
    if (nut.classList.contains("bt-khac") || nut.classList.contains("bt-mo-mau")) {
      var hop = document.getElementById(nut.getAttribute("aria-controls"));
      if (!hop) return;
      var mo2 = hop.hidden;
      dongHop(hop);
      hop.hidden = !mo2;
      nut.setAttribute("aria-expanded", mo2 ? "true" : "false");
    }
  });
  datBen(doc("knjsc-bt-ben") === "mo");
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(".bt-mau-hop")) return;
    dongHop(null);
  });

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
    moi("thead tr.bt-hang-chu th[data-cot]", function (th) {
      var gia_tri = an.indexOf(th.dataset.cot) >= 0;
      moi('[data-cot="' + th.dataset.cot + '"]', function (o) { o.hidden = gia_tri; });
    });
    canhCotCoDinh();
  }
  function tenCot(ma) {
    var th = LUOI.querySelector('thead tr.bt-hang-ten th[data-cot="' + ma + '"]');
    var a = th && th.querySelector(".bt-sap");
    return a ? a.textContent.replace(/[↑↓↕]\s*$/, "").trim() : ma;
  }
  function veHopAnCot(nut) {
    var an = cotAn();
    HOP_AN_COT.innerHTML = "";
    moi("thead tr.bt-hang-chu th[data-cot]", function (th) {
      var nhan = document.createElement("label");
      nhan.className = "bt-an-cot-muc";
      var o = document.createElement("input");
      o.type = "checkbox";
      o.checked = an.indexOf(th.dataset.cot) < 0;
      o.dataset.cot = th.dataset.cot;
      o.addEventListener("change", function () {
        var moi_ = cotAn().filter(function (m) { return m !== th.dataset.cot; });
        if (!o.checked) moi_.push(th.dataset.cot);
        nho(KHOA_AN_COT, JSON.stringify(moi_));
        apAnCot();
        danhChuCot();
      });
      nhan.appendChild(o);
      nhan.appendChild(document.createTextNode(" " + tenCot(th.dataset.cot)));
      HOP_AN_COT.appendChild(nhan);
    });
    var r = nut.getBoundingClientRect();
    HOP_AN_COT.style.top = (window.scrollY + r.bottom + 4) + "px";
    HOP_AN_COT.style.left = Math.max(8, Math.min(window.scrollX + r.left, window.innerWidth - 240)) + "px";
  }

  // ── Chữ cột A B C, kéo đổi độ rộng, kéo thả đổi thứ tự — nhớ theo bảng ──
  var KHOA_RONG = "knjsc-bt-rong-" + MA_BANG;
  var KHOA_THU_TU = "knjsc-bt-thu-tu-" + MA_BANG;
  var SO_CO_DINH = parseInt(LUOI.dataset.coDinh || "0", 10);
  function docJSON(khoa, mac_dinh) {
    try { return JSON.parse(doc(khoa)) || mac_dinh; } catch (e) { return mac_dinh; }
  }
  function chuCot(i) {
    var chu = "";
    i += 1;
    while (i > 0) { var du = (i - 1) % 26; chu = String.fromCharCode(65 + du) + chu; i = Math.floor((i - 1) / 26); }
    return chu;
  }
  function danhChuCot() {
    var i = 0;
    moi("thead tr.bt-hang-chu th", function (th) {
      var o = th.querySelector(".bt-chu-cot");
      if (!o || th.hidden) return;
      o.textContent = chuCot(i++);
    });
  }
  function datRong(ma, px) {
    moi('[data-cot="' + ma + '"]', function (o) {
      o.style.width = px + "px"; o.style.minWidth = px + "px"; o.style.maxWidth = px + "px";
    });
  }
  function apRong() {
    var r = docJSON(KHOA_RONG, {});
    Object.keys(r).forEach(function (ma) { datRong(ma, r[ma]); });
  }
  function thuTuHienTai() {
    return Array.prototype.map.call(LUOI.querySelectorAll("thead tr.bt-hang-chu th[data-cot]"), function (th) { return th.dataset.cot; });
  }
  function apThuTu() {
    var luu = docJSON(KHOA_THU_TU, null);
    if (!luu || !luu.length) return;
    var hien = thuTuHienTai();
    var thu_tu = luu.filter(function (m) { return hien.indexOf(m) >= 0; })
      .concat(hien.filter(function (m) { return luu.indexOf(m) < 0; }));
    // Cột cố định luôn đứng đầu, đúng thứ tự gốc; cột trống luôn ở cuối
    var co_dinh = hien.slice(0, SO_CO_DINH);
    thu_tu = co_dinh.concat(thu_tu.filter(function (m) { return co_dinh.indexOf(m) < 0; }));
    moi("tr", function (tr) {
      var theo_ma = {}, trong = [];
      Array.prototype.forEach.call(tr.children, function (o) {
        if (o.dataset.cot) theo_ma[o.dataset.cot] = o;
        else if (o.dataset.trong) trong.push(o);
      });
      if (!Object.keys(theo_ma).length) return;          // dòng "không có dòng nào"
      thu_tu.forEach(function (ma) { if (theo_ma[ma]) tr.appendChild(theo_ma[ma]); });
      trong.forEach(function (o) { tr.appendChild(o); });
    });
  }
  function apBoCuc() {
    apThuTu();
    apRong();
    apAnCot();          // gọi luôn canhCotCoDinh()
    danhChuCot();
    danhSoDong();
  }
  apBoCuc();
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (t && t.tagName === "TR") apBoCuc();
  });

  // Kéo mép phải chữ cột để đổi độ rộng (tối thiểu 36px như demo)
  var KEO_RONG = null;
  document.addEventListener("mousedown", function (e) {
    var tay = e.target.closest && e.target.closest(".bt-keo-cot");
    if (!tay || !LUOI.contains(tay)) return;
    var th = tay.closest("th");
    e.preventDefault();
    KEO_RONG = { ma: th.dataset.cot, x: e.clientX, rong: th.getBoundingClientRect().width, th: th };
    th.classList.add("bt-dang-keo-rong");
    document.body.style.cursor = "col-resize";
  });
  document.addEventListener("mousemove", function (e) {
    if (!KEO_RONG) return;
    var moi_ = Math.max(36, Math.round(KEO_RONG.rong + e.clientX - KEO_RONG.x));
    datRong(KEO_RONG.ma, moi_);
    KEO_RONG.moi = moi_;
  });
  document.addEventListener("mouseup", function () {
    if (!KEO_RONG) return;
    if (KEO_RONG.moi) {
      var r = docJSON(KHOA_RONG, {});
      r[KEO_RONG.ma] = KEO_RONG.moi;
      nho(KHOA_RONG, JSON.stringify(r));
      canhCotCoDinh();
    }
    KEO_RONG.th.classList.remove("bt-dang-keo-rong");
    document.body.style.cursor = "";
    KEO_RONG = null;
  });

  // Kéo thả tên cột để đổi thứ tự (cột cố định đứng yên)
  var KEO_COT = null;
  moi("thead th[data-cot]", function (th) {
    if (!th.classList.contains("co-dinh")) th.setAttribute("draggable", "true");
  });
  LUOI.addEventListener("dragstart", function (e) {
    var th = e.target.closest && e.target.closest("thead th[data-cot]");
    if (!th || KEO_RONG) { e.preventDefault(); return; }
    KEO_COT = th.dataset.cot;
    th.classList.add("bt-dang-keo");
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", KEO_COT); } catch (err) {}
  });
  function xoaDauTha() {
    moi("th.bt-tha-truoc, th.bt-tha-sau", function (o) { o.classList.remove("bt-tha-truoc", "bt-tha-sau"); });
  }
  LUOI.addEventListener("dragover", function (e) {
    if (!KEO_COT) return;
    var th = e.target.closest && e.target.closest("thead th[data-cot]");
    if (!th || th.classList.contains("co-dinh")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    var r = th.getBoundingClientRect();
    xoaDauTha();
    th.classList.add(e.clientX < r.left + r.width / 2 ? "bt-tha-truoc" : "bt-tha-sau");
  });
  LUOI.addEventListener("dragleave", function (e) {
    var th = e.target.closest && e.target.closest("thead th[data-cot]");
    if (th) th.classList.remove("bt-tha-truoc", "bt-tha-sau");
  });
  LUOI.addEventListener("drop", function (e) {
    if (!KEO_COT) return;
    var th = e.target.closest && e.target.closest("thead th[data-cot]");
    if (!th || th.classList.contains("co-dinh") || th.dataset.cot === KEO_COT) { xoaDauTha(); return; }
    e.preventDefault();
    var truoc = th.classList.contains("bt-tha-truoc");
    var thu_tu = thuTuHienTai().filter(function (m) { return m !== KEO_COT; });
    var i = thu_tu.indexOf(th.dataset.cot) + (truoc ? 0 : 1);
    thu_tu.splice(Math.max(i, SO_CO_DINH), 0, KEO_COT);
    nho(KHOA_THU_TU, JSON.stringify(thu_tu));
    xoaDauTha();
    apBoCuc();
  });
  LUOI.addEventListener("dragend", function () {
    moi("th.bt-dang-keo", function (o) { o.classList.remove("bt-dang-keo"); });
    xoaDauTha();
    KEO_COT = null;
  });

  // Đặt lại độ rộng, thứ tự, cột ẩn
  document.addEventListener("click", function (e) {
    var nut = e.target.closest && e.target.closest(".bt-dat-lai-cot");
    if (!nut) return;
    nho(KHOA_RONG, null); nho(KHOA_THU_TU, null); nho(KHOA_AN_COT, null);
    location.reload();
  });
  document.addEventListener("click", function (e) {
    if (!HOP_AN_COT || HOP_AN_COT.hidden) return;
    if (HOP_AN_COT.contains(e.target) || e.target.closest(".bt-an-cot")) return;
    HOP_AN_COT.hidden = true;
    var nut = document.querySelector(".bt-an-cot");
    if (nut) nut.setAttribute("aria-expanded", "false");
  });

  // ── Ô hiện tại: thanh công thức, tô số dòng và chữ cột, đồng bộ thanh công cụ ──
  var O_HIEN = null;
  function chiSoCot(td) { return Array.prototype.indexOf.call(td.parentElement.children, td); }
  function chuCotCua(td) {
    var hang = LUOI.querySelector("thead tr.bt-hang-chu");
    var th = hang && hang.children[chiSoCot(td)];
    var chu = th && th.querySelector(".bt-chu-cot");
    return chu ? chu.textContent : "";
  }
  function soDongCua(td) {
    var th = td.parentElement.querySelector("th.bt-so-dong");
    return th ? th.textContent : "";
  }
  function diaChi(td) { return chuCotCua(td) + soDongCua(td); }
  function toHang(td) {
    moi(".hl", function (o) { o.classList.remove("hl"); });
    if (!td) return;
    var so = td.parentElement.querySelector("th.bt-so-dong");
    if (so) so.classList.add("hl");
    var hang = LUOI.querySelector("thead tr.bt-hang-chu");
    var th = hang && hang.children[chiSoCot(td)];
    if (th) th.classList.add("hl");
  }
  function giaTriCua(td) {
    if (td.classList.contains("o-moi")) {
      var o = td.querySelector("input:not([type=hidden])");
      return o ? o.value : "";
    }
    return td.dataset.goc || "";
  }
  function capNhatThanhCT(td) {
    if (!DIA_CHI || !CONG_THUC) return;
    if (!td) { CONG_THUC.value = ""; return; }
    DIA_CHI.value = diaChi(td);
    CONG_THUC.value = giaTriCua(td);
    var sua_duoc = !!td.dataset.suaUrl || td.classList.contains("o-moi");
    CONG_THUC.disabled = !sua_duoc;
    CONG_THUC.title = sua_duoc ? "" : "Ô này không sửa được ở đây";
  }
  var LOP_DD = { b: "dd-dam", i: "dd-nghieng", u: "dd-gach-chan", st: "dd-gach-ngang", wr: "dd-xuong-dong", bd: "dd-vien" };
  var LOP_CAN = { l: "dd-can-trai", c: "dd-can-giua", r: "dd-can-phai" };
  var MA_DINH = { "so": "num", "phan-tram": "pct", "usd": "usd", "vnd": "vnd", "chu": "text" };
  function dongBoCongCu(td) {
    var co = td && td.dataset.cot ? td : null;
    Array.prototype.forEach.call(document.querySelectorAll(".bt-cong-cu .bt-dd[data-bat]"), function (nut) {
      nut.classList.toggle("on", !!co && co.classList.contains(LOP_DD[nut.dataset.dd]));
    });
    Array.prototype.forEach.call(document.querySelectorAll('.bt-cong-cu .bt-dd[data-dd="al"]'), function (nut) {
      nut.classList.toggle("on", !!co && co.classList.contains(LOP_CAN[nut.dataset.giaTri]));
    });
    var fs = document.querySelector('.bt-cong-cu select[data-dd="fs"]');
    if (fs) { var m = co && /\bdd-co-(\d+)\b/.exec(co.className); fs.value = m ? m[1] : ""; }
    var fmt = document.querySelector('.bt-cong-cu select[data-dd="fmt"]');
    if (fmt) { var m2 = co && /\bdd-dinh-([a-z-]+)\b/.exec(co.className); fmt.value = m2 ? (MA_DINH[m2[1]] || "") : ""; }
  }
  LUOI.addEventListener("focusin", function (e) {
    var td = e.target.closest && e.target.closest("td");
    if (!td || td.classList.contains("dang-sua")) return;
    O_HIEN = td;
    capNhatThanhCT(td);
    toHang(td);
    dongBoCongCu(td);
  });
  // Dòng trống: gõ vào ô nhập thì ô giá trị trên thanh công thức chạy theo
  LUOI.addEventListener("input", function (e) {
    if (!CONG_THUC || !O_HIEN || !e.target.classList || !e.target.classList.contains("o-moi-nhap")) return;
    if (O_HIEN.contains(e.target)) CONG_THUC.value = e.target.value;
  });
  // Ô địa chỉ: gõ B7 (hoặc B2:D9) + Enter để nhảy tới
  function oTai(chu, so) {
    var hang = LUOI.querySelector("thead tr.bt-hang-chu");
    if (!hang) return null;
    var i = -1;
    Array.prototype.some.call(hang.children, function (th, k) {
      var c = th.querySelector(".bt-chu-cot");
      if (c && !th.hidden && c.textContent === chu) { i = k; return true; }
      return false;
    });
    if (i < 0) return null;
    var dong = Array.prototype.filter.call(LUOI.querySelectorAll("tbody tr"), function (tr) { return !tr.classList.contains("bt-dong-rong"); });
    var tr = dong[so - DONG_DAU];
    if (!tr || !tr.children[i]) return null;
    var o = tr.children[i];
    return (o.hasAttribute("tabindex") || o.classList.contains("o-moi")) ? o : null;
  }
  if (DIA_CHI) {
    DIA_CHI.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { if (O_HIEN) capNhatThanhCT(O_HIEN); DIA_CHI.blur(); return; }
      if (e.key !== "Enter") return;
      e.preventDefault();
      var m = /^\s*([A-Za-z]{1,3})(\d+)\s*(?::([A-Za-z]{1,3})(\d+))?\s*$/.exec(DIA_CHI.value);
      var a = m && oTai(m[1].toUpperCase(), parseInt(m[2], 10));
      if (!a) { if (O_HIEN) capNhatThanhCT(O_HIEN); return; }
      toiO(a);
      if (m[3]) {
        var b = oTai(m[3].toUpperCase(), parseInt(m[4], 10));
        if (b) LUOI.dispatchEvent(new CustomEvent("bt-chon-vung", { detail: { a: a, b: b } }));
      }
    });
    DIA_CHI.addEventListener("focus", function () { DIA_CHI.select(); });
  }
  // Ô giá trị: Enter lưu rồi xuống dòng, Tab sang phải, Esc trả lại
  if (CONG_THUC) {
    var CT_O = null;
    CONG_THUC.addEventListener("focus", function () { CT_O = O_HIEN; });
    CONG_THUC.addEventListener("keydown", function (e) {
      var td = CT_O || O_HIEN;
      if (e.key === "Escape") { e.preventDefault(); if (td) { capNhatThanhCT(td); toiO(td); } return; }
      if (e.key !== "Enter" && e.key !== "Tab") return;
      e.preventDefault();
      if (!td || !LUOI.contains(td)) return;
      var gia_tri = CONG_THUC.value;
      if (/^\s*=/.test(gia_tri)) {
        baoLoi("Chưa hỗ trợ công thức gõ tay", "Cột tính sẵn (cộng, trừ, nhân, chia, phần trăm) đặt ở Sửa cột — kế hoạch công thức theo tên cột ghi ở backlog.");
        return;
      }
      var sau = e.key === "Tab" ? (e.shiftKey ? "trai" : "phai") : "xuong";
      if (td.classList.contains("o-moi")) {
        var o = td.querySelector("input:not([type=hidden])");
        if (o) { o.value = gia_tri; toiO(o); }
        return;
      }
      if (!td.dataset.suaUrl) return;
      if (gia_tri === (td.dataset.goc || "")) {
        toiO(oCanh(td, sau === "xuong" ? 1 : 0, sau === "phai" ? 1 : (sau === "trai" ? -1 : 0)) || td);
        return;
      }
      td.dataset.sauKhiLuu = sau;
      htmx.ajax("POST", td.dataset.suaUrl, { source: td, target: td, swap: "outerHTML", values: { gia_tri: gia_tri } });
    });
  }

  // ── Chọn ô và định dạng ──
  // Ô "đang chọn": các ô mang .o-chon (Shift+bấm chọn vùng, Ctrl+bấm thêm từng
  // ô; bang-tinh-o.js thêm kéo chuột), không có thì là ô hiện tại. Nút trên
  // thanh công cụ lấy con trỏ khi bấm, nên phải nhớ ô cuối cùng bằng tay.
  var O_CUOI = null;
  var O_NEO = null;
  var CHON_SAU_SWAP = [];
  var NHOM_DD = document.querySelector(".bt-dinh-dang");

  function oDuLieu(el) {
    var td = el && el.closest && el.closest("td[data-dong][data-cot]");
    return td && LUOI.contains(td) && !td.classList.contains("o-moi") ? td : null;
  }
  function boChon() {
    CHON_SAU_SWAP = [];                          // bỏ chọn rồi thì ô vẽ lại không được chọn lại
    moi("td.o-chon", function (o) { o.classList.remove("o-chon", "o-chon-t", "o-chon-b", "o-chon-l", "o-chon-r"); });
  }
  function chonVung(a, b) {
    var ha = a.parentElement, hb = b.parentElement;
    var hang = Array.prototype.slice.call(LUOI.querySelectorAll("tbody tr[data-dong]"));
    var ia = hang.indexOf(ha), ib = hang.indexOf(hb);
    var ca = Array.prototype.indexOf.call(ha.children, a), cb = Array.prototype.indexOf.call(hb.children, b);
    if (ia < 0 || ib < 0) return;
    var r1 = Math.min(ia, ib), r2 = Math.max(ia, ib), c1 = Math.min(ca, cb), c2 = Math.max(ca, cb);
    boChon();
    for (var r = r1; r <= r2; r++) {
      for (var c = c1; c <= c2; c++) {
        var o = hang[r].children[c];
        if (!o || !o.dataset.cot || o.hidden) continue;
        o.classList.add("o-chon");
        if (r === r1) o.classList.add("o-chon-t");
        if (r === r2) o.classList.add("o-chon-b");
        if (c === c1) o.classList.add("o-chon-l");
        if (c === c2) o.classList.add("o-chon-r");
      }
    }
  }
  function cacODangChon() {
    var chon = Array.prototype.slice.call(LUOI.querySelectorAll("td.o-chon"));
    if (chon.length) return chon;
    return O_CUOI && LUOI.contains(O_CUOI) ? [O_CUOI] : [];
  }
  LUOI.addEventListener("focusin", function (e) {
    var td = oDuLieu(e.target);
    if (td) O_CUOI = td;
  });
  LUOI.addEventListener("mousedown", function (e) {
    var td = oDuLieu(e.target);
    if (!td) return;
    if (e.shiftKey && O_NEO) { e.preventDefault(); chonVung(O_NEO, td); O_CUOI = td; return; }
    if (e.ctrlKey || e.metaKey) { e.preventDefault(); td.classList.toggle("o-chon"); O_NEO = td; O_CUOI = td; return; }
    boChon();
    O_NEO = td;
    O_CUOI = td;
  });
  LUOI.addEventListener("bt-chon-vung", function (e) {
    var a = oDuLieu(e.detail && e.detail.a), b = oDuLieu(e.detail && e.detail.b);
    if (a && b) { chonVung(a, b); O_NEO = a; O_CUOI = b; if (DIA_CHI) DIA_CHI.value = diaChi(a) + ":" + diaChi(b); }
  });
  function coLop(cac, lop) {
    return cac.length > 0 && cac.every(function (o) { return o.classList.contains(lop); });
  }
  function batTat(khoa) {
    var dd = {};
    dd[khoa] = coLop(cacODangChon(), LOP_DD[khoa]) ? "" : "1";
    guiDinhDang(dd);
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && LUOI.querySelector("td.o-chon")) boChon();
    if (!(e.ctrlKey || e.metaKey) || !NHOM_DD) return;
    var khoa = { b: "b", i: "i", u: "u" }[e.key.toLowerCase()];
    if (!khoa || e.shiftKey || e.altKey) return;
    var td = oDuLieu(e.target);
    if (td) { e.preventDefault(); batTat(khoa); }
  });
  function guiDinhDang(dd) {
    if (!NHOM_DD) return;
    var cac = cacODangChon();
    if (!cac.length) {
      baoLoi("Chưa chọn ô nào", "Bấm vào một ô, kéo hoặc Shift+bấm để chọn vùng, rồi mới định dạng.");
      return;
    }
    baoLoi("");
    CHON_SAU_SWAP = cac.map(function (o) { return o.id; });
    var gia_tri = Object.assign({ o: cac.map(function (o) { return o.dataset.dong + ":" + o.dataset.cot; }) }, dd);
    htmx.ajax("POST", NHOM_DD.dataset.url, { source: NHOM_DD, values: gia_tri, swap: "none", target: LUOI })
      .then(function () { setTimeout(chonLai, 30); });
  }
  // Ô được vẽ lại (oob) là phần tử mới, mất .o-chon — đánh dấu lại theo id
  function chonLai() {
    if (!CHON_SAU_SWAP.length) return;
    CHON_SAU_SWAP.forEach(function (id) {
      var o = document.getElementById(id);
      if (o && CHON_SAU_SWAP.length > 1) o.classList.add("o-chon");
    });
    O_CUOI = document.getElementById(CHON_SAU_SWAP[CHON_SAU_SWAP.length - 1]) || O_CUOI;
    if (O_CUOI) { O_HIEN = O_CUOI; dongBoCongCu(O_CUOI); }
  }
  document.body.addEventListener("htmx:afterSettle", function (e) {
    var cfg = e.detail && e.detail.requestConfig;
    if (cfg && cfg.elt === NHOM_DD) chonLai();
  });
  document.body.addEventListener("htmx:oobAfterSwap", function (e) {
    var t = e.detail && e.detail.target;
    if (t && t.id && CHON_SAU_SWAP.length > 1 && CHON_SAU_SWAP.indexOf(t.id) >= 0) {
      var moi_ = document.getElementById(t.id);
      if (moi_) moi_.classList.add("o-chon");
    }
  });
  document.addEventListener("click", function (e) {
    var nut = e.target.closest && e.target.closest(".bt-dd");
    if (!nut || nut.tagName === "SELECT") return;
    var loai = nut.dataset.dd;
    dongHop(null);
    if (loai === "xoa") { guiDinhDang({ xoa: "1" }); return; }
    if (nut.dataset.bat) { batTat(loai); return; }
    var dd = {};
    dd[loai] = nut.dataset.giaTri || "";
    guiDinhDang(dd);
    var sw = document.querySelector(loai === "c" ? ".bt-swbar-chu" : (loai === "bg" ? ".bt-swbar-nen" : "#khong-co"));
    if (sw && nut.classList.contains("bt-mau")) sw.style.background = nut.title || "";
  });
  document.addEventListener("change", function (e) {
    var chon = e.target.closest && e.target.closest("select.bt-dd");
    if (!chon) return;
    var dd = {};
    dd[chon.dataset.dd] = chon.value;
    guiDinhDang(dd);
  });

  // ── Hộp lọc một cột: đặt ngay dưới nút ▼ vừa bấm ──
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
    if (dau && nut && !nut.classList.contains("o-nhap")) dau.focus();
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
