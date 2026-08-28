/* ══════════════════════════════════════════════════════════════════
   BẢNG TÍNH — engine tự viết, không dùng thư viện ngoài (ADR-002)

   Ranh giới bắt buộc theo kien-truc.md:
   sheet KHÔNG phải nguồn dữ liệu. Trang tính nối với bảng cố định thì
   các cột lấy từ bảng đó là chỉ đọc — người dùng tính toán ở cột bên
   phải, kết quả không ghi ngược về bảng gốc.
   ══════════════════════════════════════════════════════════════════ */

const SO_COT = 14;          /* A tới N */
const SO_DONG_DAU = 60;

/* ── Địa chỉ ô ────────────────────────────────────────────────── */
const tenCot = i => {
  let s = "";
  for (i++; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + (i - 1) % 26) + s;
  return s;
};
const soCot = ten => {
  let n = 0;
  for (const c of ten.toUpperCase()) n = n * 26 + (c.charCodeAt(0) - 64);
  return n - 1;
};
const diaChi = (d, c) => tenCot(c) + (d + 1);
const tachDiaChi = a => {
  const m = /^([A-Za-z]+)(\d+)$/.exec(a.trim());
  return m ? { d: parseInt(m[2], 10) - 1, c: soCot(m[1]) } : null;
};

/* ── Tài liệu ─────────────────────────────────────────────────── */
let TL = null;      /* tài liệu đang mở */
let hienTai = { d: 0, c: 0 };
let neo = { d: 0, c: 0 };   /* neo của vùng chọn */
let dangKeo = false;
let lichSu = [], lichSuTien = [];

const trangHien = () => TL.trang[TL.hien];
const oTai = (t, d, c) => t.o[diaChi(d, c)];

function datO(t, d, c, v) {
  const a = diaChi(d, c);
  if (v === "" || v === null || v === undefined) {
    if (t.o[a]) { delete t.o[a].v; if (!t.o[a].s) delete t.o[a]; }
  } else {
    t.o[a] = t.o[a] || {};
    t.o[a].v = v;
  }
}

function khoaO(t, d, c) {
  /* Cột lấy từ bảng cố định là chỉ đọc — ranh giới kiến trúc */
  return !!t.nguon && c < (t.cot_khoa || 0);
}

/* ── Ghi nhớ để hoàn tác ──────────────────────────────────────── */
function ghiNho() {
  lichSu.push(JSON.stringify(TL.trang));
  if (lichSu.length > 60) lichSu.shift();
  lichSuTien.length = 0;
  capNhatNutHoanTac();
}
function hoanTac() {
  if (!lichSu.length) return;
  lichSuTien.push(JSON.stringify(TL.trang));
  TL.trang = JSON.parse(lichSu.pop());
  ve(); capNhatNutHoanTac(); danhDauChuaLuu();
}
function lamLai() {
  if (!lichSuTien.length) return;
  lichSu.push(JSON.stringify(TL.trang));
  TL.trang = JSON.parse(lichSuTien.pop());
  ve(); capNhatNutHoanTac(); danhDauChuaLuu();
}
function capNhatNutHoanTac() {
  document.getElementById("bt-hoan-tac").disabled = !lichSu.length;
  document.getElementById("bt-lam-lai").disabled = !lichSuTien.length;
}

/* ══ TÍNH CÔNG THỨC ════════════════════════════════════════════
   Bộ phân tích đệ quy nhỏ. Chỉ nhận các hàm khai báo trong HAM —
   không dùng eval, nên chuỗi lạ trong ô không chạy được gì.        */

const LOI = t => ({ loi: t });
const laLoi = v => v && typeof v === "object" && "loi" in v;

/* Chỉ nhận là số khi khớp hẳn một trong bốn dạng viết của tiếng Việt.
   Nhờ vậy "28.08" là ngày, không bị đọc thành 2808. */
function thuSo(v) {
  if (typeof v === "number") return v;
  if (typeof v !== "string") return null;
  const t = v.trim();
  if (t === "") return null;
  if (/^-?\d+$/.test(t)) return parseFloat(t);                       /* 1234 */
  if (/^-?\d+,\d+$/.test(t)) return parseFloat(t.replace(",", "."));  /* 1234,56 */
  if (/^-?\d{1,3}(\.\d{3})+(,\d+)?$/.test(t))                         /* 1.234.567,89 */
    return parseFloat(t.replace(/\./g, "").replace(",", "."));
  return null;
}

