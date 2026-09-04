/* Bảng tính — chọn vùng, bàn phím kiểu Excel, cắt/chép/dán, tay kéo điền, xoá
   nội dung, hoàn tác/làm lại, thống kê vùng chọn (ADR-011). Nạp sau
   bang-tinh.js: dùng window.KNJSC_BT (ô kế bên, mở sửa, dòng trống, thanh
   công thức, định dạng) và cung cấp window.KNJSC_BTO (các ô đang chọn, ghi
   hoàn tác, vẽ lại).

   Mọi thay đổi giá trị đi qua POST luu-o/ — được cả hoặc không gì, quyền kiểm
   ở máy chủ. Hoàn tác là gửi lại giá trị cũ, phía trình duyệt, tối đa 100 bước;
   tải lại trang là hết. Dòng trống vừa thành dòng thật thì không hoàn tác được
   phần tạo dòng (xoá dòng là việc của menu chuột phải).

   Chuột:   bấm chọn · kéo chọn vùng · Shift+bấm mở rộng · bấm số dòng chọn hàng ·
            bấm chữ cột chọn cột · góc trên trái chọn cả trang · kéo ô vuông ở góc
            dưới phải để điền
   Phím:    Shift+mũi tên mở rộng · Ctrl+A cả trang · Ctrl+C/X/V · Delete xoá nội
            dung · Ctrl+Z / Ctrl+Y hoàn tác, làm lại · Esc bỏ dấu cắt */
