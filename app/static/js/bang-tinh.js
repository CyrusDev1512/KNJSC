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
    var nut = e.target.closest && e.target.closest(".bt-them-dong, .bt-loc-o, .bt-an-cot, .bt-thu-ben, .bt-thu-muc-moi");
    if (!nut) return;
    if (nut.classList.contains("bt-thu-muc-moi")) {
      var form = document.getElementById("bt-form-thu-muc");
      if (!form) return;
      if (BO_CUC && BO_CUC.classList.contains("thu-gon")) {
        BO_CUC.classList.remove("thu-gon");
        nho("knjsc-bt-ben", null);
      }
      form.hidden = !form.hidden;
      Array.prototype.forEach.call(document.querySelectorAll(".bt-thu-muc-moi"), function (n) {
        n.setAttribute("aria-expanded", form.hidden ? "false" : "true");
      });
      if (!form.hidden) form.querySelector("input[name=name]").focus();
      return;
    }
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
        danhChuCot();
      });
      nhan.appendChild(o);
      nhan.appendChild(document.createTextNode(" " + (th.querySelector("a") ? th.querySelector("a").textContent.replace(/[↑↓↕]\s*$/, "").trim() : th.dataset.cot)));
      HOP_AN_COT.appendChild(nhan);
    });
    var r = nut.getBoundingClientRect();
    HOP_AN_COT.style.top = (window.scrollY + r.bottom + 4) + "px";
    HOP_AN_COT.style.left = (window.scrollX + r.left) + "px";
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
    Array.prototype.forEach.call(LUOI.querySelectorAll("thead th[data-cot]"), function (th) {
      var o = th.querySelector(".bt-chu-cot");
      if (!o) return;
      if (th.hidden) return;
      o.textContent = chuCot(i++);
    });
  }
  function datRong(ma, px) {
    Array.prototype.forEach.call(LUOI.querySelectorAll('[data-cot="' + ma + '"]'), function (o) {
      o.style.width = px + "px"; o.style.minWidth = px + "px"; o.style.maxWidth = px + "px";
    });
  }
  function apRong() {
    var r = docJSON(KHOA_RONG, {});
    Object.keys(r).forEach(function (ma) { datRong(ma, r[ma]); });
  }
  function thuTuHienTai() {
    return Array.prototype.map.call(LUOI.querySelectorAll("thead th[data-cot]"), function (th) { return th.dataset.cot; });
  }
  function apThuTu() {
    var luu = docJSON(KHOA_THU_TU, null);
    if (!luu || !luu.length) return;
    var hien = thuTuHienTai();
    var thu_tu = luu.filter(function (m) { return hien.indexOf(m) >= 0; })
      .concat(hien.filter(function (m) { return luu.indexOf(m) < 0; }));
    // Cột cố định luôn đứng đầu, đúng thứ tự gốc
    var co_dinh = hien.slice(0, SO_CO_DINH);
    thu_tu = co_dinh.concat(thu_tu.filter(function (m) { return co_dinh.indexOf(m) < 0; }));
    Array.prototype.forEach.call(LUOI.querySelectorAll("tr"), function (tr) {
      var theo_ma = {};
      Array.prototype.forEach.call(tr.children, function (o) { if (o.dataset.cot) theo_ma[o.dataset.cot] = o; });
      if (!Object.keys(theo_ma).length) return;          // dòng "không có dòng nào"
      thu_tu.forEach(function (ma) { if (theo_ma[ma]) tr.appendChild(theo_ma[ma]); });
    });
  }
  function apBoCuc() {
    apThuTu();
    apRong();
    apAnCot();          // gọi luôn canhCotCoDinh()
    danhChuCot();
  }
  apBoCuc();
  document.body.addEventListener("htmx:afterSwap", function (e) {
    var t = e.detail.target;
    if (t && t.tagName === "TR") apBoCuc();
  });

  // Kéo mép phải tiêu đề để đổi độ rộng
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
    var moi = Math.max(48, Math.round(KEO_RONG.rong + e.clientX - KEO_RONG.x));
    datRong(KEO_RONG.ma, moi);
    KEO_RONG.moi = moi;
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

  // Kéo thả tiêu đề để đổi thứ tự cột (cột cố định đứng yên)
  var KEO_COT = null;
  Array.prototype.forEach.call(LUOI.querySelectorAll("thead th[data-cot]"), function (th) {
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
    Array.prototype.forEach.call(LUOI.querySelectorAll("th.bt-tha-truoc, th.bt-tha-sau"), function (o) {
      o.classList.remove("bt-tha-truoc", "bt-tha-sau");
    });
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
    Array.prototype.forEach.call(LUOI.querySelectorAll("th.bt-dang-keo"), function (o) { o.classList.remove("bt-dang-keo"); });
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

  // ── Chọn ô và định dạng (Giai đoạn B) ──
  // Ô "đang chọn": các ô mang .o-chon (Shift+bấm chọn vùng chữ nhật, Ctrl+bấm
  // thêm từng ô), không có thì là ô vừa được đưa con trỏ vào. Nút trên thanh
  // công cụ lấy con trỏ khi bấm, nên phải nhớ ô cuối cùng bằng tay.
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
    Array.prototype.forEach.call(LUOI.querySelectorAll("td.o-chon"), function (o) { o.classList.remove("o-chon"); });
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
        if (o && o.dataset.cot && !o.hidden) o.classList.add("o-chon");
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
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && LUOI.querySelector("td.o-chon")) boChon();
    if ((e.ctrlKey || e.metaKey) && (e.key === "b" || e.key === "B") && NHOM_DD) {
      var td = oDuLieu(e.target);
      if (td) { e.preventDefault(); guiDinhDang({ b: dangDam(cacODangChon()) ? "" : "1" }); }
    }
  });
  function dangDam(cac) {
    return cac.length > 0 && cac.every(function (o) { return o.classList.contains("dd-dam"); });
  }
  function guiDinhDang(dd) {
    if (!NHOM_DD) return;
    var cac = cacODangChon();
    var loi = document.getElementById("bt-loi");
    if (!cac.length) {
      if (loi) loi.innerHTML = '<div class="bao bao-xau"><span class="bao-ic">!</span><div><b>Chưa chọn ô nào</b><p>Bấm vào một ô, Shift+bấm để chọn vùng, rồi mới định dạng.</p></div></div>';
      return;
    }
    if (loi) loi.innerHTML = "";
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
  }
  document.body.addEventListener("htmx:afterSettle", function (e) {
    var cfg = e.detail && e.detail.requestConfig;
    if (cfg && cfg.elt === NHOM_DD) chonLai();
  });
  document.body.addEventListener("htmx:oobAfterSwap", function (e) {
    var t = e.detail && e.detail.target;
    if (t && t.id && CHON_SAU_SWAP.length > 1 && CHON_SAU_SWAP.indexOf(t.id) >= 0) {
      var moi = document.getElementById(t.id);
      if (moi) moi.classList.add("o-chon");
    }
  });
  document.addEventListener("click", function (e) {
    var nut = e.target.closest && e.target.closest(".bt-dd, .bt-mo-mau");
    if (!nut || nut.tagName === "SELECT") return;
    var bang_mau = document.getElementById("bt-bang-mau");
    if (nut.classList.contains("bt-mo-mau")) {
      var mo = bang_mau.hidden;
      bang_mau.hidden = !mo;
      nut.setAttribute("aria-expanded", mo ? "true" : "false");
      return;
    }
    var loai = nut.dataset.dd;
    if (bang_mau) { bang_mau.hidden = true; }
    if (loai === "xoa") { guiDinhDang({ xoa: "1" }); return; }
    if (loai === "b") { guiDinhDang({ b: dangDam(cacODangChon()) ? "" : "1" }); return; }
    var dd = {};
    dd[loai] = nut.dataset.giaTri || "";
    guiDinhDang(dd);
  });
  document.addEventListener("change", function (e) {
    var chon = e.target.closest && e.target.closest("select.bt-dd");
    if (!chon) return;
    guiDinhDang({ fs: chon.value });
    chon.value = "";
  });
  document.addEventListener("click", function (e) {
    var bang_mau = document.getElementById("bt-bang-mau");
    if (!bang_mau || bang_mau.hidden) return;
    if (e.target.closest(".bt-mau-hop")) return;
    bang_mau.hidden = true;
  });
  // Lỗi 400 của định dạng: vẫn swap (oob) để hiện lời báo
  // (đã bật chung ở htmx:beforeSwap phía trên)

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