function soHoa(v) {
  if (laLoi(v)) return v;
  if (v === null || v === undefined || v === "") return 0;
  if (typeof v === "boolean") return v ? 1 : 0;
  const n = thuSo(v);
  return n === null ? LOI("#GIÁ TRỊ!") : n;
}

const HAM = {
  SUM:     a => a.reduce((s, v) => s + (typeof v === "number" ? v : 0), 0),
  AVERAGE: a => { const x = a.filter(v => typeof v === "number"); return x.length ? x.reduce((s, v) => s + v, 0) / x.length : LOI("#CHIA0!"); },
  COUNT:   a => a.filter(v => typeof v === "number").length,
  COUNTA:  a => a.filter(v => v !== "" && v !== null && v !== undefined).length,
  MIN:     a => { const x = a.filter(v => typeof v === "number"); return x.length ? Math.min(...x) : 0; },
  MAX:     a => { const x = a.filter(v => typeof v === "number"); return x.length ? Math.max(...x) : 0; },
  ROUND:   a => { const n = soHoa(a[0]); return laLoi(n) ? n : Math.round(n * 10 ** (a[1] || 0)) / 10 ** (a[1] || 0); },
  ABS:     a => Math.abs(soHoa(a[0])),
  LEN:     a => String(a[0] ?? "").length,
  LEFT:    a => String(a[0] ?? "").slice(0, a[1] ?? 1),
  RIGHT:   a => String(a[0] ?? "").slice(-(a[1] ?? 1)),
  MID:     a => String(a[0] ?? "").substr((a[1] || 1) - 1, a[2] ?? 1),
  CONCAT:  a => a.map(v => v ?? "").join(""),
  TODAY:   () => new Date().toLocaleDateString("vi-VN"),
  NOW:     () => new Date().toLocaleString("vi-VN"),
  IF:      a => (a[0] ? a[1] : a[2] ?? ""),
  IFERROR: a => (laLoi(a[0]) ? (a[1] ?? "") : a[0]),
  COUNTIF: (a, tho) => demTheoDieuKien(tho[0], tho[1]),
  SUMIF:   (a, tho) => tongTheoDieuKien(tho[0], tho[1], tho[2])
};
HAM.CONCATENATE = HAM.CONCAT;

function hopDieuKien(v, dk) {
  const s = String(dk ?? "");
  const m = /^(>=|<=|<>|>|<|=)(.*)$/.exec(s);
  if (!m) return String(v ?? "") === s;
  const n = parseFloat(m[2]), x = typeof v === "number" ? v : parseFloat(v);
  switch (m[1]) {
    case ">":  return x > n;   case "<":  return x < n;
    case ">=": return x >= n;  case "<=": return x <= n;
    case "<>": return String(v ?? "") !== m[2];
    default:   return String(v ?? "") === m[2];
  }
}
function demTheoDieuKien(vung, dk) {
  return (Array.isArray(vung) ? vung : [vung]).filter(v => hopDieuKien(v, dk)).length;
}
function tongTheoDieuKien(vung, dk, vungTong) {
  const a = Array.isArray(vung) ? vung : [vung];
  const b = Array.isArray(vungTong) ? vungTong : a;
  let s = 0;
  a.forEach((v, i) => { if (hopDieuKien(v, dk) && typeof b[i] === "number") s += b[i]; });
  return s;
}