(function () {
  "use strict";
  var BT = window.KNJSC_BT;
  if (!BT) return;
  var LUOI = BT.LUOI;
  var URL_LUU = LUOI.dataset.luuOUrl || "";
  var DUOC_THEM = LUOI.dataset.themDong === "1";
  var MAX_O = 2000, MAX_HOAN_TAC = 100, MAX_THONG_KE = 20000, SO_DONG_TRONG = 5;
  var TAY = document.getElementById("bt-tay-keo");
  var DIA_CHI = document.getElementById("bt-dia-chi");
  var THONG_KE = document.getElementById("bt-chon-tt");
  var NUT_HOAN = document.getElementById("bt-hoan-tac");
  var NUT_LAM = document.getElementById("bt-lam-lai");
  var HUONG = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] };

  // ── TRẠNG THÁI ──
  var cur = null;            // {r, c} ô hiện tại (chỉ số dòng trong tbody, chỉ số ô trong dòng)
  var neo = null;            // {r, c} mốc của vùng
  var vung = null;           // {r1, c1, r2, c2}
  var dang_keo = false;      // đang kéo chuột chọn vùng
  var dien = null;           // đang kéo tay điền: {nguon, dich}
  var bo_dem = null;         // clipboard nội bộ: {tsv, o: [[{gt, kieu}]], cat, nguon}
  var hoan_tac = [], lam_lai = [];
  var giu_vung = false;      // đang tự đưa con trỏ vào ô, đừng thu vùng về một ô

  function hang() {
    return Array.prototype.filter.call(LUOI.querySelectorAll("tbody tr"), function (tr) {
      return !tr.classList.contains("bt-dong-rong");
    });
  }
  function oTai(r, c) { var h = hang()[r]; return h ? (h.children[c] || null) : null; }
  function viTri(td) {
    var tr = td.parentElement;
    var r = hang().indexOf(tr);
    return r < 0 ? null : { r: r, c: Array.prototype.indexOf.call(tr.children, td) };
  }
  function laO(td) { return !!td && td.tagName === "TD" && !td.hidden; }
  function chuan(a, b) { return { r1: Math.min(a.r, b.r), c1: Math.min(a.c, b.c), r2: Math.max(a.r, b.r), c2: Math.max(a.c, b.c) }; }
  function soCot() { var h = hang()[0]; return h ? h.children.length : 0; }
  function nhieuO() { return !!vung && (vung.r1 !== vung.r2 || vung.c1 !== vung.c2); }
  function giaTri(td) {
    if (!td) return "";
    if (td.classList.contains("o-moi")) { var o = td.querySelector("input:not([type=hidden])"); return o ? o.value : ""; }
    return td.dataset.goc || "";
  }
  function laSo(s) { return s !== "" && s !== null && s !== undefined && isFinite(Number(String(s).replace(/,/g, ""))); }
  function soCua(s) { return Number(String(s).replace(/,/g, "")); }

  // ── VẼ VÙNG CHỌN ──
  var LOP_VE = ["o-chon", "o-chon-t", "o-chon-b", "o-chon-l", "o-chon-r", "o-hien"];
  function xoaVe() {
    Array.prototype.forEach.call(LUOI.querySelectorAll("td.o-chon, td.o-hien"), function (o) {
      LOP_VE.forEach(function (l) { o.classList.remove(l); });
    });
    Array.prototype.forEach.call(LUOI.querySelectorAll(".hl"), function (o) { o.classList.remove("hl"); });
    if (TAY) TAY.hidden = true;
  }
  function ve() {
    xoaVe();
    if (!vung) return;
    var H = hang();
    var chu = LUOI.querySelector("thead tr.bt-hang-chu");
    for (var r = vung.r1; r <= vung.r2; r++) {
      var tr = H[r];
      if (!tr) continue;
      var so = tr.querySelector("th.bt-so-dong");
      if (so) so.classList.add("hl");
      for (var c = vung.c1; c <= vung.c2; c++) {
        var o = tr.children[c];
        if (!laO(o)) continue;
        o.classList.add("o-chon");
        if (r === vung.r1) o.classList.add("o-chon-t");
        if (r === vung.r2) o.classList.add("o-chon-b");
        if (c === vung.c1) o.classList.add("o-chon-l");
        if (c === vung.c2) o.classList.add("o-chon-r");
      }
    }
    if (chu) for (var k = vung.c1; k <= vung.c2; k++) { var th = chu.children[k]; if (th && !th.hidden) th.classList.add("hl"); }
    var oc = cur && oTai(cur.r, cur.c);
    if (oc) oc.classList.add("o-hien");
    datTay();
    capNhatDiaChi();
    thongKe();
  }
  function datTay() {
    if (!TAY || !vung) return;
    var goc = oTai(vung.r2, vung.c2);
    if (!laO(goc) || goc.classList.contains("o-trong-cot")) { TAY.hidden = true; return; }
    var rl = LUOI.getBoundingClientRect(), ro = goc.getBoundingClientRect();
    TAY.style.left = (ro.right - rl.left + LUOI.scrollLeft - 5) + "px";
    TAY.style.top = (ro.bottom - rl.top + LUOI.scrollTop - 5) + "px";
    TAY.hidden = false;
  }
  function capNhatDiaChi() {
    if (!DIA_CHI || !vung) return;
    if (!nhieuO()) return;                       // một ô: bang-tinh.js đã ghi địa chỉ khi ô nhận con trỏ
    var a = oTai(vung.r1, vung.c1), b = oTai(vung.r2, vung.c2);
    if (a && b) DIA_CHI.value = BT.diaChi(a) + ":" + BT.diaChi(b);
  }
  function thongKe() {
    if (!THONG_KE) return;
    THONG_KE.textContent = "";
    if (!nhieuO()) return;
    var n = 0, tong = 0, so = 0, dem = 0;
    var H = hang();
    for (var r = vung.r1; r <= vung.r2; r++) {
      var tr = H[r];
      if (!tr) continue;
      for (var c = vung.c1; c <= vung.c2; c++) {
        if (++dem > MAX_THONG_KE) return;
        var td = tr.children[c];
        if (!laO(td)) continue;
        var gt = giaTri(td);
        if (gt === "") continue;
        n++;
        if (laSo(gt)) { so++; tong += soCua(gt); }
      }
    }
    if (n < 2) return;
    var chu = "Số ô: " + n;
    if (so) chu = "Tổng: " + lamTron(tong) + "  ·  TB: " + lamTron(tong / so) + "  ·  " + chu;
    THONG_KE.textContent = chu;
  }
  function lamTron(x) { return String(Math.round(x * 1e6) / 1e6); }

  // ── CHỌN ──
  function datCur(r, c, giu_neo) {
    var o = oTai(r, c);
    if (!laO(o)) return false;
    cur = { r: r, c: c };
    if (!giu_neo || !neo) neo = { r: r, c: c };
    vung = chuan(neo, cur);
    ve();
    return true;
  }
  function moRongToi(r, c) {
    var o = oTai(r, c);
    if (!laO(o) || !neo) return;
    vung = chuan(neo, { r: r, c: c });
    ve();
  }
  function tapTrung(td) {                       // đưa con trỏ vào ô mà không thu vùng
    if (!td) return;
    giu_vung = true;
    var muc = td.classList.contains("o-moi") ? td.querySelector("input:not([type=hidden])") : td;
    if (muc && muc.focus) muc.focus({ preventScroll: true });
    giu_vung = false;
  }
  function chonCot(c, them) {
    var H = hang();
    if (!H.length || !laO(oTai(0, c))) return;
    if (them && vung) { vung = { r1: 0, r2: H.length - 1, c1: Math.min(vung.c1, c), c2: Math.max(vung.c2, c) }; }
    else { neo = { r: 0, c: c }; cur = { r: 0, c: c }; vung = { r1: 0, r2: H.length - 1, c1: c, c2: c }; }
    ve();
    tapTrung(oTai(cur.r, cur.c));
  }
  function chonHang(r, them) {
    var n = soCot();
    if (n < 2 || !hang()[r]) return;
    var c_dau = dauDong(r);
    if (them && vung) { vung = { r1: Math.min(vung.r1, r), r2: Math.max(vung.r2, r), c1: 1, c2: n - 1 }; }
    else { neo = { r: r, c: c_dau }; cur = { r: r, c: c_dau }; vung = { r1: r, r2: r, c1: 1, c2: n - 1 }; }
    ve();
    tapTrung(oTai(cur.r, cur.c));
  }
  function dauDong(r) {
    var tr = hang()[r];
    for (var c = 1; c < tr.children.length; c++) if (laO(tr.children[c])) return c;
    return 1;
  }
  function chonTatCa() {
    var H = hang(), n = soCot();
    if (!H.length || n < 2) return;
    neo = { r: 0, c: dauDong(0) }; cur = { r: 0, c: dauDong(0) };
    vung = { r1: 0, r2: H.length - 1, c1: 1, c2: n - 1 };
    ve();
    tapTrung(oTai(cur.r, cur.c));
  }
  function boChon() {
    if (cur) { neo = { r: cur.r, c: cur.c }; vung = chuan(neo, cur); ve(); } else { vung = null; xoaVe(); }
  }
  function cacODangChon() {
    return Array.prototype.slice.call(LUOI.querySelectorAll("td.o-chon[data-dong][data-cot]"));
  }
  // Ô nhận con trỏ (bấm, mũi tên, Tab, sau khi lưu) là ô hiện tại; nếu không
  // đang giữ vùng thì vùng thu về một ô đó
  LUOI.addEventListener("focusin", function (e) {
    var td = e.target.closest && e.target.closest("td");
    if (!td || td.classList.contains("dang-sua")) return;
    var vt = viTri(td);
    if (!vt) return;
    if (giu_vung || dang_keo) { cur = vt; ve(); return; }
    cur = vt; neo = vt; vung = chuan(vt, vt);
    ve();
  });
  LUOI.addEventListener("bt-chon-vung", function (e) {
    var a = e.detail && e.detail.a, b = e.detail && e.detail.b;
    var va = a && viTri(a), vb = b && viTri(b);
    if (!va || !vb) return;
    neo = va; cur = va; vung = chuan(va, vb);
    ve();
    tapTrung(a);
  });
  LUOI.addEventListener("bt-chon-tat-ca", chonTatCa);

  // ── CHUỘT ──
  LUOI.addEventListener("mousedown", function (e) {
    if (e.button !== 0) return;
    if (e.target.closest(".nut-loc, .bt-keo-cot, .o-khoa-loc, .bt-tay-keo")) return;
    var so = e.target.closest("tbody th.bt-so-dong");
    if (so) { e.preventDefault(); var vt = viTri(so); if (vt) chonHang(vt.r, e.shiftKey); return; }
    var chu = e.target.closest("thead tr.bt-hang-chu th");
    if (chu) {
      if (chu.classList.contains("bt-goc")) { e.preventDefault(); chonTatCa(); return; }
      var c = Array.prototype.indexOf.call(chu.parentElement.children, chu);
      if (c > 0) { chonCot(c, e.shiftKey); }
      return;
    }
    var td = e.target.closest("td");
    if (!td || !LUOI.contains(td) || td.classList.contains("dang-sua")) return;
    var vt2 = viTri(td);
    if (!vt2) return;
    if (e.shiftKey && neo) { e.preventDefault(); moRongToi(vt2.r, vt2.c); return; }
    // Ctrl+bấm: như bấm thường (không có nhiều vùng rời nhau, như demo)
    neo = vt2; cur = vt2; vung = chuan(vt2, vt2);
    dang_keo = true;
    LUOI.classList.add("bt-dang-chon");
    ve();
    // bấm vào ô hiển thị thì trình duyệt tự đưa con trỏ (tabindex); ô dòng trống thì vào ô nhập
  });
  document.addEventListener("mousemove", function (e) {
    if (dien) { keoDien(e); return; }
    if (!dang_keo) return;
    var el = document.elementFromPoint(e.clientX, e.clientY);
    var td = el && el.closest && el.closest("td");
    if (!td || !LUOI.contains(td)) return;
    var vt = viTri(td);
    if (!vt || !laO(td)) return;
    if (vung && vt.r === (neo.r === vung.r1 ? vung.r2 : vung.r1) && vt.c === (neo.c === vung.c1 ? vung.c2 : vung.c1)) return;
    moRongToi(vt.r, vt.c);
  });
  document.addEventListener("mouseup", function () {
    if (dang_keo) { dang_keo = false; LUOI.classList.remove("bt-dang-chon"); }
    if (dien) { thaDien(); }
  });
  // Đang kéo chọn thì không cho bấm đúp mở sửa hay chọn chữ
  LUOI.addEventListener("selectstart", function (e) { if (dang_keo || dien) e.preventDefault(); });

  // ── BÀN PHÍM ──
  document.addEventListener("keydown", function (e) {
    // Hoàn tác / làm lại nghe ở mọi nơi trừ ô đang gõ (kể cả khi con trỏ đang ở nút thanh công cụ)
    if ((e.ctrlKey || e.metaKey) && !e.altKey && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) {
      var kz = e.key.toLowerCase();
      if (kz === "z") { e.preventDefault(); if (e.shiftKey) lamLaiDi(); else hoanTacDi(); return; }
      if (kz === "y") { e.preventDefault(); lamLaiDi(); return; }
    }
    var td = e.target.closest && e.target.closest("td");
    if (!td || !LUOI.contains(td) || td.classList.contains("dang-sua")) return;
    var trong_o_nhap = e.target.tagName === "INPUT";
    var h = HUONG[e.key];
    if (h && e.shiftKey && vung && !trong_o_nhap) {
      e.preventDefault();
      var xa = { r: neo.r === vung.r1 ? vung.r2 : vung.r1, c: neo.c === vung.c1 ? vung.c2 : vung.c1 };
      var r = xa.r + h[0], c = xa.c + h[1];
      while (oTai(r, c) && oTai(r, c).hidden) c += h[1];    // nhảy qua cột ẩn
      if (c < 1) c = 1;
      if (oTai(r, c)) moRongToi(r, c);
      return;
    }
    if ((e.ctrlKey || e.metaKey) && !e.altKey) {
      var k = e.key.toLowerCase();
      if (k === "a") { e.preventDefault(); chonTatCa(); return; }
      if (k === "c" || k === "x") {
        if (trong_o_nhap && !nhieuO()) return;               // một ô nhập: để trình duyệt chép chữ trong ô
        e.preventDefault(); saoChep(k === "x"); return;
      }
      return;
    }
    if ((e.key === "Delete" || e.key === "Backspace") && !trong_o_nhap) { e.preventDefault(); xoaNoiDung(); return; }
    if (e.key === "Escape") { boCat(); }
  });
  document.addEventListener("paste", function (e) {
    var act = document.activeElement;
    var td = act && act.closest && act.closest("td");
    if (!td || !LUOI.contains(td) || td.classList.contains("dang-sua")) return;
    var chu = (e.clipboardData || window.clipboardData).getData("text/plain");
    if (act.tagName === "INPUT" && !/[\t\r\n]/.test(chu) && !nhieuO()) return;  // dán một giá trị vào ô dòng trống: để trình duyệt làm
    e.preventDefault();
    dan(chu);
  });

  // ── CLIPBOARD ──
  function maTran(v) {
    var H = hang(), ma = [];
    for (var r = v.r1; r <= v.r2; r++) {
      var tr = H[r], dong = [];
      for (var c = v.c1; c <= v.c2; c++) {
        var td = tr ? tr.children[c] : null;
        if (td && td.hidden) continue;
        dong.push({ gt: giaTri(td), kieu: td ? kieuTuLop(td.className) : {} });
      }
      ma.push(dong);
    }
    return ma;
  }
  function tsvCua(ma) {
    return ma.map(function (d) {
      return d.map(function (o) { return String(o.gt).replace(/[\t\r\n]+/g, " "); }).join("\t");
    }).join("\n");
  }
  function saoChep(cat) {
    if (!vung) return;
    boCat();
    var ma = maTran(vung);
    var tsv = tsvCua(ma);
    bo_dem = { tsv: tsv, o: ma, cat: cat, nguon: { r1: vung.r1, c1: vung.c1, r2: vung.r2, c2: vung.c2 } };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(tsv).catch(function () { chepDuPhong(tsv); });
    } else {
      chepDuPhong(tsv);
    }
    if (cat) {
      var H = hang();
      for (var r = vung.r1; r <= vung.r2; r++) for (var c = vung.c1; c <= vung.c2; c++) {
        var td = H[r] && H[r].children[c];
        if (laO(td)) td.classList.add("o-cat");
      }
    }
  }
  function chepDuPhong(tsv) {
    var ta = document.createElement("textarea");
    ta.value = tsv;
    ta.setAttribute("aria-hidden", "true");
    ta.style.position = "fixed"; ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (err) {}
    ta.remove();
    var oc = cur && oTai(cur.r, cur.c);
    if (oc) tapTrung(oc);
  }
  function boCat() {
    Array.prototype.forEach.call(LUOI.querySelectorAll("td.o-cat"), function (o) { o.classList.remove("o-cat"); });
    if (bo_dem) bo_dem.cat = false;
  }
  function tachTSV(chu) {
    var dong = chu.replace(/\r\n?/g, "\n").split("\n");
    if (dong.length > 1 && dong[dong.length - 1] === "") dong.pop();
    return dong.map(function (d) { return d.split("\t").map(function (g) { return { gt: g, kieu: null }; }); });
  }
  function dan(chu) {
    if (!cur) return;
    var noi_bo = !!(bo_dem && chu === bo_dem.tsv);
    var ma = noi_bo ? bo_dem.o : tachTSV(chu || "");
    if (!ma.length || !ma[0].length) return;
    var cat = noi_bo && bo_dem.cat ? bo_dem.nguon : null;
    danVao(ma, noi_bo, cat);
  }
  // Dán ma trận từ góc trên trái vùng chọn; vùng chọn là bội số thì lặp khối;
  // tràn xuống dòng trống thì tạo dòng, tràn ra cột trống thì bỏ phần thừa
  function danVao(ma, mang_kieu, cat) {
    var dau = vung ? { r: vung.r1, c: vung.c1 } : cur;
    var mh = ma.length, mw = Math.max.apply(null, ma.map(function (d) { return d.length; }));
    var h = mh, w = mw;
    if (vung && nhieuO()) {
      var vh = vung.r2 - vung.r1 + 1, vw = vung.c2 - vung.c1 + 1;
      if (vh % mh === 0 && vw % mw === 0 && (vh > mh || vw > mw)) { h = vh; w = vw; }
    }
    var thieu_dong = dau.r + h - hang().length;
    if (thieu_dong > 0 && DUOC_THEM) BT.themDongTrong(thieu_dong);
    var items = [], bo_qua = 0, buoc = [], kieu_theo_o = {};
    var H = hang();
    for (var i = 0; i < h; i++) {
      var tr = H[dau.r + i];
      if (!tr) { bo_qua += w; continue; }
      var cot_that = 0;
      for (var c = dau.c, j = 0; j < w; c++) {
        var td = tr.children[c];
        if (!td) { bo_qua += w - j; break; }
        if (td.hidden) continue;
        var o = ma[i % mh][j % mw] || { gt: "" };
        j++;
        var kq = ghiO(td, o.gt, tr);
        if (!kq) { bo_qua++; continue; }
        items.push(kq.item);
        if (kq.buoc) buoc.push(kq.buoc);
        if (mang_kieu && td.id && o.kieu) kieu_theo_o[td.id] = o.kieu;
        cot_that++;
      }
    }
    luuO(items, { buoc: buoc, chon: { r1: dau.r, c1: dau.c, r2: dau.r + h - 1, c2: dau.c + w - 1 }, bo_qua: bo_qua })
      .then(function (ok) {
        if (!ok) return;
        if (mang_kieu) apKieuDaChep(kieu_theo_o);
        if (cat) {
          var xoa = [];
          var H2 = hang();
          for (var r = cat.r1; r <= cat.r2; r++) for (var c2 = cat.c1; c2 <= cat.c2; c2++) {
            var o2 = H2[r] && H2[r].children[c2];
            if (!laO(o2) || (r >= dau.r && r <= dau.r + h - 1 && c2 >= dau.c && c2 <= dau.c + w - 1)) continue;
            var kq2 = ghiO(o2, "", H2[r]);
            if (kq2) xoa.push(kq2.item);
          }
          boCat();
          bo_dem = null;
          if (xoa.length) luuO(xoa, { buoc: [] });
        }
      });
  }
  // Chuẩn bị ghi một ô: trả {item, buoc} hoặc null nếu ô không ghi được
  function ghiO(td, gt, tr) {
    if (td.classList.contains("o-trong-cot") || td.classList.contains("o-tinh")) return null;
    if (td.classList.contains("o-moi")) {
      var inp = td.querySelector("input:not([type=hidden])");
      if (!inp || !td.dataset.cot) return null;
      inp.value = gt;
      return { item: { khoa: tr.dataset.moi, cot: td.dataset.cot, gt: gt }, buoc: null };
    }
    if (!td.dataset.suaUrl || !td.dataset.dong || !td.dataset.cot) return null;
    return {
      item: { khoa: td.dataset.dong, cot: td.dataset.cot, gt: gt },
      buoc: { khoa: td.dataset.dong, cot: td.dataset.cot, cu: td.dataset.goc || "", moi: gt },
    };
  }
  function apKieuDaChep(kieu_theo_o) {
    var nhom = {};
    Object.keys(kieu_theo_o).forEach(function (id) {
      var k = JSON.stringify(kieu_theo_o[id]);
      (nhom[k] = nhom[k] || []).push(id);
    });
    Object.keys(nhom).forEach(function (k) {
      var cac = nhom[k].map(function (id) { return document.getElementById(id); }).filter(Boolean);
      if (cac.length) BT.guiDinhDangCho(cac, kieuDayDu(JSON.parse(k)), false);
    });
  }

  // ── XOÁ NỘI DUNG ──
  function xoaNoiDung() {
    if (!vung) return;
    var H = hang(), items = [], buoc = [], bo_qua = 0;
    for (var r = vung.r1; r <= vung.r2; r++) for (var c = vung.c1; c <= vung.c2; c++) {
      var td = H[r] && H[r].children[c];
      if (!laO(td)) continue;
      if (giaTri(td) === "") continue;
      var kq = ghiO(td, "", H[r]);
      if (!kq) { bo_qua++; continue; }
      items.push(kq.item);
      if (kq.buoc) buoc.push(kq.buoc);
    }
    if (!items.length) return;
    luuO(items, { buoc: buoc, bo_qua: bo_qua });
  }

  // ── TAY KÉO ĐIỀN ──
  if (TAY) TAY.addEventListener("mousedown", function (e) {
    if (!vung) return;
    e.preventDefault();
    dien = { nguon: { r1: vung.r1, c1: vung.c1, r2: vung.r2, c2: vung.c2 }, dich: null };
    document.body.classList.add("bt-dang-keo");
  });
  function xoaVeDien() {
    Array.prototype.forEach.call(LUOI.querySelectorAll("td.o-dien"), function (o) {
      o.classList.remove("o-dien", "o-dien-t", "o-dien-b", "o-dien-l", "o-dien-r");
    });
  }
  function keoDien(e) {
    var el = document.elementFromPoint(e.clientX, e.clientY);
    var td = el && el.closest && el.closest("td");
    if (!td || !LUOI.contains(td)) return;
    var vt = viTri(td);
    if (!vt) return;
    var n = dien.nguon;
    var xuong = vt.r > n.r2 ? vt.r - n.r2 : 0, len = vt.r < n.r1 ? n.r1 - vt.r : 0;
    var phai = vt.c > n.c2 ? vt.c - n.c2 : 0, trai = vt.c < n.c1 ? n.c1 - vt.c : 0;
    var dich = null;
    var lon = Math.max(xuong, len, phai, trai);
    if (lon > 0) {
      if (lon === xuong) dich = { r1: n.r2 + 1, r2: vt.r, c1: n.c1, c2: n.c2, huong: "xuong" };
      else if (lon === len) dich = { r1: vt.r, r2: n.r1 - 1, c1: n.c1, c2: n.c2, huong: "len" };
      else if (lon === phai) dich = { r1: n.r1, r2: n.r2, c1: n.c2 + 1, c2: vt.c, huong: "phai" };
      else dich = { r1: n.r1, r2: n.r2, c1: vt.c, c2: n.c1 - 1, huong: "trai" };
    }
    dien.dich = dich;
    xoaVeDien();
    if (!dich) return;
    var H = hang();
    for (var r = dich.r1; r <= dich.r2; r++) for (var c = dich.c1; c <= dich.c2; c++) {
      var o = H[r] && H[r].children[c];
      if (!laO(o)) continue;
      o.classList.add("o-dien");
      if (r === dich.r1) o.classList.add("o-dien-t");
      if (r === dich.r2) o.classList.add("o-dien-b");
      if (c === dich.c1) o.classList.add("o-dien-l");
      if (c === dich.c2) o.classList.add("o-dien-r");
    }
  }
  function buocChuoi(cac) {                      // số cách đều → bước; không thì null
    if (cac.length < 2 || !cac.every(laSo)) return null;
    var so = cac.map(soCua), b = so[1] - so[0];
    for (var i = 2; i < so.length; i++) if (Math.abs(so[i] - so[i - 1] - b) > 1e-9) return null;
    return { b: b, cuoi: so[so.length - 1], dau: so[0] };
  }
  function thaDien() {
    var d = dien;
    dien = null;
    document.body.classList.remove("bt-dang-keo");
    xoaVeDien();
    if (!d || !d.dich) return;
    var n = d.nguon, t = d.dich, H = hang();
    var nguon = maTran(n);
    var h = n.r2 - n.r1 + 1, w = n.c2 - n.c1 + 1;
    var items = [], buoc = [];
    var doc = t.huong === "xuong" || t.huong === "len";
    for (var r = t.r1; r <= t.r2; r++) {
      var tr = H[r];
      if (!tr) continue;
      for (var c = t.c1; c <= t.c2; c++) {
        var td = tr.children[c];
        if (!laO(td)) continue;
        var gt;
        if (doc) {
          var cot = nguon.map(function (dong) { return (dong[c - n.c1] || { gt: "" }).gt; });
          var ch = buocChuoi(cot);
          var k = t.huong === "xuong" ? r - n.r2 : n.r1 - r;
          gt = ch ? lamTron((t.huong === "xuong" ? ch.cuoi + ch.b * k : ch.dau - ch.b * k))
                  : cot[(((r - n.r1) % h) + h) % h];
        } else {
          var dong2 = nguon[r - n.r1] || [];
          var hang_gt = dong2.map(function (o) { return o.gt; });
          var ch2 = buocChuoi(hang_gt);
          var k2 = t.huong === "phai" ? c - n.c2 : n.c1 - c;
          gt = ch2 ? lamTron((t.huong === "phai" ? ch2.cuoi + ch2.b * k2 : ch2.dau - ch2.b * k2))
                   : hang_gt[(((c - n.c1) % w) + w) % w];
        }
        var kq = ghiO(td, gt === undefined ? "" : gt, tr);
        if (!kq) continue;
        items.push(kq.item);
        if (kq.buoc) buoc.push(kq.buoc);
      }
    }
    var hop = { r1: Math.min(n.r1, t.r1), c1: Math.min(n.c1, t.c1), r2: Math.max(n.r2, t.r2), c2: Math.max(n.c2, t.c2) };
    luuO(items, { buoc: buoc, chon: hop });
  }

  // ── LƯU NHIỀU Ô ──
  var dang_luu = Promise.resolve(true);
  // htmx bắn afterRequest trước khi thay ô (oob); phải chờ afterSettle mới có DOM
  // mới để đánh số lại và bù dòng trống. Lỗi không có swap (403, 500) thì xong ngay.
  function guiLuu(values) {
    return new Promise(function (resolve) {
      var xhr = null, hen = null;
      function cuaToi(e) { var cfg = e.detail && e.detail.requestConfig; return !!cfg && cfg.path === URL_LUU; }
      function don() {
        document.body.removeEventListener("htmx:afterRequest", sauYeuCau);
        document.body.removeEventListener("htmx:afterSettle", sauLang);
        clearTimeout(hen);
      }
      function sauYeuCau(e) {
        if (!cuaToi(e)) return;
        xhr = e.detail.xhr;
        var co_swap = xhr && ((xhr.status >= 200 && xhr.status < 300) || xhr.status === 400);
        if (co_swap) return;
        don(); resolve(xhr);
      }
      function sauLang(e) { if (!cuaToi(e)) return; don(); resolve(xhr || e.detail.xhr); }
      document.body.addEventListener("htmx:afterRequest", sauYeuCau);
      document.body.addEventListener("htmx:afterSettle", sauLang);
      hen = setTimeout(function () { don(); resolve(xhr); }, 20000);
      htmx.ajax("POST", URL_LUU, { source: LUOI, target: LUOI, swap: "none", values: values });
    });
  }
  function luuO(items, opts) {
    opts = opts || {};
    if (!URL_LUU) return Promise.resolve(false);
    if (!items.length) {
      BT.baoLoi("Không có ô nào lưu được", opts.bo_qua ? "Ô đã chọn là cột trống, cột tính sẵn hay ô bạn không sửa được." : "Chọn ô sửa được rồi thử lại.");
      return Promise.resolve(false);
    }
    if (items.length > MAX_O) {
      BT.baoLoi("Quá nhiều ô", "Chỉ lưu tối đa " + MAX_O + " ô một lần — dán thành nhiều đợt.");
      return Promise.resolve(false);
    }
    var values = { o: items.map(function (i) { return i.khoa + ":" + i.cot; }), gt: items.map(function (i) { return i.gt; }) };
    var viec = dang_luu.then(function () { return guiLuu(values); }).then(function (xhr) {
      var ok = xhr && xhr.status >= 200 && xhr.status < 300;
      LUOI.dispatchEvent(new CustomEvent("bt-da-luu", { detail: { ok: ok, status: xhr ? xhr.status : 0, so_o: items.length } }));
      if (ok) {
        if (opts.buoc && opts.buoc.length && !opts.khong_ghi) ghiBuoc({ loai: "gia_tri", cac: opts.buoc });
        BT.apBoCuc();
        boSungDongTrong();
        if (opts.chon) { vung = opts.chon; if (!cur || cur.r < vung.r1 || cur.r > vung.r2 || cur.c < vung.c1 || cur.c > vung.c2) { cur = { r: vung.r1, c: vung.c1 }; neo = cur; } }
        ve();
        if (opts.bo_qua) BT.baoLoi("Đã lưu, bỏ qua " + opts.bo_qua + " ô", "Cột trống, cột tính sẵn và ô bạn không sửa được thì không nhận dữ liệu.");
      } else if (xhr && xhr.status === 400) {
        chiOLoi();
      } else if (xhr && xhr.status === 403) {
        BT.baoLoi("Không có quyền", "Bạn không sửa được một trong các dòng vừa chọn, hoặc dòng đó ngoài phạm vi — không ô nào được lưu.");
      } else {
        BT.baoLoi("Lỗi lưu", "Máy chủ không trả lời được — thử lại sau.");
      }
      return ok;
    });
    dang_luu = viec.catch(function (err) { if (window.console) console.error("luu-o:", err); return false; });
    return viec;
  }
  // Lời báo 400 mang `data-o`: đổi thành địa chỉ ô như Excel
  function chiOLoi() {
    var bao = document.querySelector("#bt-loi [data-o]");
    if (!bao) return;
    var phan = bao.dataset.o.split(":"), td = null;
    if (/^\d+$/.test(phan[0])) td = document.getElementById("o-" + phan[0] + "-" + phan[1]);
    else { var tr = LUOI.querySelector('tr[data-moi="' + phan[0] + '"]'); td = tr && tr.querySelector('td[data-cot="' + phan[1] + '"]'); }
    if (!td) return;
    var p = bao.querySelector("p");
    if (p) p.textContent = "Ô " + BT.diaChi(td) + ": " + p.textContent;
    var vt = viTri(td);
    if (vt) { cur = vt; neo = vt; vung = chuan(vt, vt); ve(); }
  }
  function boSungDongTrong() {
    if (!DUOC_THEM) return;
    var n = LUOI.querySelectorAll("tbody tr.dong-moi").length;
    if (n < SO_DONG_TRONG) BT.themDongTrong(SO_DONG_TRONG - n);
  }

  // ── HOÀN TÁC / LÀM LẠI ──
  function ghiBuoc(b) {
    hoan_tac.push(b);
    if (hoan_tac.length > MAX_HOAN_TAC) hoan_tac.shift();
    lam_lai = [];
    capNhatNutHoanTac();
  }
  function capNhatNutHoanTac() {
    if (NUT_HOAN) NUT_HOAN.disabled = !hoan_tac.length;
    if (NUT_LAM) NUT_LAM.disabled = !lam_lai.length;
  }
  function hoanTacDi() {
    var b = hoan_tac.pop();
    if (!b) return;
    apBuoc(b, true).then(function (ok) { if (ok) lam_lai.push(b); else hoan_tac.push(b); capNhatNutHoanTac(); });
    capNhatNutHoanTac();
  }
  function lamLaiDi() {
    var b = lam_lai.pop();
    if (!b) return;
    apBuoc(b, false).then(function (ok) { if (ok) hoan_tac.push(b); else lam_lai.push(b); capNhatNutHoanTac(); });
    capNhatNutHoanTac();
  }
  function apBuoc(b, nguoc) {
    if (b.loai === "gia_tri") {
      var items = b.cac.map(function (o) { return { khoa: o.khoa, cot: o.cot, gt: nguoc ? o.cu : o.moi }; });
      return luuO(items, { khong_ghi: true });
    }
    if (b.loai === "dinh_dang") {
      if (!nguoc) {
        var cac = b.cac.map(function (o) { return document.getElementById(o.id); }).filter(Boolean);
        return Promise.resolve(BT.guiDinhDangCho(cac, b.dd, false)).then(function () { return true; });
      }
      var nhom = {};
      b.cac.forEach(function (o) { var k = JSON.stringify(o.cu); (nhom[k] = nhom[k] || []).push(o.id); });
      var viec = Object.keys(nhom).map(function (k) {
        var cac2 = nhom[k].map(function (id) { return document.getElementById(id); }).filter(Boolean);
        return cac2.length ? BT.guiDinhDangCho(cac2, kieuDayDu(JSON.parse(k)), false) : null;
      });
      return Promise.all(viec).then(function () { return true; });
    }
    return Promise.resolve(false);
  }
  if (NUT_HOAN) NUT_HOAN.addEventListener("click", hoanTacDi);
  if (NUT_LAM) NUT_LAM.addEventListener("click", lamLaiDi);
  // bang-tinh.js gọi trước khi gửi định dạng: nhớ kiểu cũ từng ô
  function ghiDinhDang(cac, dd) {
    ghiBuoc({ loai: "dinh_dang", dd: dd, cac: cac.map(function (o) { return { id: o.id, cu: kieuTuLop(o.className) }; }) });
  }
  // Sổ định dạng đọc ngược từ lớp CSS (record_service.STYLE_SCHEMA ↔ grid_service.STYLE_CLASSES)
  var LOP_BAT = { "dd-dam": "b", "dd-nghieng": "i", "dd-gach-chan": "u", "dd-gach-ngang": "st", "dd-xuong-dong": "wr", "dd-vien": "bd" };
  var LOP_CAN = { "dd-can-trai": "l", "dd-can-giua": "c", "dd-can-phai": "r" };
  var LOP_DINH = { "dd-dinh-so": "num", "dd-dinh-phan-tram": "pct", "dd-dinh-usd": "usd", "dd-dinh-vnd": "vnd", "dd-dinh-chu": "text" };
  var MOI_KHOA = ["b", "i", "u", "st", "wr", "bd", "bg", "c", "fs", "al", "fmt"];
  function kieuTuLop(className) {
    var k = {};
    String(className || "").split(/\s+/).forEach(function (l) {
      if (LOP_BAT[l]) k[LOP_BAT[l]] = "1";
      else if (LOP_CAN[l]) k.al = LOP_CAN[l];
      else if (LOP_DINH[l]) k.fmt = LOP_DINH[l];
      else if (l.indexOf("dd-nen-") === 0) k.bg = l.slice(7);
      else if (l.indexOf("dd-chu-") === 0) k.c = l.slice(7);
      else if (l.indexOf("dd-co-") === 0) k.fs = l.slice(6);
    });
    return k;
  }
  function kieuDayDu(k) {                       // mọi khoá: thiếu là bỏ — thay hẳn kiểu cũ
    var d = {};
    MOI_KHOA.forEach(function (khoa) { d[khoa] = k[khoa] || ""; });
    return d;
  }

  // ── VẼ LẠI SAU KHI MÁY CHỦ TRẢ Ô MỚI ──
  var hen_ve = null;
  function veSau() { clearTimeout(hen_ve); hen_ve = setTimeout(function () { if (vung) ve(); }, 30); }
  document.body.addEventListener("htmx:afterSettle", veSau);
  document.body.addEventListener("htmx:oobAfterSwap", veSau);
  LUOI.addEventListener("scroll", function () { if (vung) datTay(); });
  window.addEventListener("resize", function () { if (vung) datTay(); });

  window.KNJSC_BTO = {
    cacODangChon: cacODangChon, boChon: boChon, ghiDinhDang: ghiDinhDang, veLai: veSau,
    vung: function () { return vung; }, dan: dan, saoChep: saoChep, xoaNoiDung: xoaNoiDung,
    hoanTac: hoanTacDi, lamLai: lamLaiDi, chonTatCa: chonTatCa,
  };
})();