/* Phân tích biểu thức */
function phanTich(bt, dangTinh) {
  let i = 0;
  const bo = () => { while (i < bt.length && bt[i] === " ") i++; };
  const xem = () => { bo(); return bt[i]; };

  function bieuThuc() { return soSanh(); }

  function soSanh() {
    let t = cong();
    for (;;) {
      bo();
      const hai = bt.substr(i, 2);
      if (hai === "<>" || hai === "<=" || hai === ">=") {
        i += 2; const p = cong();
        t = hai === "<>" ? String(t) !== String(p) : hai === "<=" ? soHoa(t) <= soHoa(p) : soHoa(t) >= soHoa(p);
      } else if (bt[i] === "=" || bt[i] === "<" || bt[i] === ">") {
        const d = bt[i]; i++; const p = cong();
        t = d === "=" ? String(t) === String(p) : d === "<" ? soHoa(t) < soHoa(p) : soHoa(t) > soHoa(p);
      } else return t;
    }
  }

  function cong() {
    let t = nhan();
    for (;;) {
      bo();
      if (bt[i] === "+" || bt[i] === "-") {
        const d = bt[i]; i++; const p = nhan();
        if (d === "+" && (typeof t === "string" || typeof p === "string") && isNaN(parseFloat(t)) && t !== "") {
          t = String(t) + String(p);
        } else {
          const a = soHoa(t), b = soHoa(p);
          if (laLoi(a)) return a; if (laLoi(b)) return b;
          t = d === "+" ? a + b : a - b;
        }
      } else return t;
    }
  }

  function nhan() {
    let t = luyThua();
    for (;;) {
      bo();
      if (bt[i] === "*" || bt[i] === "/") {
        const d = bt[i]; i++;
        const a = soHoa(t), b = soHoa(luyThua());
        if (laLoi(a)) return a; if (laLoi(b)) return b;
        if (d === "/" && b === 0) return LOI("#CHIA0!");
        t = d === "*" ? a * b : a / b;
      } else return t;
    }
  }

  function luyThua() {
    let t = donNguyen();
    bo();
    if (bt[i] === "^") { i++; const b = soHoa(luyThua()); const a = soHoa(t); t = a ** b; }
    return t;
  }

  function donNguyen() {
    bo();
    if (bt[i] === "-") { i++; const v = soHoa(donNguyen()); return laLoi(v) ? v : -v; }
    if (bt[i] === "+") { i++; return donNguyen(); }
    return goc();
  }

  function goc() {
    bo();
    if (bt[i] === "(") { i++; const v = bieuThuc(); bo(); if (bt[i] === ")") i++; return v; }
    if (bt[i] === '"') {
      i++; let s = "";
      while (i < bt.length && bt[i] !== '"') s += bt[i++];
      i++; return s;
    }
    /* Số */
    let m = /^\d+(\.\d+)?/.exec(bt.slice(i));
    if (m) { i += m[0].length; return parseFloat(m[0]); }
    /* Tên: hàm, vùng, ô, TRUE/FALSE */
    m = /^[A-Za-z_][A-Za-z0-9_.]*/.exec(bt.slice(i));
    if (!m) { i++; return LOI("#CÚ PHÁP!"); }
    const ten = m[0]; i += ten.length; bo();

    if (bt[i] === "(") {                       /* gọi hàm */
      i++;
      const tho = [], phang = [];
      if (xem() !== ")") {
        for (;;) {
          const v = bieuThuc();
          tho.push(v);
          Array.isArray(v) ? phang.push(...v) : phang.push(v);
          bo();
          if (bt[i] === "," || bt[i] === ";") { i++; continue; }
          break;
        }
      }
      bo(); if (bt[i] === ")") i++;
      const f = HAM[ten.toUpperCase()];
      if (!f) return LOI("#TÊN?");
      const kq = f(phang, tho);
      return kq === undefined ? "" : kq;
    }

    const hoa = ten.toUpperCase();
    if (hoa === "TRUE") return true;
    if (hoa === "FALSE") return false;

    /* Vùng A1:B5 */
    if (bt[i] === ":") {
      const sau = /^:([A-Za-z]+\d+)/.exec(bt.slice(i));
      if (sau) {
        i += sau[0].length;
        return docVung(ten, sau[1], dangTinh);
      }
    }
    /* Ô đơn */
    const o = tachDiaChi(ten);
    return o ? docO(o.d, o.c, dangTinh) : LOI("#TÊN?");
  }

  const kq = bieuThuc();
  return kq;
}

function docO(d, c, dangTinh) {
  const a = diaChi(d, c);
  if (dangTinh.has(a)) return LOI("#VÒNG LẶP!");
  const o = oTai(trangHien(), d, c);
  if (!o || o.v === undefined || o.v === "") return "";
  return tinhGiaTri(o.v, a, dangTinh);
}

function docVung(tu, den, dangTinh) {
  const a = tachDiaChi(tu), b = tachDiaChi(den);
  if (!a || !b) return LOI("#THAM CHIẾU!");
  const ra = [];
  for (let d = Math.min(a.d, b.d); d <= Math.max(a.d, b.d); d++)
    for (let c = Math.min(a.c, b.c); c <= Math.max(a.c, b.c); c++)
      ra.push(docO(d, c, dangTinh));
  return ra;
}

function tinhGiaTri(tho, a, dangTinh) {
  if (typeof tho !== "string" || tho[0] !== "=") {
    const n = thuSo(tho);
    return n === null ? tho : n;
  }
  dangTinh = dangTinh || new Set();
  if (a) dangTinh.add(a);
  let kq;
  try { kq = phanTich(tho.slice(1), dangTinh); }
  catch (e) { kq = LOI("#CÚ PHÁP!"); }
  if (a) dangTinh.delete(a);
  return kq;
}

function giaTriO(d, c) {
  const o = oTai(trangHien(), d, c);
  if (!o || o.v === undefined) return "";
  return tinhGiaTri(o.v, diaChi(d, c), new Set());
}

/* ── Định dạng hiển thị ───────────────────────────────────────── */
function hienThi(v, dd) {
  if (laLoi(v)) return v.loi;
  if (v === "" || v === null || v === undefined) return "";
  if (typeof v === "boolean") return v ? "ĐÚNG" : "SAI";
  const so = typeof v === "number";
  switch (dd) {
    case "so":  return so ? v.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : String(v);
    case "pt":  return so ? (v * 100).toLocaleString("vi-VN", { maximumFractionDigits: 2 }) + "%" : String(v);
    case "vnd": return so ? v.toLocaleString("vi-VN", { maximumFractionDigits: 0 }) + " ₫" : String(v);
    case "usd": return so ? "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : String(v);
    case "van": return String(v);
    default:    return so ? v.toLocaleString("vi-VN", { maximumFractionDigits: 4 }) : String(v);
  }
}

/* ══ VẼ LƯỚI ═══════════════════════════════════════════════════ */

function ve() {
  const t = trangHien();
  const bang = document.getElementById("bt-luoi");
  const dau = ["<thead><tr><th class=\"bt-goc\"></th>"];
  for (let c = 0; c < SO_COT; c++) dau.push(`<th data-cot="${c}" style="width:118px">${tenCot(c)}</th>`);
  dau.push("</tr></thead><tbody>");

  for (let d = 0; d < t.dong; d++) {
    dau.push(`<tr><th data-dong="${d}">${d + 1}</th>`);
    for (let c = 0; c < SO_COT; c++) {
      const o = oTai(t, d, c) || {};
      const s = o.s || {};
      const v = giaTriO(d, c);
      const chu = hienThi(v, s.dd);
      const lop = ["bt-o-td"];
      if (typeof v === "number") lop.push("bt-so");
      if (laLoi(v)) lop.push("bt-loi");
      if (s.cc) lop.push("bt-" + s.cc);
      if (s.cx) lop.push("bt-xuong-dong");
      if (typeof o.v === "string" && o.v[0] === "=") lop.push("bt-ct-goc");
      if (khoaO(t, d, c)) lop.push("bt-khoa");
      const kieu = [];
      if (s.mn) kieu.push(`background:${s.mn}`);
      if (s.mc) kieu.push(`color:${s.mc}`);
      if (s.d) kieu.push("font-weight:700");
      if (s.n) kieu.push("font-style:italic");
      if (s.g || s.ng) kieu.push(`text-decoration:${[s.g && "underline", s.ng && "line-through"].filter(Boolean).join(" ")}`);
      if (s.cs) kieu.push(`font-size:${s.cs}px`);
      dau.push(`<td class="${lop.join(" ")}" data-d="${d}" data-c="${c}"${kieu.length ? ` style="${kieu.join(";")}"` : ""}><span class="bt-o">${
        String(chu).replace(/&/g, "&amp;").replace(/</g, "&lt;")}</span></td>`);
    }
    dau.push("</tr>");
  }
  dau.push("</tbody>");
  bang.innerHTML = dau.join("");
  toSang();
  veTabs();
}

function vungChon() {
  return {
    d1: Math.min(hienTai.d, neo.d), d2: Math.max(hienTai.d, neo.d),
    c1: Math.min(hienTai.c, neo.c), c2: Math.max(hienTai.c, neo.c)
  };
}

function toSang() {
  const v = vungChon();
  document.querySelectorAll("#bt-luoi td").forEach(td => {
    const d = +td.dataset.d, c = +td.dataset.c;
    td.classList.toggle("bt-trong-vung", d >= v.d1 && d <= v.d2 && c >= v.c1 && c <= v.c2);
    td.classList.toggle("bt-hien-tai", d === hienTai.d && c === hienTai.c);
  });
  document.querySelectorAll("#bt-luoi thead th[data-cot]").forEach(th =>
    th.classList.toggle("dang-chon", +th.dataset.cot >= v.c1 && +th.dataset.cot <= v.c2));
  document.querySelectorAll("#bt-luoi tbody th[data-dong]").forEach(th =>
    th.classList.toggle("dang-chon", +th.dataset.dong >= v.d1 && +th.dataset.dong <= v.d2));

  const o = oTai(trangHien(), hienTai.d, hienTai.c);
  document.getElementById("bt-o-hien-tai").value = diaChi(hienTai.d, hienTai.c);
  document.getElementById("bt-cong-thuc").value = o && o.v !== undefined ? o.v : "";
  capNhatThongKe();
  capNhatNutDinhDang();
}

function capNhatThongKe() {
  const v = vungChon(), so = [];
  let dem = 0;
  for (let d = v.d1; d <= v.d2; d++) for (let c = v.c1; c <= v.c2; c++) {
    const g = giaTriO(d, c);
    if (g !== "" && !laLoi(g)) dem++;
    if (typeof g === "number") so.push(g);
  }
  const tong = so.reduce((s, x) => s + x, 0);
  const tb = so.length ? tong / so.length : 0;
  document.getElementById("bt-thong-ke").innerHTML =
    `<span>Đếm <b>${dem}</b></span>` +
    (so.length ? `<span>Tổng <b>${tong.toLocaleString("vi-VN", { maximumFractionDigits: 2 })}</b></span>
                  <span>Trung bình <b>${tb.toLocaleString("vi-VN", { maximumFractionDigits: 2 })}</b></span>` : "");
}

function capNhatNutDinhDang() {
  const s = (oTai(trangHien(), hienTai.d, hienTai.c) || {}).s || {};
  [["bt-dam", "d"], ["bt-nghieng", "n"], ["bt-gach", "g"], ["bt-xoa-ngang", "ng"], ["bt-xuong-dong", "cx"]]
    .forEach(([id, k]) => document.getElementById(id).setAttribute("aria-pressed", String(!!s[k])));
  document.getElementById("bt-dinh-dang").value = s.dd || "";
  document.getElementById("bt-co-chu").value = s.cs || "";
}

/* ── Tab trang tính ── */
function veTabs() {
  document.getElementById("bt-tabs").innerHTML = TL.trang.map((t, i) =>
    `<button class="bt-tab" data-trang="${i}" aria-selected="${i === TL.hien}">${
      String(t.ten).replace(/</g, "&lt;")}${t.nguon ? " ⛓" : ""}</button>`).join("");
  const t = trangHien();
  const bao = document.getElementById("bt-bao-nguon");
  if (t.nguon) {
    bao.hidden = false;
    bao.querySelector(".bt-nguon-ten").textContent = t.nguon;
    bao.querySelector(".bt-nguon-cot").textContent = `A–${tenCot((t.cot_khoa || 1) - 1)}`;
  } else bao.hidden = true;
}

/* ══ SỬA Ô ═════════════════════════════════════════════════════ */

let dangSua = false;

function moSua(chuDau) {
  const t = trangHien();
  if (khoaO(t, hienTai.d, hienTai.c)) {
    nhac("Cột này lấy từ bảng " + t.nguon + ", chỉ đọc. Tính toán ở cột bên phải.");
    return;
  }
  const td = document.querySelector(`#bt-luoi td[data-d="${hienTai.d}"][data-c="${hienTai.c}"]`);
  if (!td) return;
  const nhap = document.getElementById("bt-o-nhap");
  const hop = document.getElementById("bt-luoi-hop");
  const r = td.getBoundingClientRect(), rh = hop.getBoundingClientRect();
  nhap.style.display = "block";
  nhap.style.left = (r.left - rh.left + hop.scrollLeft) + "px";
  nhap.style.top = (r.top - rh.top + hop.scrollTop) + "px";
  nhap.style.width = Math.max(r.width, 90) + "px";
  nhap.style.height = r.height + "px";
  const o = oTai(t, hienTai.d, hienTai.c);
  nhap.value = chuDau !== undefined ? chuDau : (o && o.v !== undefined ? o.v : "");
  dangSua = true;
  nhap.focus();
  if (chuDau === undefined) nhap.select();
}

function dongSua(luu) {
  const nhap = document.getElementById("bt-o-nhap");
  if (!dangSua) return;
  dangSua = false;
  nhap.style.display = "none";
  if (luu) {
    ghiNho();
    datO(trangHien(), hienTai.d, hienTai.c, nhap.value);
    ve(); danhDauChuaLuu();
  }
  document.getElementById("bt-luoi-hop").focus();
}

function chuyenO(dd, dc, giuChon) {
  const t = trangHien();
  hienTai.d = Math.max(0, Math.min(t.dong - 1, hienTai.d + dd));
  hienTai.c = Math.max(0, Math.min(SO_COT - 1, hienTai.c + dc));
  if (!giuChon) neo = { ...hienTai };
  toSang();
  document.querySelector(`#bt-luoi td[data-d="${hienTai.d}"][data-c="${hienTai.c}"]`)
    ?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

/* ── Áp định dạng cho vùng chọn ── */
function apDinhDang(sua) {
  ghiNho();
  const t = trangHien(), v = vungChon();
  for (let d = v.d1; d <= v.d2; d++) for (let c = v.c1; c <= v.c2; c++) {
    const a = diaChi(d, c);
    t.o[a] = t.o[a] || {};
    t.o[a].s = t.o[a].s || {};
    sua(t.o[a].s);
    if (!Object.keys(t.o[a].s).length) delete t.o[a].s;
    if (!t.o[a].s && t.o[a].v === undefined) delete t.o[a];
  }
  ve(); danhDauChuaLuu();
}

function xoaNoiDung() {
  ghiNho();
  const t = trangHien(), v = vungChon();
  for (let d = v.d1; d <= v.d2; d++) for (let c = v.c1; c <= v.c2; c++)
    if (!khoaO(t, d, c)) datO(t, d, c, "");
  ve(); danhDauChuaLuu();
}

/* ── Trạng thái lưu ── */
let hetGioLuu = null;
function danhDauChuaLuu() {
  const el = document.getElementById("bt-trang-thai");
  el.textContent = "Chưa lưu"; el.classList.add("chua-luu");
  clearTimeout(hetGioLuu);
  hetGioLuu = setTimeout(() => {
    el.textContent = "Đã lưu " + new Date().toLocaleTimeString("vi-VN");
    el.classList.remove("chua-luu");
    try { localStorage.setItem("knjsc-bang-tinh", JSON.stringify(TL)); } catch (e) {}
  }, 900);
}

function nhac(loi) {
  let el = document.getElementById("bt-nhac");
  if (!el) {
    el = document.createElement("div");
    el.id = "bt-nhac";
    el.style.cssText = "position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:80;" +
      "background:var(--ink);color:var(--plane);padding:9px 14px;border-radius:3px;font-size:13px;" +
      "box-shadow:0 4px 14px rgba(0,0,0,.25);max-width:min(90vw,420px)";
    document.body.appendChild(el);
  }
  el.textContent = loi;
  el.style.opacity = "1";
  clearTimeout(el._h);
  el._h = setTimeout(() => { el.style.opacity = "0"; }, 2600);
}

/* ══ XUẤT CSV ══════════════════════════════════════════════════ */
function xuatCsv() {
  const t = trangHien();
  const dong = [];
  for (let d = 0; d < t.dong; d++) {
    const hang = [];
    let coGi = false;
    for (let c = 0; c < SO_COT; c++) {
      const v = giaTriO(d, c);
      const s = laLoi(v) ? v.loi : String(v ?? "");
      if (s !== "") coGi = true;
      hang.push(/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
    }
    if (coGi) dong.push(hang.join(","));
  }
  const blob = new Blob(["﻿" + dong.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${TL.ten} - ${t.ten}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
  nhac("Bản thật sẽ xuất .xlsx bằng openpyxl và ghi vào nhật ký.");
}
