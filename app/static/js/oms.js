/* KN OMS — bản demo dữ liệu giả trong KN CRM, chỉ Admin (ADR-051).
   Mọi số liệu sinh ngay trong trình duyệt từ hạt giống cố định; trang không gọi máy chủ. Sáu màn — Báo đơn, Công nợ &
   đối soát, Khách rủi ro, Kho, Kênh bán & Page, Lãi theo page — mỗi màn một địa chỉ riêng (#bao-don, #cong-no…).
   Nền dùng chung khoá knjsc-nen với KN CRM. */
(function () {
'use strict';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const h = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const MIN = 6e4, HOUR = 36e5, DAY = 864e5;
const nghi = ms => new Promise(r => setTimeout(r, ms));
// Độ trễ giả lập, một chỗ duy nhất (mili giây)
const TRE = {hoiHang: 150, ketNoi: 1500, themKenh: 1800};

// Dòng số ngẫu nhiên có hạt giống (mulberry32): "Đặt lại demo" ra lại đúng bộ dữ liệu ban đầu.
function taoRng(a) {
  return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
let R = taoRng(1);
// Chạy fn trên một dòng số riêng rồi trả lại dòng chính — dữ liệu thêm sau không làm lệch dữ liệu sinh trước nó.
function voi(rng, fn) { const cu = R; R = rng; try { return fn(); } finally { R = cu; } }
const rnd = (a, b) => a + Math.floor(R() * (b - a + 1));
const pick = a => a[Math.floor(R() * a.length)];
const chance = p => R() < p;
function weighted(ds) { let x = R() * ds.reduce((s, [, w]) => s + w, 0); for (const [v, w] of ds) if ((x -= w) < 0) return v; return ds[ds.length - 1][0]; }
const digits = n => Array.from({length: n}, () => rnd(0, 9)).join('');
const alnum = n => Array.from({length: n}, () => '0123456789ABCDEFGHJKLMNPRSTUVWXY'[rnd(0, 31)]).join('');
const boDau = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D');

// Giờ hiển thị theo giờ Việt Nam, ngày DD/MM/YYYY như KN CRM.
const dtf = new Intl.DateTimeFormat('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
function ngayGio(t) { const p = {}; for (const x of dtf.formatToParts(new Date(t))) p[x.type] = x.value; return `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}`; }
const ngay = t => ngayGio(t).slice(0, 10);
const gio = t => ngayGio(t).slice(11);
const ngayNgan = t => ngayGio(t).slice(0, 5) + ' ' + gio(t);
const mmdd = t => { const s = ngay(t); return s.slice(3, 5) + s.slice(0, 2); };
// Ngày lịch Việt Nam dạng ISO (YYYY-MM-DD): so sánh được như chuỗi, khớp .value của ô ngày; đầu ngày là 00:00 giờ VN
const isoNgay = t => { const s = ngay(t); return `${s.slice(6)}-${s.slice(3, 5)}-${s.slice(0, 2)}`; };
const dauNgay = t => Math.floor((t + 7 * HOUR) / DAY) * DAY - 7 * HOUR;
function truoc(t) { const d = Date.now() - t; if (d < MIN) return 'vừa xong'; if (d < HOUR) return Math.floor(d / MIN) + ' phút trước'; if (d < DAY) return Math.floor(d / HOUR) + ' giờ trước'; return Math.floor(d / DAY) + ' ngày trước'; }
const nfSo = new Intl.NumberFormat('vi-VN'), nf1 = new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 1});
const so = n => nfSo.format(n);
const phanTram = x => (x < 0 ? '−' : '') + nf1.format(Math.abs(x) * 100) + '%';
// Tiền giữ theo đơn vị nhỏ nhất, mỗi số đi kèm loại tiền; không cộng lẫn hai loại tiền.
const DEC = {USD: 2, CAD: 2, EUR: 2, AUD: 2, PHP: 0, JPY: 0, KRW: 0};
const nfTien = {0: new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 0}), 2: new Intl.NumberFormat('vi-VN', {minimumFractionDigits: 2, maximumFractionDigits: 2})};
const tien = (minor, cur) => nfTien[DEC[cur]].format(minor / 10 ** DEC[cur]) + ' ' + cur;
// Làm tròn theo đơn vị thường dùng của loại tiền (PHP chục, JPY trăm, KRW nghìn)
const lamTron = (minor, cur) => { const b = {PHP: 10, JPY: 100, KRW: 1000}[cur] || 1; return Math.round(minor / b) * b; };
// Cộng theo từng loại tiền — mỗi loại một tổng riêng
function tongTheoTien(ds, f) { const m = {}; for (const d of ds) { const v = f(d); if (v) m[d.cur] = (m[d.cur] || 0) + v; } return m; }
const chuoiTien = m => Object.keys(DEC).filter(c => m[c]).map(c => tien(m[c], c)).join(' · ');
const chipTien = m => Object.keys(DEC).filter(c => m[c]).map(c => `<span class="tien-o">${tien(m[c], c)}</span>`).join('');
// Tiền Việt của màn Lãi theo page: dấu trừ thật (−) cho số âm
const vnd = n => (n < 0 ? '−' : '') + so(Math.abs(Math.round(n))) + ' ₫';
function vndGon(n) {
  const a = Math.abs(n), dau = n < 0 ? '−' : '';
  if (a >= 1e9) return dau + nf1.format(a / 1e9) + ' tỉ ₫';
  if (a >= 1e6) return dau + nf1.format(a / 1e6) + ' tr ₫';
  return dau + so(Math.round(a)) + ' ₫';
}
// Đọc số tiền người dùng gõ — cùng quy tắc với core.money.parse_money: chấm ngăn nghìn, phẩy thập phân; một dấu chấm
// đứng một mình với một hai chữ số sau nó là dấu thập phân. Trả đơn vị nhỏ nhất; null khi trống, NaN khi không đọc được.
function docTien(text, cur) {
  let s = String(text).replace(/[\s ]/g, '');
  if (!s) return null;
  if (!/^\d[\d.,]*$/.test(s)) return NaN;
  const cham = s.includes('.'), phay = s.includes(',');
  if (cham && phay) s = s.lastIndexOf(',') > s.lastIndexOf('.') ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  else if (phay) { if (s.split(',').length > 2) return NaN; s = s.replace(',', '.'); }
  else if (cham) { const p = s.split('.'); if (!(p.length === 2 && p[1].length <= 2)) s = s.replace(/\./g, ''); }
  if (!/^\d+(\.\d+)?$/.test(s)) return NaN;
  const [nguyen, le = ''] = s.split('.'), dec = DEC[cur];
  if (le.length > dec) return NaN;
  return Number(nguyen) * 10 ** dec + Number((le + '00').slice(0, dec) || 0);
}

const ICON = {
  dongBo: '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.6-4.4M4 13a8 8 0 0 0 14.6 4.4"/><path d="M5 3v4h4M19 21v-4h-4"/></svg>',
  dong: '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  tai: '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
};

// ---------- Danh mục ----------
const MARKETS = {
  US: {ten: 'Hoa Kỳ', cur: 'USD', k: 1, cities: ['Houston, TX', 'San Jose, CA', 'Garden Grove, CA', 'Seattle, WA', 'Atlanta, GA', 'Philadelphia, PA']},
  CA: {ten: 'Canada', cur: 'CAD', k: 1.35, cities: ['Toronto, ON', 'Montréal, QC', 'Calgary, AB', 'Vancouver, BC']},
  PH: {ten: 'Philippines', cur: 'PHP', k: 56, cities: ['Quezon City', 'Cebu City', 'Davao City', 'Makati']},
  EU: {ten: 'Châu Âu', cur: 'EUR', k: 0.92, cities: ['Berlin', 'Hamburg', 'München', 'Frankfurt']},
  KR: {ten: 'Hàn Quốc', cur: 'KRW', k: 1350, cities: ['Seoul', 'Busan', 'Ansan']},
  JP: {ten: 'Nhật Bản', cur: 'JPY', k: 150, cities: ['Tokyo', 'Osaka', 'Nagoya']},
  AU: {ten: 'Úc', cur: 'AUD', k: 1.5, cities: ['Sydney, NSW', 'Melbourne, VIC', 'Brisbane, QLD']},
};
const SP = [
  {ma: 'RC-01', ten: 'Retinol Cream', usd: 39, w: 16},
  {ma: 'RS-02', ten: 'Retinol Serum', usd: 45, w: 14},
  {ma: 'VCC-03', ten: 'Vitamin C Cream', usd: 35, w: 9},
  {ma: 'VCS-04', ten: 'Vitamin C Serum', usd: 42, w: 13},
  {ma: 'KCN-05', ten: 'Kem Chống Nắng', usd: 29, w: 12},
  {ma: 'SRM-06', ten: 'Sữa Rửa Mặt', usd: 19, w: 10},
  {ma: 'RES-07', ten: 'Retinol Eye Serum', usd: 49, w: 8},
  {ma: 'HM-200', ten: 'Máy massage cầm tay HM-200', usd: 89, w: 5},
  {ma: 'DN-09', ten: 'Đèn ngủ cảm ứng', usd: 25, w: 4},
];
const SPMAP = Object.fromEntries(SP.map(s => [s.ma, s]));
function giaBan(usd, cur, k) {
  const v = usd * k;
  if (DEC[cur] === 2) return Math.round(v) * 100 - 1;
  if (cur === 'PHP') return Math.ceil(v / 100) * 100 - 10;
  if (cur === 'JPY') return Math.ceil(v / 100) * 100;
  return Math.ceil(v / 1000) * 1000;
}
const KHO = {
  HN: {ten: 'Kho tổng Hà Nội', ngan: 'HN'},
  US: {ten: 'Kho US — California', ngan: 'US'},
  PH: {ten: 'Kho PH — Manila', ngan: 'PH'},
};
const HANG = {
  'DHL Express': () => digits(10),
  'FedEx': () => digits(12),
  'UPS': () => '1Z' + alnum(6) + digits(10),
  'EMS (VNPost)': () => 'EE' + digits(9) + 'VN',
  'USPS': () => '9400' + digits(18),
  'J&T Express': () => 'JT' + digits(10),
  'LBC': () => digits(12),
  'Ninja Van': () => 'NVPH' + alnum(9),
};
function hangCho(wh) {
  if (wh === 'US') return weighted([['USPS', 7], ['UPS', 3]]);
  if (wh === 'PH') return weighted([['J&T Express', 5], ['LBC', 3], ['Ninja Van', 2]]);
  return weighted([['DHL Express', 4], ['FedEx', 3], ['UPS', 2], ['EMS (VNPost)', 3]]);
}
const NEN = {
  fb: {ten: 'Facebook Page', mau: 'var(--p-fb)'},
  tt: {ten: 'TikTok Shop', mau: 'var(--p-tt)'},
  sp: {ten: 'Shopee', mau: 'var(--p-sp)'},
  lz: {ten: 'Lazada', mau: 'var(--p-lz)'},
  web: {ten: 'Website', mau: 'var(--p-web)'},
};
const KENH_GOC = [
  {id: 'fb-us', nen: 'fb', ten: 'KN Beauty US', mkt: 'US', pt: 'ANHPM', w: 20},
  {id: 'fb-ca', nen: 'fb', ten: 'KN Skincare Canada', mkt: 'CA', pt: 'NAMVH', w: 14},
  {id: 'fb-ph', nen: 'fb', ten: 'KN Beauty Philippines', mkt: 'PH', pt: 'ANHPM', w: 8},
  {id: 'fb-jp', nen: 'fb', ten: 'KN Beauty Japan', mkt: 'JP', pt: 'TRANGDT', w: 5, trang: 'loi', loi: 'Pancake báo token Facebook hết hạn từ 2 ngày trước — đơn của page này đang không về CRM.'},
  {id: 'fb-kr', nen: 'fb', ten: 'KN Beauty Korea', mkt: 'KR', pt: 'TRANGDT', w: 5},
  {id: 'fb-au', nen: 'fb', ten: 'KN Beauty Australia', mkt: 'AU', pt: 'NAMVH', w: 7},
  {id: 'tt-us', nen: 'tt', ten: 'KN Beauty Official US', mkt: 'US', pt: 'ANHPM', w: 12},
  {id: 'tt-ph', nen: 'tt', ten: 'KN Beauty PH', mkt: 'PH', pt: 'NAMVH', w: 8},
  {id: 'sp-ph', nen: 'sp', ten: 'KN Beauty Mall', mkt: 'PH', pt: 'TRANGDT', w: 9},
  {id: 'lz-ph', nen: 'lz', ten: 'KN Beauty LazMall', mkt: 'PH', pt: 'TRANGDT', w: 6},
  {id: 'web-eu', nen: 'web', ten: 'Cửa hàng web EU', mkt: 'EU', pt: 'NAMVH', w: 6},
];
const SALE = ['HANT', 'HANGLT', 'DUNGTV', 'ANHPQ'];
const CSKH = ['LANPT', 'THUNM'];
const VANDON = ['TUHV', 'CHIBK'];
const MKT = ['ANHPM', 'NAMVH', 'TRANGDT'];
const HO_VN = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Ngô'];
const DEM_VN = ['Thị', 'Ngọc', 'Thu', 'Minh', 'Thanh', 'Kim', 'Bảo', 'Hồng'];
const TEN_VN = ['Lan', 'Hương', 'Thảo', 'Trang', 'Linh', 'Mai', 'Hạnh', 'Vy', 'Ngân', 'Phương', 'Hà', 'Yến', 'Tâm', 'Thư'];
const TEN_DP = {
  US: ['Emily Johnson', 'Sarah Miller', 'Jessica Brown', 'Ashley Davis', 'Michelle Wilson', 'Amanda Taylor', 'Linda Carter'],
  CA: ['Olivia Martin', 'Chloe Tremblay', 'Sophie Roy', 'Emma Wilson', 'Hannah Clark', 'Grace Gagnon'],
  AU: ['Megan Walker', 'Rachel Young', 'Laura Hall', 'Jessica White', 'Kate Thompson'],
  EU: ['Anna Müller', 'Lena Schmidt', 'Sophie Wagner', 'Laura Becker', 'Marie Hoffmann'],
  PH: ['Maria Santos', 'Ana Reyes', 'Kristine Cruz', 'Jasmine Bautista', 'Angelica Garcia', 'Rowena Mendoza', 'Liza Ramos', 'Joy Villanueva'],
  JP: ['Sato Yuki', 'Suzuki Aiko', 'Takahashi Mei', 'Tanaka Haruka', 'Watanabe Rina'],
  KR: ['Kim Ji-yeon', 'Lee Soo-min', 'Park Hye-jin', 'Choi Yu-na', 'Jung Min-ji'],
};
function tenKhach(m) { return chance(m === 'PH' || m === 'EU' ? 0.25 : 0.6) ? `${pick(HO_VN)} ${pick(DEM_VN)} ${pick(TEN_VN)}` : pick(TEN_DP[m]); }
function sdt(m) {
  const c = digits(2);
  switch (m) {
    case 'US': return `+1 (${rnd(201, 989)}) •••-••${c}`;
    case 'CA': return `+1 (${pick([416, 514, 403, 604, 647])}) •••-••${c}`;
    case 'PH': return `+63 9${digits(2)} ••• ••${c}`;
    case 'EU': return `+49 15${rnd(1, 9)} •••• ••${c}`;
    case 'KR': return `+82 10-••••-••${c}`;
    case 'JP': return `+81 90-••••-••${c}`;
    default: return `+61 4${digits(2)} ••• •${c}`;
  }
}

// Tám trạng thái vận đơn đang dùng ở KN CRM; hành trình của hãng đổi về đúng tám nhãn này.
const TT = ['Đã lên đơn', 'Đang giao', 'Khách vắng', 'Hẹn lại', 'Đã nhận hàng', 'Hoàn đơn', 'Hủy sau giao', 'Hủy trước giao'];
// Nhãn trạng thái là .chip của KN CRM; chip-tin (xanh dương) do oms.css thêm
const TT_LOP = {'Đã lên đơn': 'chip-nhat', 'Đang giao': 'chip-tin', 'Khách vắng': 'chip-lo', 'Hẹn lại': 'chip-cho', 'Đã nhận hàng': 'chip-tot', 'Hoàn đơn': 'chip-xau', 'Hủy sau giao': 'chip-xau', 'Hủy trước giao': 'chip-nhat'};
const NHOM = {goi: ['Khách vắng', 'Hẹn lại'], hoan: ['Hoàn đơn', 'Hủy sau giao']};
const KET_THUC = new Set(['xong', 'huy', 'daHoan']);
const CHANG = {
  qt: m => ['Đã xuất khẩu — rời Việt Nam', `Đến ${MARKETS[m].ten} — chờ thông quan`, 'Đã thông quan', 'Đang phát'],
  nd: () => ['Đang trung chuyển', 'Đang phát'],
};
const badge = t => `<span class="chip ${TT_LOP[t]}"><i></i>${h(t)}</span>`;
const nenChip = k => `<span class="nen" style="--c:${NEN[k.nen].mau}"><i></i>${NEN[k.nen].ten}</span>`;

// Thanh toán: đúng bảy phương thức, ba trạng thái và nhãn đối soát của bảng Vận đơn (orders/constants.py)
const PTTT = ['Zelle', 'PayPal', 'Visa/Website', 'Cheque', 'Western Union', 'RIA', 'Money Gram'];
const PTTT_THEO_TT = {
  US: [['Zelle', 6], ['PayPal', 2], ['Cheque', 1], ['Money Gram', 1]],
  PH: [['RIA', 3], ['Western Union', 3], ['Money Gram', 2], ['PayPal', 1]],
  khac: [['PayPal', 4], ['Western Union', 2], ['RIA', 1], ['Money Gram', 1]],
};
const TT_TIEN = {CHUA: 'Chưa thanh toán', MOT: 'Thanh toán 1 phần', DU: 'Đã thanh toán'};
const TT_TIEN_LOP = {[TT_TIEN.CHUA]: 'chip-cho', [TT_TIEN.MOT]: 'chip-tin', [TT_TIEN.DU]: 'chip-tot'};
// Nguồn tiền theo nền tảng: page Facebook khách trả sau (phải thu), sàn thu hộ, website trả trước qua thẻ
const NGUON = {fb: 'khach', web: 'web', tt: 'san', sp: 'san', lz: 'san'};
// Số minh hoạ cho Lãi theo page, chưa chốt: phí sàn, giá vốn (₫ một sản phẩm), cước (₫ một đơn theo tuyến và thị trường)
const PHI_SAN = {tt: 0.08, sp: 0.09, lz: 0.10};
const GIA_VON = {'RC-01': 180000, 'RS-02': 210000, 'VCC-03': 160000, 'VCS-04': 195000, 'KCN-05': 120000, 'SRM-06': 85000, 'RES-07': 230000, 'HM-200': 650000, 'DN-09': 140000};
const CUOC = {qt: {US: 420000, CA: 450000, PH: 260000, EU: 480000, KR: 300000, JP: 320000, AU: 440000}, nd: {US: 160000, PH: 60000}};
// Tỉ giá tạm khởi đầu = settings.EXCHANGE_RATES_VND (knjsc/settings/base.py); KRW cố ý chưa có, như ở đó.
const TI_GIA_MAC_DINH = {USD: 25500, CAD: 17500, PHP: 440, EUR: 28500, JPY: 155, AUD: 17000};
const TI_GIA_CO = ['USD', 'CAD', 'EUR', 'AUD', 'PHP', 'JPY', 'KRW'];
// Số ngày tiền quảng cáo giả — kỳ dài nhất của màn Lãi theo page
const KY_QC = 30;
// Khách mẫu cố định của màn Khách rủi ro. Số Bắc Mỹ dải 555-01xx là số giả theo quy ước, không thuộc ai.
const KHACH_MAU = [
  {mau: 'tot', id: 'KH-90001', ten: 'Trần Diệu Linh', mkt: 'US', kenh: 'fb-us', wh: 'US', city: 'San Jose, CA', so: '14085550142',
    don: [64, 41, 23, 11].map(truoc => ({truoc, ep: ['giao'], tien: {pttt: 'Zelle', tra: 'du'}}))},
  {mau: 'hoan', id: 'KH-90002', ten: 'Phạm Khánh Hân', mkt: 'CA', kenh: 'fb-ca', wh: 'HN', city: 'Toronto, ON', so: '16475550117',
    don: [{truoc: 52, ep: ['giao'], tien: {pttt: 'PayPal', tra: 'du'}}, {truoc: 30, ep: ['hoan'], tien: {pttt: 'PayPal', tra: 'chua'}},
      {truoc: 8, ep: ['vang', 'hoan'], tien: {pttt: 'PayPal', tra: 'chua'}}]},
  {mau: 'no', id: 'KH-90003', ten: 'Lê Phương Thảo', mkt: 'US', kenh: 'fb-us', wh: 'US', city: 'Houston, TX', so: '17135550163',
    don: [{truoc: 38, ep: ['giao'], tien: {pttt: 'Zelle', tra: 'du'}}, {truoc: 19, ep: ['giao'], tien: {pttt: 'Zelle', tra: 'chua', nhac: 1}}]},
];
const SDT_MOI = '12125550199';
const TEN_MAU = {tot: 'Khách tốt', hoan: 'Khách hoàn 2 lần', no: 'Khách còn nợ', moi: 'SĐT mới'};
// Đơn page cũ (giao 16–58 ngày trước) để đủ bốn nhóm tuổi nợ — dữ liệu chính chỉ trải 21 ngày
const NO_CU = [
  {truoc: 16, kenh: 'fb-us', tra: 'du', veTk: false}, {truoc: 18, kenh: 'fb-ca', tra: 'chua'}, {truoc: 21, kenh: 'fb-ph', tra: 'du'},
  {truoc: 24, kenh: 'fb-au', tra: 'mot'}, {truoc: 27, kenh: 'fb-us', tra: 'chua'}, {truoc: 33, kenh: 'fb-kr', tra: 'du'},
  {truoc: 36, kenh: 'fb-ca', tra: 'chua'}, {truoc: 41, kenh: 'fb-us', tra: 'du'}, {truoc: 47, kenh: 'fb-ph', tra: 'chua'},
  {truoc: 58, kenh: 'fb-au', tra: 'du'},
];
const MUC_NHAN = {cao: 'Cao', 'chu-y': 'Cần chú ý', thap: 'Thấp'};

let S;
const kenhTheoId = id => S.kenh.find(k => k.id === id);
function cuoi(d, chiHang) { for (let i = d.sk.length - 1; i >= 0; i--) if (!chiHang || !d.sk[i].noiBo) return d.sk[i]; return d.sk[0]; }
const laTac = d => !KET_THUC.has(d.pha) && d.pha !== 'hen' && Date.now() - cuoi(d, true).t > S.bd.nguong * DAY;
const soNgayIm = d => Math.floor((Date.now() - cuoi(d, true).t) / DAY);
const maPhieu = (p, t, n) => `${p}-${mmdd(t)}-${String(n).padStart(2, '0')}`;
// Công nợ: chỉ đơn page Facebook đã giao mới là tiền khách nợ
const laPhaiThu = d => d.nguon === 'khach' && d.tt === 'Đã nhận hàng';
const conLai = d => Math.max(0, d.tong - (d.tien ? d.tien.daThu : 0));
const tuoiNo = d => Math.floor((Date.now() - d.nhanLuc) / DAY);
const nhomTuoi = n => n <= 7 ? '0-7' : n <= 14 ? '8-14' : n <= 30 ? '15-30' : '>30';
const cuocDon = d => (CUOC[d.route] || {})[d.mkt] || CUOC.qt[d.mkt] || 300000;
const giaVon = d => d.items.reduce((s, i) => s + i.sl * GIA_VON[i.ma], 0);

// ---------- Dữ liệu giả ----------
function maDon(t) { const k = mmdd(t); S.seqNgay[k] = (S.seqNgay[k] || 0) + 1; return `DH-${k}-${String(S.seqNgay[k]).padStart(4, '0')}`; }
// o (tuỳ chọn) chỉ dùng cho đơn mẫu: kh — khách định sẵn, wh — kho xuất, ep — kết cục định sẵn của hãng
function taoDon(t0, kenh, o) {
  const m = kenh.mkt, M = MARKETS[m];
  let kh = o && o.kh ? o.kh : null;
  if (!kh) {
    const cu = S.khach.filter(k => k.mkt === m && k.dau < t0 && !k.mau);
    if (cu.length && chance(0.22)) kh = pick(cu);
    else {
      kh = {id: 'KH-' + String(++S.demKhach).padStart(5, '0'), ten: tenKhach(m), sdt: sdt(m), mkt: m, kenhDau: kenh.id, dau: t0, city: pick(M.cities), sdtSo: '', mau: '', danhDau: '', lyDoChan: '', su: []};
      S.khach.push(kh); S.khMap[kh.id] = kh;
    }
  }
  const items = [], dung = new Set();
  for (let n = weighted([[1, 6], [2, 3], [3, 1]]); items.length < n;) {
    const sp = weighted(SP.map(s => [s, s.w]));
    if (dung.has(sp.ma)) continue;
    dung.add(sp.ma);
    items.push({ma: sp.ma, sl: weighted([[1, 6], [2, 3], [3, 1]]), gia: giaBan(sp.usd, M.cur, M.k)});
  }
  const wh = o && o.wh ? o.wh : m === 'US' ? (chance(0.55) ? 'US' : 'HN') : m === 'PH' ? (chance(0.6) ? 'PH' : 'HN') : 'HN';
  const hang = hangCho(wh);
  const d = {id: maDon(t0), pck: 'PCK-' + (++S.demPck), kenh: kenh.id, mkt: m, cur: M.cur, kh: kh.id, items,
    tong: items.reduce((s, x) => s + x.sl * x.gia, 0), wh, hang, trk: HANG[hang](), route: wh === 'HN' ? 'qt' : 'nd',
    pha: 'tao', buoc: 0, tt: 'Đã lên đơn', sk: [], tao: t0, nt: ngay(t0), ntIso: isoNgay(t0), giao: null, sale: pick(SALE), cskh: pick(CSKH),
    thieu: false, daNhanHoan: false, chamCham: chance(0.2),
    nguon: NGUON[kenh.nen], nhanLuc: null, hoanLuc: null, soVang: 0, ep: o && o.ep ? [...o.ep] : null, tien: null};
  d.sk.push({t: t0 - rnd(3, 80) * MIN, x: `Khách đặt qua ${NEN[kenh.nen].ten} — ${kenh.ten}`, n: 'Pancake'});
  d.sk.push({t: t0, x: 'Kéo về CRM, vào bảng Vận đơn — Đã lên đơn', n: 'CRM'});
  return d;
}
function themDon(d) { S.don.push(d); S.donMap[d.id] = d; }

// Giao cho hãng thì trừ tồn của kho xuất; kho không đủ thì đơn đứng lại ở "Đã lên đơn".
function xuatChoDon(d, t) {
  const thieu = d.items.find(i => S.ton[d.wh][i.ma].co < i.sl);
  if (thieu) {
    if (!d.thieu) d.sk.push({t, x: `${KHO[d.wh].ten} thiếu ${SPMAP[thieu.ma].ten} — chưa giao được cho hãng`, n: 'Kho', noiBo: true});
    d.thieu = true;
    return false;
  }
  for (const i of d.items) { S.ton[d.wh][i.ma].co -= i.sl; ghiSo({t, loai: 'Xuất cho đơn', ma: i.ma, sl: -i.sl, wh: d.wh, ghi: d.id}); }
  d.thieu = false;
  return true;
}
function buocTiep(d, t, live) {
  const city = S.khMap[d.kh].city;
  const add = (x, n = d.hang) => d.sk.push({t, x, n});
  // Đơn mẫu có kết cục định sẵn (ep) không rút số ngẫu nhiên ở các ngã rẽ
  const ketCuc = () => d.ep && d.ep.length ? d.ep.shift() : null;
  switch (d.pha) {
    case 'tao':
      if (!live && !d.ep && chance(0.04)) { add('Khách báo huỷ trước khi giao hãng', 'CSKH'); d.tt = 'Hủy trước giao'; d.pha = 'huy'; break; }
      if (live && !xuatChoDon(d, t)) break;
      add(`${d.hang} đã nhận hàng tại ${KHO[d.wh].ten}`); d.tt = 'Đang giao'; d.pha = 'di'; d.buoc = 0; d.giao = t;
      break;
    case 'di': {
      const ds = CHANG[d.route](d.mkt);
      if (!live && !d.ep && d.buoc < ds.length - 1 && chance(0.02)) {
        add('Khách báo huỷ khi hàng đang đi — hãng chuyển hoàn', 'CSKH'); d.tt = 'Hủy sau giao'; d.pha = 'hoan'; d.hoanLuc = t; break;
      }
      const x = ds[d.buoc];
      add(x === 'Đang phát' ? `Đang phát — ${city}` : x);
      d.buoc++;
      if (live) d.chamCham = false;
      if (d.buoc >= ds.length) d.pha = 'phat';
      break;
    }
    case 'phat': {
      const kq = ketCuc(), r = kq ? null : R();
      if (kq === 'giao' || (r !== null && r < 0.74)) { add(`Đã giao thành công — ${city}`); d.tt = 'Đã nhận hàng'; d.pha = 'xong'; d.nhanLuc = t; }
      else if (kq === 'vang' || (r !== null && r < 0.94)) { add('Phát không thành công — khách vắng nhà'); d.tt = 'Khách vắng'; d.pha = 'vang'; d.soVang++; }
      else { add('Khách từ chối nhận — hãng chuyển hoàn'); d.tt = 'Hoàn đơn'; d.pha = 'hoan'; d.hoanLuc = t; }
      break;
    }
    case 'vang': add(`Đã gọi khách, hẹn phát lại ngày ${ngay(t + DAY)}`, 'CSKH · ' + d.cskh); d.tt = 'Hẹn lại'; d.pha = 'hen'; break;
    case 'hen': add(`Đang phát lại — ${city}`); d.tt = 'Đang giao'; d.pha = 'phat2'; break;
    case 'phat2': {
      const kq = ketCuc();
      if (kq ? kq === 'giao' : chance(0.7)) { add(`Đã giao thành công — ${city}`); d.tt = 'Đã nhận hàng'; d.pha = 'xong'; d.nhanLuc = t; }
      else { add('Không liên lạc được khách — hãng chuyển hoàn'); d.tt = 'Hoàn đơn'; d.pha = 'hoan'; d.hoanLuc = t; }
      break;
    }
    case 'hoan': add('Đang hoàn về kho'); d.pha = 'hoanve'; break;
    case 'hoanve': add(`Đã hoàn về ${KHO[d.wh].ten} — chờ kho nhận`); d.pha = 'daHoan'; break;
  }
}
// Số giờ tới tin kế tiếp của hãng, dùng khi dựng lịch sử. Đơn "chậm" kẹt lâu ở hải quan hoặc trung chuyển.
function treTiep(d) {
  switch (d.pha) {
    case 'tao': return rnd(4, 36);
    case 'di': {
      const x = CHANG[d.route](d.mkt)[d.buoc];
      if (d.chamCham && (x === 'Đã thông quan' || (d.route === 'nd' && x === 'Đang phát'))) return rnd(170, 380);
      return x === 'Đã thông quan' ? rnd(8, 50) : rnd(18, 60);
    }
    case 'phat': case 'phat2': return rnd(3, 12);
    case 'vang': return rnd(20, 60);
    case 'hen': return rnd(16, 40);
    case 'hoan': return rnd(20, 60);
    case 'hoanve': return rnd(60, 160);
    default: return 9999;
  }
}
function moPhong(d, toi) {
  let t = d.tao;
  for (let i = 0; i < 20 && !KET_THUC.has(d.pha); i++) {
    t += treTiep(d) * HOUR + rnd(0, 59) * MIN;
    if (t > toi) break;
    buocTiep(d, t, false);
  }
}
// Đơn mẫu: chặng cách nhau một ngày, mốc quyết định (giao hoặc hoàn) rơi đúng `truoc` ngày trước hiện tại
function donMau(o) {
  const k = kenhTheoId(o.kenh);
  const chang = CHANG[o.wh === 'HN' ? 'qt' : 'nd'](k.mkt).length;
  const tQuyet = S.now - o.truoc * DAY - rnd(1, 9) * HOUR;
  const t0 = tQuyet - (1 + chang + (o.ep[0] === 'vang' ? 4 : 1)) * DAY;
  const d = taoDon(t0, k, o);
  let t = t0;
  for (let i = 0; i < 12 && !KET_THUC.has(d.pha); i++) { t += DAY; buocTiep(d, t, false); }
  if (d.pha === 'daHoan') { d.daNhanHoan = true; d.sk.push({t: t + DAY, x: 'Kho đã nhận lại hàng hoàn — cộng lại vào tồn', n: 'Kho', noiBo: true}); }
  d.tien = taoTien(d, o.tien);
  themDon(d);
  return d;
}
function taoTien(d, sp) {
  const t = {pttt: sp.pttt, daThu: 0, tt: TT_TIEN.CHUA, veTk: false, nhac: 0, nhacLuc: null};
  if (sp.tra === 'du') { t.daThu = d.tong; t.tt = TT_TIEN.DU; t.veTk = sp.veTk !== false; }
  else if (sp.tra === 'mot') { t.daThu = lamTron(d.tong * 0.5, d.cur); t.tt = TT_TIEN.MOT; }
  if (sp.nhac) { t.nhac = sp.nhac; t.nhacLuc = S.now - 2 * DAY; }
  return t;
}
function bangGiu() { const m = {}; for (const d of S.don) if (d.pha === 'tao') for (const i of d.items) { const k = d.wh + '|' + i.ma; m[k] = (m[k] || 0) + i.sl; } return m; }
// Số đã xuất cho đơn (giao cho hãng) trong 7 × 24 giờ tới mốc `toi`, theo kho|mã — tốc độ xuất của màn Kho
function bangXuat7(toi = Date.now()) { const m = {}; for (const d of S.don) if (d.giao && d.giao >= toi - 7 * DAY && d.giao <= toi) for (const i of d.items) { const k = d.wh + '|' + i.ma; m[k] = (m[k] || 0) + i.sl; } return m; }
function bangVe() { const m = {}; for (const p of S.phieu) for (const i of p.items) { const k = p.wh + '|' + i.ma; m[k] = (m[k] || 0) + i.sl; } return m; }
function ghiSo(e) { S.so.unshift({t: Date.now(), wh2: null, ai: pick(VANDON), ...e}); }

function khoiTao() {
  R = taoRng(20261012);   // dòng chính, giữ đúng thứ tự gọi của bản mockup: Báo đơn, Kho, Kênh ra y như mockup
  const now = Date.now();
  S = {view: 'baodon', mounted: {}, now, don: [], donMap: {}, khach: [], khMap: {}, seqNgay: {}, demKhach: 0, demPck: 482100, demPhieu: 3, demKenh: 0,
    kenh: [], ton: {}, so: [], phieu: [], ngan: null, truocNgan: null, dangHoi: false,
    bd: {q: '', mkt: '', hang: '', kenh: '', tt: '', tac: false, sx: 'moi', trang: 1, nguong: 5, ngay: {chip: '', tu: '', den: ''}},
    kho: {wh: '', loai: '', xem: 12}, kn: {nen: ''},
    cn: {q: '', pttt: '', mkt: '', tuoi: '', loc: 'chua', trang: 1, ngay: {chip: '', tu: '', den: ''}, chon: new Set()},
    rr: {sdt: '', mau: '', loc: '', xem: 20, chan: null}, lp: {ky: 30, xem: 'page', page: '', diem: null},
    tiGia: {...TI_GIA_MAC_DINH}, tienVe: [], qc: {}};
  S.kenh = KENH_GOC.map(k => ({trang: 'ok', tu: true, ...k, hoiThoai: k.nen === 'fb' ? rnd(14, 86) : rnd(0, 9), ma: (k.nen === 'fb' ? 'pg_' : 'shop_') + '••••' + digits(4)}));
  const moc = Array.from({length: 165}, () => now - Math.pow(R(), 1.45) * 21 * DAY - rnd(0, 59) * MIN).sort((a, b) => a - b);
  for (const t of moc) {
    let k;
    do k = weighted(S.kenh.map(x => [x, x.w])); while (k.trang !== 'ok' && now - t < 2 * DAY);
    const d = taoDon(t, k);
    moPhong(d, now);
    themDon(d);
  }
  // Hàng hoàn về đã lâu thì kho đã nhận rồi; còn lại chờ kho bấm nhận.
  for (const d of S.don) if (d.pha === 'daHoan') {
    const t = cuoi(d).t + rnd(4, 30) * HOUR;
    if (t < now - DAY) { d.daNhanHoan = true; d.sk.push({t, x: 'Kho đã nhận lại hàng hoàn — cộng lại vào tồn', n: 'Kho', noiBo: true}); }
  }
  for (const d of S.don) if (d.giao && now - d.giao < 3 * DAY) for (const i of d.items) S.so.push({t: d.giao, loai: 'Xuất cho đơn', ma: i.ma, sl: -i.sl, wh: d.wh, wh2: null, ai: pick(VANDON), ghi: d.id});
  // Tồn kho: đủ cho đơn đang giữ, cộng thêm một ít; cố ý để vài chỗ sắp hết, hết và thiếu cho đơn.
  const giu = bangGiu();
  for (const w of Object.keys(KHO)) { S.ton[w] = {}; for (const sp of SP) S.ton[w][sp.ma] = {co: (giu[w + '|' + sp.ma] || 0) + (w === 'HN' ? rnd(90, 420) : rnd(40, 170)), nguong: w === 'HN' ? 60 : 25}; }
  S.ton.HN['KCN-05'].co = (giu['HN|KCN-05'] || 0) + 41;
  S.ton.US['HM-200'].co = giu['US|HM-200'] || 0;
  let max = null;
  for (const e of Object.entries(giu)) if (!max || e[1] > max[1]) max = e;
  const th = max ? {w: max[0].split('|')[0], ma: max[0].split('|')[1]} : {w: 'PH', ma: 'RES-07'};
  if (max) S.ton[th.w][th.ma].co = Math.max(0, max[1] - 2);
  const khac = th.ma === 'KCN-05' ? 'SRM-06' : 'KCN-05';
  S.phieu = [
    {id: maPhieu('PN', now - 3 * DAY, 1), wh: 'US', items: [{ma: 'RC-01', sl: 120}, {ma: 'VCS-04', sl: 80}], eta: now + 2 * DAY, ghi: 'Hàng bay từ kho tổng Hà Nội'},
    {id: maPhieu('PN', now - DAY, 2), wh: th.w, items: [{ma: th.ma, sl: 60}, {ma: khac, sl: 100}], eta: now + DAY, ghi: th.w === 'HN' ? 'Nhà cung cấp giao' : 'Hàng bay từ kho tổng Hà Nội'},
    {id: maPhieu('PN', now, 3), wh: 'HN', items: [{ma: 'SRM-06', sl: 300}], eta: now + 4 * DAY, ghi: 'Nhà cung cấp giao'},
  ];
  for (const i of S.phieu[0].items) S.so.push({t: now - 3 * DAY, loai: 'Chuyển đi', ma: i.ma, sl: -i.sl, wh: 'HN', wh2: 'US', ai: 'CHIBK', ghi: 'Phiếu ' + S.phieu[0].id});
  S.so.push({t: now - 2.2 * DAY, loai: 'Nhập', ma: 'VCC-03', sl: 200, wh: 'HN', wh2: null, ai: 'TUHV', ghi: 'Nhà cung cấp giao'});
  S.so.push({t: now - 1.6 * DAY, loai: 'Xuất', ma: 'KCN-05', sl: -12, wh: 'HN', wh2: null, ai: 'CHIBK', ghi: 'Xuất mẫu cho KOL'});
  S.so.sort((a, b) => b.t - a.t);
  // Mã xuất cho đơn nhiều nhất 7 ngày qua (trừ ba chỗ thiếu, sắp hết cố ý ở trên và hàng đang về) chỉ còn khoảng 5 ngày
  // bán: màn Kho có gợi ý nhập thật. Không rút số ngẫu nhiên nên không làm lệch dữ liệu sinh sau.
  const ve = bangVe(), boQua = new Set([th.w + '|' + th.ma, 'HN|KCN-05', 'US|HM-200']);
  const chay = Object.entries(bangXuat7(now)).filter(([k]) => !boQua.has(k) && !ve[k]).sort((a, b) => b[1] - a[1])[0];
  if (chay) { const [w, ma] = chay[0].split('|'); S.ton[w][ma].co = (giu[chay[0]] || 0) + Math.ceil(chay[1] / 7 * 5); }
  // Ba màn mới dùng dòng số riêng, sinh sau dữ liệu cũ
  const rMau = taoRng(20261013), rTien = taoRng(20261014), rPhi = taoRng(20261015);
  voi(rMau, () => { taoKhachMau(); taoNoCu(); });
  ganSoDayDu();
  voi(rTien, () => { taoThanhToan(); taoTienVe(); });
  voi(rPhi, taoChiPhi);
}
function taoKhachMau() {
  for (const m of KHACH_MAU) {
    const k = {id: m.id, ten: m.ten, sdt: `+1 (${m.so.slice(1, 4)}) •••-••${m.so.slice(-2)}`, sdtSo: m.so, mkt: m.mkt, kenhDau: m.kenh,
      dau: S.now, city: m.city, mau: m.mau, danhDau: '', lyDoChan: '', su: []};
    S.khach.push(k); S.khMap[k.id] = k;
    for (const o of m.don) k.dau = Math.min(k.dau, donMau({...o, kh: k, kenh: m.kenh, wh: m.wh}).tao);
  }
}
function taoNoCu() {
  for (const o of NO_CU) {
    const k = kenhTheoId(o.kenh);
    donMau({kenh: o.kenh, wh: 'HN', truoc: o.truoc, ep: ['giao'],
      tien: {pttt: weighted(PTTT_THEO_TT[k.mkt] || PTTT_THEO_TT.khac), tra: o.tra, veTk: o.veTk, nhac: o.tra === 'chua' ? rnd(1, 3) : 0}});
  }
}
// Số đầy đủ để tra ở màn Khách rủi ro: chỉ khách Mỹ/Canada, suy từ số đang che — dải 555-01xx là số giả theo quy ước
function ganSoDayDu() {
  const daDung = new Set(KHACH_MAU.map(k => k.so).concat(SDT_MOI));
  for (const k of S.khach) {
    if (k.mau || (k.mkt !== 'US' && k.mkt !== 'CA')) continue;
    const m = /^\+1 \((\d{3})\) •••-••(\d{2})$/.exec(k.sdt);
    const so = m ? `1${m[1]}55501${m[2]}` : '';
    k.sdtSo = so && !daDung.has(so) ? so : '';
  }
}
function taoThanhToan() {
  for (const d of S.don) {
    if (d.tien) continue;
    const t = {pttt: null, daThu: 0, tt: TT_TIEN.CHUA, veTk: false, nhac: 0, nhacLuc: null};
    d.tien = t;
    if (d.nguon === 'san') {
      // Sàn trả theo kỳ: đơn giao quá 14 ngày coi như sàn đã trả
      if (d.tt === 'Đã nhận hàng' && S.now - d.nhanLuc > 14 * DAY) { t.daThu = d.tong; t.tt = TT_TIEN.DU; t.veTk = true; }
      continue;
    }
    if (d.nguon === 'web') { t.pttt = 'Visa/Website'; t.daThu = d.tong; t.tt = TT_TIEN.DU; t.veTk = chance(0.9); continue; }
    t.pttt = weighted(PTTT_THEO_TT[d.mkt] || PTTT_THEO_TT.khac);
    if (d.tt === 'Đã nhận hàng') {
      const tuoi = (S.now - d.nhanLuc) / DAY;
      const p = tuoi <= 3 ? 0.15 : tuoi <= 7 ? 0.45 : tuoi <= 14 ? 0.7 : tuoi <= 30 ? 0.85 : 0.9;
      if (chance(p)) {
        if (chance(0.12)) { t.daThu = lamTron(d.tong * rnd(30, 70) / 100, d.cur); t.tt = TT_TIEN.MOT; }
        else { t.daThu = d.tong; t.tt = TT_TIEN.DU; t.veTk = chance(0.8); }
      } else if (tuoi > 7) { t.nhac = rnd(0, 2); if (t.nhac) t.nhacLuc = S.now - rnd(1, 5) * DAY; }
    } else if (t.pttt === 'PayPal' && !KET_THUC.has(d.pha) && chance(0.25)) {
      t.daThu = d.tong; t.tt = TT_TIEN.DU; t.veTk = true;   // khách trả trước qua PayPal
    }
  }
}
// Tiền về tài khoản chờ khớp: khớp mã đơn, khớp tên người gửi, trả một nửa, một khoản lệch số tiền phải chọn tay
function taoTienVe() {
  const ung = S.don.filter(d => laPhaiThu(d) && d.tien.tt === TT_TIEN.CHUA && !S.khMap[d.kh].mau);
  const lay = dk => { const i = ung.findIndex(dk); return i < 0 ? null : ung.splice(i, 1)[0]; };
  const ten = d => boDau(S.khMap[d.kh].ten).toUpperCase();
  const ds = [];
  const them = (d, so, gui, noiDung, cur = d.cur, kenh = d.tien.pttt) =>
    ds.push({id: 'TV-' + String(ds.length + 1).padStart(2, '0'), kenh, t: S.now - rnd(2, 40) * HOUR, so, cur, gui, noiDung, xong: ''});
  let d = lay(x => x.cur === 'USD');
  if (d) them(d, conLai(d), ten(d), `${d.id} thanh toan`);
  d = lay(() => true);
  if (d) them(d, conLai(d), ten(d), 'Thanh toan don hang');
  d = lay(x => x.cur === 'PHP');
  if (d) them(d, lamTron(conLai(d) / 2, d.cur), ten(d), `Tra truoc mot nua ${d.id}`);
  const daCo = new Set(S.don.filter(laPhaiThu).map(x => x.cur + conLai(x)));
  let lech = 5700;
  while (daCo.has('USD' + lech)) lech += 100;
  them(null, lech, 'J NGUYEN', 'chuyen tien hang', 'USD', 'Zelle');
  d = lay(x => x.cur === 'CAD');
  if (d) them(d, conLai(d), ten(d), d.id);
  S.tienVe = ds.sort((a, b) => b.t - a.t);
}
// Quảng cáo (₫/ngày, chỉ số 0 là hôm nay) theo page — báo cáo Marketing nộp bằng tiền Việt (ADR-047). Mỗi page tiêu một
// tỉ lệ doanh số riêng ở từng kỳ 7 và 30 ngày (ROAS khoảng 3–10); doanh số ước theo hệ số giá của thị trường, không theo
// tỉ giá tạm trên màn — sửa tỉ giá thì lãi đổi, tiền quảng cáo đã tiêu thì không.
const TI_LE_QC = {fb: [22, 32], web: [15, 22], tt: [10, 16], sp: [10, 16], lz: [10, 16]};
function taoChiPhi() {
  for (const k of S.kenh) {
    const tiLe = rnd(...TI_LE_QC[k.nen]) / 100, qc = S.qc[k.id] = Array(KY_QC).fill(0);
    for (const [tu, den] of [[0, 7], [7, KY_QC]]) {
      const uocVnd = laiKhoang(k, tu, den).dsMinor / 10 ** DEC[MARKETS[k.mkt].cur] / MARKETS[k.mkt].k * TI_GIA_MAC_DINH.USD;
      for (let i = tu; i < den; i++) qc[i] = Math.round(uocVnd * tiLe / (den - tu) * rnd(80, 120) / 100 / 1000) * 1000;
    }
  }
  // Hai page cố ý lỗ cả kỳ 7 lẫn 30 ngày: page Nhật mất kết nối mà quảng cáo vẫn chạy; LazMall đơn ít, quảng cáo sàn đắt
  for (const id of ['fb-jp', 'lz-ph']) {
    const k = kenhTheoId(id);
    for (const [tu, den] of [[0, 7], [7, KY_QC]]) {
      const r = laiKhoang(k, tu, den);
      if (r.lai === null) continue;
      const thieu = r.lai + Math.max(3e6, Math.round(r.dsVnd * 0.2));
      if (thieu <= 0) continue;
      const moiNgay = Math.ceil(thieu / (den - tu) / 1000) * 1000;
      for (let i = tu; i < den; i++) S.qc[id][i] += moiNgay;
    }
  }
}

// ---------- Hỏi hãng ----------
function thoiDiemMoi(d) { const now = Date.now(); return Math.min(now, Math.max(cuoi(d).t + MIN, now - rnd(1, 40) * MIN)); }
function capNhatHang(ds, p) {
  const now = Date.now(), kq = {doi: 0, giao: 0, congNo: 0, vang: 0, thieu: 0};
  for (const d of ds) {
    if (KET_THUC.has(d.pha)) continue;
    const xs = d.chamCham && now - cuoi(d, true).t > 4 * DAY ? 0.3 : d.pha === 'tao' ? Math.min(1, p * 1.5) : p;
    if (!chance(xs)) continue;
    const truocTT = d.tt, n = d.sk.length;
    buocTiep(d, thoiDiemMoi(d), true);
    // Hàng đã ra phát thì kết quả thường về trong ngày: một lần hỏi hãng có thể nhận cả tin "Đang phát" lẫn kết quả
    if ((d.pha === 'phat' || d.pha === 'phat2') && chance(0.5)) buocTiep(d, thoiDiemMoi(d), true);
    if (d.sk.length > n && !d.sk[d.sk.length - 1].noiBo) {
      kq.doi++;
      if (d.tt === 'Đã nhận hàng' && truocTT !== 'Đã nhận hàng') { kq.giao++; if (laPhaiThu(d) && conLai(d)) kq.congNo++; }
      if (d.tt === 'Khách vắng' && truocTT !== 'Khách vắng') kq.vang++;
    }
    if (d.thieu && d.pha === 'tao') kq.thieu++;
  }
  return kq;
}
// "7 ngày" là 7 ngày lịch giờ Việt Nam (hôm nay và 6 ngày trước), đúng như chip "7 ngày" ở Báo đơn
const ngayLui = (tu, n) => new Set(Array.from({length: n}, (_, i) => ngay(Date.now() - (tu + i) * DAY)));
function soLieuKenh(k) {
  const hn = ngay(Date.now()), bay7 = ngayLui(0, 7), truoc7 = ngayLui(7, 7);
  let homNay = 0, bay = 0, dt = 0, bayTruoc = 0, dtTruoc = 0, ketThuc = 0, hoan = 0;
  for (const d of S.don) {
    if (d.kenh !== k.id) continue;
    if (d.nt === hn) homNay++;
    if (bay7.has(d.nt)) { bay++; dt += d.tong; } else if (truoc7.has(d.nt)) { bayTruoc++; dtTruoc += d.tong; }
    if (d.pha === 'xong') ketThuc++;
    if (NHOM.hoan.includes(d.tt)) { hoan++; ketThuc++; }
  }
  return {homNay, bay, dt, bayTruoc, dtTruoc, cur: MARKETS[k.mkt].cur, tile: ketThuc ? Math.round(hoan / ketThuc * 100) : 0};
}
function trangThaiTon(w, ma, giu) {
  const o = S.ton[w][ma], cb = o.co - (giu[w + '|' + ma] || 0);
  if (cb < 0) return {lop: 'do', nhan: `Thiếu ${so(-cb)} cho đơn`, muc: 3};
  if (o.co === 0) return {lop: 'do', nhan: 'Hết hàng', muc: 3};
  if (cb <= o.nguong) return {lop: 'vang', nhan: 'Sắp hết', muc: 2};
  return {lop: 'xanh', nhan: 'Đủ hàng', muc: 1};
}

// ---------- Công nợ, khách rủi ro, lãi: phần tính, không đụng giao diện ----------
function ghiNhanTien(d, so, o) {
  const t = d.tien;
  t.daThu = Math.min(d.tong, t.daThu + so);
  const du = t.daThu >= d.tong;
  t.tt = du ? TT_TIEN.DU : TT_TIEN.MOT;
  if (o.veTk && du) t.veTk = true;
  d.sk.push({t: Date.now(), x: `${o.nguon}: nhận ${tien(so, d.cur)}${du ? ' — đủ tiền' + (t.veTk ? ', Đã về TK' : '') : ' — còn ' + tien(conLai(d), d.cur)}`, n: 'Kế toán', noiBo: true});
}
function tienSan() {
  const duoi = Date.now() - 14 * DAY, m = new Map();
  for (const d of S.don) {
    if (d.nguon !== 'san' || d.tt !== 'Đã nhận hàng' || !d.nhanLuc || d.nhanLuc < duoi) continue;
    const nen = kenhTheoId(d.kenh).nen, key = nen + '|' + d.cur;
    let r = m.get(key);
    if (!r) m.set(key, r = {nen, cur: d.cur, so: 0, don: 0, dau: Infinity});
    r.so += Math.round(d.tong * (1 - PHI_SAN[nen])); r.don++; r.dau = Math.min(r.dau, d.nhanLuc);
  }
  return [...m.values()].sort((a, b) => a.nen.localeCompare(b.nen) || a.cur.localeCompare(b.cur));
}
function goiYKhop(tv) {
  const ung = S.don.filter(d => laPhaiThu(d) && d.cur === tv.cur && conLai(d) > 0);
  const theoMa = ung.find(d => tv.noiDung.includes(d.id));
  if (theoMa && tv.so <= conLai(theoMa)) return {cach: tv.so === conLai(theoMa) ? 'ma' : 'mot-phan', don: theoMa};
  const theoTen = ung.filter(d => conLai(d) === tv.so && boDau(S.khMap[d.kh].ten).toUpperCase() === tv.gui);
  if (theoTen.length === 1) return {cach: 'ten', don: theoTen[0]};
  return {cach: '', ung: ung.sort((a, b) => Math.abs(conLai(a) - tv.so) - Math.abs(conLai(b) - tv.so)).slice(0, 5)};
}
function donTheoKhach() { const m = new Map(); for (const d of S.don) { let a = m.get(d.kh); if (!a) m.set(d.kh, a = []); a.push(d); } return m; }
// Chấm điểm rủi ro — ngưỡng demo, chưa chốt; đúng như khối "Cách tính" trên màn
function ruiRo(kh, theoKhach) {
  const ds = theoKhach.get(kh.id) || [];
  const nhan = ds.filter(d => d.tt === 'Đã nhận hàng').length, hoan = ds.filter(d => NHOM.hoan.includes(d.tt)).length;
  const vang = ds.reduce((s, d) => s + (d.soVang || 0), 0);
  const no = ds.filter(d => laPhaiThu(d) && conLai(d) > 0), noLau = no.reduce((m, d) => Math.max(m, tuoiNo(d)), 0);
  const noTien = tongTheoTien(no, conLai);
  let diem = 0;
  const lyDo = [`Đã nhận ${nhan}/${ds.length} đơn`];
  if (hoan >= 2) { diem += 3; lyDo.push(`Hoàn / không nhận ${hoan} lần`); } else if (hoan === 1) { diem += 1; lyDo.push('Hoàn / không nhận 1 lần'); }
  if (vang >= 2) { diem += 1; lyDo.push(`Khách vắng ${vang} lần`); } else if (vang === 1) lyDo.push('Khách vắng 1 lần');
  if (no.length) { diem += noLau > 30 ? 3 : noLau > 14 ? 2 : noLau > 7 ? 1 : 0; lyDo.push(`Còn nợ ${chuoiTien(noTien)} — ${no.length} đơn, lâu nhất ${noLau} ngày`); }
  if (nhan >= 3 && !hoan && !no.length) diem -= 1;
  const muc = diem >= 3 ? 'cao' : diem >= 1 ? 'chu-y' : 'thap';
  const nenLam = muc === 'cao' ? ['Yêu cầu chuyển khoản trước (Zelle, PayPal…) rồi mới gửi hàng.', 'Cần Manager duyệt mới lên đơn.']
    : muc === 'chu-y' ? ['Gọi xác nhận trước khi giao.'] : ['Lên đơn bình thường.'];
  if (no.length) nenLam.push('Nhắc khách trả đơn cũ trước khi lên đơn mới.');
  if (kh.danhDau === 'chan') nenLam.unshift('Đang chặn lên đơn — Manager mở chặn mới lên được.');
  return {diem, muc, lyDo, nenLam, nhan, tong: ds.length, hoan, vang, no: no.length, noLau, noTien: no.length ? noTien : null, cuoi: ds.reduce((m, d) => Math.max(m, d.tao), 0)};
}
function timTheoSdt(chuoi) {
  let so = String(chuoi).replace(/\D/g, '');
  if (so.length === 10) so = '1' + so;
  return S.khach.find(k => k.sdtSo && k.sdtSo === so) || null;
}
const dinhDangSo = so => `+1 (${so.slice(1, 4)}) ${so.slice(4, 7)}-${so.slice(7)}`;
// Lãi một page trong các ngày lịch [tu, den) tính lùi từ hôm nay (0 là hôm nay, giờ Việt Nam). Doanh số quy VND theo tỉ
// giá tạm; thiếu tỉ giá thì doanh số và lãi là null, không đoán.
function laiKhoang(k, tu, den) {
  const d0 = dauNgay(S.now), tren = tu === 0 ? Infinity : d0 - (tu - 1) * DAY, duoi = d0 - (den - 1) * DAY;
  let dsMinor = 0, don = 0, von = 0, cuoc = 0, hoan = 0;
  for (const d of S.don) {
    if (d.kenh !== k.id) continue;
    if (d.tt === 'Đã nhận hàng' && d.nhanLuc >= duoi && d.nhanLuc < tren) { dsMinor += d.tong; don++; von += giaVon(d); cuoc += cuocDon(d); }
    if (NHOM.hoan.includes(d.tt) && d.hoanLuc && d.hoanLuc >= duoi && d.hoanLuc < tren) hoan += 2 * cuocDon(d);
  }
  const cur = MARKETS[k.mkt].cur, tg = S.tiGia[cur];
  const dsVnd = tg ? Math.round(dsMinor / 10 ** DEC[cur] * tg) : null;
  const phiSan = dsVnd === null ? 0 : Math.round(dsVnd * (PHI_SAN[k.nen] || 0));
  const qc = (S.qc[k.id] || []).slice(tu, den).reduce((a, b) => a + b, 0);
  return {k, cur, tg, dsMinor, dsVnd, phiSan, von, cuoc, qc, hoan, don, lai: dsVnd === null ? null : dsVnd - phiSan - von - cuoc - qc - hoan};
}
// Theo sản phẩm là lãi gộp: phí sàn, cước, hoàn chia theo tỉ trọng dòng trong đơn; quảng cáo tính theo page nên không trừ
function laiTheoSp(ky) {
  const duoi = dauNgay(S.now) - (ky - 1) * DAY, m = {};
  let thieu = 0;
  for (const sp of SP) m[sp.ma] = {sp, sl: 0, dsVnd: 0, von: 0, phi: 0};
  for (const d of S.don) {
    const giao = d.tt === 'Đã nhận hàng' && d.nhanLuc >= duoi, hoan = NHOM.hoan.includes(d.tt) && d.hoanLuc && d.hoanLuc >= duoi;
    if (!giao && !hoan) continue;
    const tg = S.tiGia[d.cur];
    if (!tg) { if (giao) thieu++; continue; }
    const phiSan = PHI_SAN[kenhTheoId(d.kenh).nen] || 0;
    for (const i of d.items) {
      const r = m[i.ma], phan = i.gia * i.sl / d.tong;
      if (giao) {
        const ds = Math.round(i.gia * i.sl / 10 ** DEC[d.cur] * tg);
        r.sl += i.sl; r.dsVnd += ds; r.von += i.sl * GIA_VON[i.ma]; r.phi += Math.round(ds * phiSan + cuocDon(d) * phan);
      } else r.phi += Math.round(2 * cuocDon(d) * phan);
    }
  }
  return {ds: Object.values(m).map(r => ({...r, lai: r.dsVnd - r.von - r.phi})), thieu};
}
// Lãi từng ngày của kỳ (cũ tới mới), cộng mọi page có tỉ giá hoặc một page; tổng các ngày là ô Lãi của dải chỉ số
function chuoiLai(ky, id) {
  const ds = id ? S.kenh.filter(k => k.id === id) : S.kenh, ngayDs = [], lai = [];
  let coTg = false;
  for (let i = ky - 1; i >= 0; i--) {
    let v = 0;
    for (const k of ds) { const r = laiKhoang(k, i, i + 1); if (r.lai === null) continue; coTg = true; v += r.lai; }
    ngayDs.push(dauNgay(S.now) - i * DAY); lai.push(v);
  }
  return {ngay: ngayDs, lai, coTg, tong: lai.reduce((a, b) => a + b, 0)};
}
function laiTheoTt(ky) {
  return Object.keys(MARKETS).map(m => {
    const cur = MARKETS[m].cur, r = {m, cur, dsMinor: 0, dsVnd: 0, chiPhi: 0, don: 0, lai: null};
    for (const k of S.kenh.filter(x => x.mkt === m)) {
      const x = laiKhoang(k, 0, ky);
      r.dsMinor += x.dsMinor; r.don += x.don; r.chiPhi += x.phiSan + x.von + x.cuoc + x.qc + x.hoan;
      if (x.dsVnd !== null) r.dsVnd += x.dsVnd;
    }
    if (S.tiGia[cur]) r.lai = r.dsVnd - r.chiPhi; else r.dsVnd = null;
    return r;
  });
}

// ---------- Mẩu giao diện ----------
// Ô số của dải chỉ số: lớp .o-so của KN CRM; có act thì là nút lọc, bật thì aria-pressed
function kpiO(o) {
  const tag = o.act ? 'button' : 'div';
  const them = (o.act ? ` type="button" data-act="${o.act}" aria-pressed="${!!o.on}"` : '') + (o.loc !== undefined ? ` data-loc="${h(o.loc)}"` : '') + (o.soTho !== undefined ? ` data-so="${o.soTho}"` : '');
  return `<${tag} class="o-so ${o.lop || ''}"${them}><span class="nhan">${o.nhan}</span><span class="gia-tri">${o.so}</span>${o.phu ? `<span class="phu">${o.phu}</span>` : ''}</${tag}>`;
}
const chipLoc = (act, attr, gt, on, nhan, dem) => `<button type="button" class="oms-chip" data-act="${act}" data-${attr}="${h(gt)}" aria-pressed="${!!on}">${nhan}${dem === undefined ? '' : ` <span class="dem">${dem}</span>`}</button>`;
function phanTrang(ds, trang, co = 25) { const tong = Math.max(1, Math.ceil(ds.length / co)), p = Math.min(Math.max(1, trang), tong); return {p, tong, rows: ds.slice((p - 1) * co, p * co)}; }
const thanhTrang = (pt, n, donVi, pham) => `<span>${so(n)} ${donVi} · trang ${pt.p}/${pt.tong}</span><span class="hang-nut"><button type="button" class="nut nut-nho" data-act="trang" data-pham="${pham}" data-buoc="-1"${pt.p <= 1 ? ' disabled' : ''}>‹ Trước</button><button type="button" class="nut nut-nho" data-act="trang" data-pham="${pham}" data-buoc="1"${pt.p >= pt.tong ? ' disabled' : ''}>Sau ›</button></span>`;
// Bảng trống: nói rõ vì sao và chỉ cách gỡ lọc
const hangTrong = (cot, chu, act) => `<tr><td colspan="${cot}" class="trong">${chu}${act ? `<button type="button" class="link" data-act="${act}">Bỏ lọc</button>` : ''}</td></tr>`;
const nutDong = `<button type="button" class="nut-icon" data-act="dong-ngan" aria-label="Đóng">${ICON.dong}</button>`;
function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast'; el.textContent = msg;
  $('#thong-bao').append(el);
  setTimeout(() => { el.classList.add('an'); setTimeout(() => el.remove(), 320); }, 4600);
}
function badgeTien(d) {
  if (d.nguon === 'san') return '<span class="chip chip-nhat"><i></i>Sàn thu hộ</span>';
  return `<span class="chip ${TT_TIEN_LOP[d.tien.tt]}"><i></i>${h(d.tien.tt)}</span>`;
}
const chipVeTk = '<span class="chip chip-tot"><i></i>Đã về TK</span>';
const nutDanhDau = kh => [['theo-doi', 'Theo dõi'], ['chan', 'Chặn lên đơn'], ['', 'Không đánh dấu']].map(([v, t]) =>
  `<button type="button" class="nut nut-nho" data-act="rr-danh-dau" data-kh="${kh.id}" data-gia-tri="${v}" aria-pressed="${kh.danhDau === v}">${t}</button>`).join('');
// Hàng nút đánh dấu; bấm "Chặn lên đơn" thì hàng thành ô ghi lý do ngay tại chỗ (thẻ cảnh báo hay ngăn kéo khách)
function hangDanhDau(kh, noi) {
  if (S.rr.chan && S.rr.chan.kh === kh.id && S.rr.chan.noi === noi) return `<form class="oms-chan" id="f-chan" data-kh="${kh.id}" novalidate>
    <div class="truong"><label for="chan-ly-do">Lý do chặn lên đơn</label><textarea id="chan-ly-do" name="ly-do" class="o-nhap" rows="2" maxlength="200" placeholder="Ví dụ: hoàn 2 đơn liên tiếp, không nghe máy" aria-describedby="chan-loi" data-dau></textarea><p class="loi-truong" id="chan-loi" role="alert"></p></div>
    <div class="hang"><button type="submit" class="nut nut-nho nut-nguy">Chặn lên đơn</button><button type="button" class="nut nut-nho" data-act="rr-chan-huy">Huỷ</button></div></form>`;
  return `<div class="hang">${nutDanhDau(kh)}${noi === 'the' ? `<button type="button" class="nut nut-nho" data-act="mo-khach" data-id="${kh.id}">Xem lịch sử</button>` : ''}</div>`;
}
const lyDoChan = kh => kh.danhDau === 'chan' && kh.lyDoChan ? `<p class="oms-ly-do-chan"><b>Lý do chặn:</b> ${h(kh.lyDoChan)}</p>` : '';
// Dòng thời gian của khách: sự kiện mọi đơn và đánh dấu của khách, mới nhất trước
function dongThoiGianKhach(kh) {
  const su = kh.su.map(e => ({...e, don: ''}));
  for (const d of S.don) if (d.kh === kh.id) for (const e of d.sk) su.push({...e, don: d.id});
  su.sort((a, b) => b.t - a.t);
  return `<ol class="dong-tg">${su.map(e => `<li data-t="${Math.round(e.t)}"${e.noiBo ? ' class="noi-bo"' : ''}><div class="sk">${e.don ? `<span class="mono">${e.don}</span> · ` : ''}${h(e.x)}</div><div class="tg">${ngayGio(e.t)} · <span class="nguon">${h(e.n)}</span></div></li>`).join('')}</ol>`;
}
// Lọc ngày: chip nhanh (Hôm nay, 7 ngày, 30 ngày — ngày lịch giờ VN) hoặc ô Từ–Đến; trả [từ, đến] dạng ISO, '' là không chặn
const CHIP_NGAY = [['', 'Tất cả'], ['hom-nay', 'Hôm nay'], ['7', '7 ngày'], ['30', '30 ngày']];
function khoangNgay(f) {
  if (!f.chip) return [f.tu, f.den];
  const lui = {'hom-nay': 0, 7: 6, 30: 29}[f.chip];
  return [isoNgay(Date.now() - lui * DAY), isoNgay(Date.now())];
}
const trongKhoang = (iso, [tu, den]) => (!tu || iso >= tu) && (!den || iso <= den);
const oNgay = (pham, nhanTu, nhanDen) => `<div class="truong"><label for="${pham}-tu">${nhanTu}</label><input id="${pham}-tu" class="o-nhap" type="date" autocomplete="off" aria-describedby="${pham}-ngay-loi"></div>
      <div class="truong"><label for="${pham}-den">${nhanDen}</label><input id="${pham}-den" class="o-nhap" type="date" autocomplete="off" aria-describedby="${pham}-ngay-loi"></div>
      <p class="loi-truong oms-loi-loc" id="${pham}-ngay-loi" role="alert"></p>`;
// Gõ Từ–Đến: ngày sai hay Từ sau Đến thì báo ngay dưới ô và giữ nguyên bộ lọc đang dùng
function doiNgay(pham) {
  const tu = $(`#${pham}-tu`), den = $(`#${pham}-den`), loi = $(`#${pham}-ngay-loi`);
  const sai = [tu, den].find(o => !o.checkValidity());
  if (sai) { loi.textContent = sai.validationMessage || 'Nhập ngày hợp lệ theo DD/MM/YYYY.'; return; }
  if (tu.value && den.value && tu.value > den.value) { loi.textContent = 'Từ ngày phải trước hoặc trùng Đến ngày.'; return; }
  loi.textContent = '';
  S[pham].ngay = {chip: '', tu: tu.value, den: den.value}; S[pham].trang = 1;
  MAN[S.view].upd();
}
function chonChipNgay(pham, chip) {
  S[pham].ngay = {chip, tu: '', den: ''}; S[pham].trang = 1;
  for (const o of [$(`#${pham}-tu`), $(`#${pham}-den`)]) o.value = '';
  $(`#${pham}-ngay-loi`).textContent = '';
  MAN[S.view].upd();
}
// CSV cho Excel tiếng Việt: UTF-8 có BOM, phân cách ";", CRLF. Ô mở đầu bằng = + - @ (công thức) hay dãy số dài (mã vận
// đơn — Excel đổi thành số mũ) có dấu ' đứng trước. Tiền ghi đơn vị chính, phẩy thập phân, loại tiền ở cột riêng.
const oCsv = v => { let x = String(v ?? ''); if (/^[=+\-@]/.test(x) || /^\d{12,}$/.test(x)) x = "'" + x; return /[;"\r\n]/.test(x) ? `"${x.replace(/"/g, '""')}"` : x; };
const soCsv = (minor, cur) => (minor / 10 ** DEC[cur]).toFixed(DEC[cur]).replace('.', ',');
function xuatCsv(ten, dau, dong) {
  const tep = `kn-oms-${ten}-${isoNgay(Date.now()).replace(/-/g, '')}.csv`;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\ufeff' + [dau, ...dong].map(r => r.map(oCsv).join(';')).join('\r\n') + '\r\n'], {type: 'text/csv;charset=utf-8'}));
  a.download = tep;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  toast(`Đã xuất ${so(dong.length)} dòng ra tệp ${tep}.`);
}
const chonMkt = (id, nhan) => `<div class="truong"><label for="${id}">${nhan}</label><select id="${id}" class="o-nhap"><option value="">Mọi thị trường</option>${Object.entries(MARKETS).map(([m, x]) => `<option value="${m}">${m} — ${x.ten}</option>`).join('')}</select></div>`;

// ---------- Báo đơn ----------
function mountBaoDon() {
  $('#v-baodon').innerHTML = `
  <header class="trang-dau">
    <div><h1>Báo đơn</h1><p>Hành trình từng đơn theo hãng vận chuyển; đơn im quá ngưỡng thì báo tắc.</p></div>
    <div class="hanh-dong">
      <label class="oms-nhan-chon" for="bd-nguong">Báo tắc sau</label><select id="bd-nguong" class="o-nhap oms-gon">${[3, 5, 7].map(n => `<option value="${n}"${n === S.bd.nguong ? ' selected' : ''}>${n} ngày</option>`).join('')}</select>
      <button type="button" class="nut" data-act="bd-xuat">${ICON.tai}<span>Xuất danh sách</span></button>
      <button type="button" class="nut nut-chinh" data-act="hoi-hang" id="bd-hoi">${ICON.dongBo}<span>Cập nhật từ hãng</span></button>
    </div>
  </header>
  <div class="oms-kpi" id="bd-kpi"></div>
  <div class="bang-hop cq">
    <div class="loc">
      <div class="truong o-tim"><label for="bd-q">Tìm đơn</label><input id="bd-q" class="o-nhap" type="search" placeholder="Mã đơn, vận đơn, tên khách, SĐT" autocomplete="off"></div>
      ${chonMkt('bd-mkt', 'Thị trường')}
      <div class="truong"><label for="bd-hang">Hãng vận chuyển</label><select id="bd-hang" class="o-nhap"><option value="">Mọi hãng</option>${Object.keys(HANG).map(x => `<option>${h(x)}</option>`).join('')}</select></div>
      <div class="truong"><label for="bd-kenh">Kênh bán</label><select id="bd-kenh" class="o-nhap"></select></div>
      <div class="truong"><label for="bd-sx">Sắp xếp</label><select id="bd-sx" class="o-nhap"><option value="moi">Mới lên đơn trước</option><option value="lau">Lâu chưa có tin trước</option></select></div>
      <div class="truong oms-truong-chip"><span class="oms-nhan-loc" id="bd-ngay-nhan">Ngày lên đơn</span><div class="oms-chips" id="bd-ngay" role="group" aria-labelledby="bd-ngay-nhan"></div></div>
      ${oNgay('bd', 'Lên đơn từ', 'Đến ngày')}
    </div>
    <div class="oms-chips" id="bd-chips" role="group" aria-label="Lọc theo trạng thái"></div>
    <div class="bang-cuon"><table class="bang">
      <thead><tr><th>Mã đơn</th><th class="an-s">Khách hàng</th><th class="an-l">Kênh</th><th class="an-l">Hãng · mã vận đơn</th><th>Trạng thái</th><th class="an-xl">Tin mới nhất</th><th class="phai an-m">Ngày đi</th><th class="phai">Tổng tiền</th></tr></thead>
      <tbody id="bd-than"></tbody>
    </table></div>
    <div class="phan-trang" id="bd-trang"></div>
  </div>`;
}
function hangDon(d) {
  const k = S.khMap[d.kh], kn = kenhTheoId(d.kenh), c = cuoi(d), tac = laTac(d);
  const di = d.giao ? Math.floor(((KET_THUC.has(d.pha) ? cuoi(d, true).t : Date.now()) - d.giao) / DAY) : null;
  return `<tr class="bam${S.ngan && S.ngan.id === d.id ? ' dang-mo' : ''}" data-don="${d.id}" data-ngay="${d.ntIso}" tabindex="0">
    <td><span class="mono dam nw">${d.id}</span><div class="oms-mo nw">${d.mkt} · ${d.pck}</div><div class="chi-s">${h(k.ten)}</div></td>
    <td class="an-s">${h(k.ten)}<div class="oms-mo nw">${h(k.sdt)}</div></td>
    <td class="an-l">${nenChip(kn)}<div class="oms-mo">${h(kn.ten)}</div></td>
    <td class="an-l">${h(d.hang)}<div class="oms-mo mono">${h(d.trk)}</div></td>
    <td>${badge(d.tt)}${tac ? `<div><span class="tac">Tắc ${soNgayIm(d)} ngày</span></div>` : ''}${d.thieu && d.pha === 'tao' ? '<div><span class="tac cam">Kho thiếu hàng</span></div>' : ''}</td>
    <td class="an-xl">${h(c.x)}<div class="oms-mo">${truoc(c.t)}</div></td>
    <td class="phai an-m">${di === null ? '—' : di}</td>
    <td class="phai">${tien(d.tong, d.cur)}</td></tr>`;
}
// Các đơn khớp bộ lọc Báo đơn: `base` theo tìm kiếm, thị trường, hãng, kênh, ngày lên đơn; `ds` thêm trạng thái, đã sắp xếp
function locBaoDon() {
  const b = S.bd, now = Date.now(), q = b.q.trim().toLowerCase(), kn = khoangNgay(b.ngay);
  const base = S.don.filter(d => (!b.mkt || d.mkt === b.mkt) && (!b.hang || d.hang === b.hang) && (!b.kenh || d.kenh === b.kenh) &&
    trongKhoang(d.ntIso, kn) && (!q || [d.id, d.pck, d.trk, S.khMap[d.kh].ten, S.khMap[d.kh].sdt].some(v => v.toLowerCase().includes(q))));
  let ds = base;
  if (b.tac) ds = ds.filter(laTac);
  else if (b.tt === 'goi') ds = ds.filter(d => NHOM.goi.includes(d.tt));
  else if (b.tt === 'hoan') ds = ds.filter(d => NHOM.hoan.includes(d.tt));
  else if (b.tt === 'nhan7') ds = ds.filter(d => d.tt === 'Đã nhận hàng' && now - cuoi(d, true).t < 7 * DAY);
  else if (b.tt) ds = ds.filter(d => d.tt === b.tt);
  ds = [...ds].sort(b.sx === 'lau' ? (x, y) => (KET_THUC.has(x.pha) - KET_THUC.has(y.pha)) || (cuoi(x, true).t - cuoi(y, true).t) : (x, y) => y.tao - x.tao);
  return {base, ds};
}
function xuatBaoDon() {
  xuatCsv('bao-don', ['Mã đơn', 'Ngày lên đơn', 'Thị trường', 'Khách hàng', 'SĐT', 'Kênh', 'Nền tảng', 'Hãng vận chuyển', 'Mã vận đơn', 'Trạng thái', 'Tin mới nhất', 'Tổng tiền', 'Loại tiền'],
    locBaoDon().ds.map(d => { const k = S.khMap[d.kh], kn = kenhTheoId(d.kenh); return [d.id, d.nt, d.mkt, k.ten, k.sdt, kn.ten, NEN[kn.nen].ten, d.hang, d.trk, d.tt, cuoi(d).x, soCsv(d.tong, d.cur), d.cur]; }));
}
function updBaoDon() {
  const b = S.bd, now = Date.now();
  const chonKenh = $('#bd-kenh');
  chonKenh.innerHTML = '<option value="">Mọi kênh</option>' + S.kenh.map(k => `<option value="${k.id}">${h(k.ten)} · ${NEN[k.nen].ten}</option>`).join('');
  chonKenh.value = b.kenh;
  $('#bd-ngay').innerHTML = CHIP_NGAY.map(([v, t]) => chipLoc('bd-ngay', 'ngay', v, b.ngay.chip === v && (v || (!b.ngay.tu && !b.ngay.den)), t)).join('');
  const {base, ds} = locBaoDon();
  const k = {giao: 0, tac: 0, goi: 0, nhan: 0, hoan: 0}, dem = {};
  for (const d of base) {
    dem[d.tt] = (dem[d.tt] || 0) + 1;
    if (d.tt === 'Đang giao') k.giao++;
    if (laTac(d)) k.tac++;
    if (NHOM.goi.includes(d.tt)) k.goi++;
    if (d.tt === 'Đã nhận hàng' && now - cuoi(d, true).t < 7 * DAY) k.nhan++;
    if (NHOM.hoan.includes(d.tt)) k.hoan++;
  }
  const on = loc => loc === 'tac' ? b.tac : (!b.tac && b.tt === loc);
  $('#bd-kpi').innerHTML = [
    kpiO({nhan: 'Đang trên đường', so: k.giao, act: 'bd-kpi', loc: 'Đang giao', on: on('Đang giao'), lop: 'xanh-duong'}),
    kpiO({nhan: `Tắc quá ${b.nguong} ngày`, so: k.tac, act: 'bd-kpi', loc: 'tac', on: on('tac'), lop: k.tac ? 'do' : '', phu: 'Không có tin mới từ hãng'}),
    kpiO({nhan: 'Cần gọi khách', so: k.goi, act: 'bd-kpi', loc: 'goi', on: on('goi'), lop: k.goi ? 'cam' : '', phu: 'Khách vắng, hẹn lại'}),
    kpiO({nhan: 'Đã nhận trong 7 ngày', so: k.nhan, act: 'bd-kpi', loc: 'nhan7', on: on('nhan7'), lop: 'xanh'}),
    kpiO({nhan: 'Hoàn, huỷ sau giao', so: k.hoan, act: 'bd-kpi', loc: 'hoan', on: on('hoan'), lop: k.hoan ? 'do' : ''}),
  ].join('');
  $('#bd-chips').innerHTML = chipLoc('bd-tt', 'tt', '', !b.tt && !b.tac, 'Tất cả', base.length) +
    TT.map(t => chipLoc('bd-tt', 'tt', t, !b.tac && b.tt === t, t, dem[t] || 0)).join('');
  const pt = phanTrang(ds, b.trang);
  b.trang = pt.p;
  const coLoc = b.q || b.mkt || b.hang || b.kenh || b.tt || b.tac || b.ngay.chip || b.ngay.tu || b.ngay.den;
  $('#bd-than').innerHTML = pt.rows.map(hangDon).join('') || hangTrong(8, 'Không có đơn nào khớp bộ lọc.', coLoc ? 'bd-bo-loc' : '');
  $('#bd-trang').innerHTML = thanhTrang(pt, ds.length, 'đơn', 'bd');
}
function boLocBaoDon() {
  Object.assign(S.bd, {q: '', mkt: '', hang: '', kenh: '', tt: '', tac: false, trang: 1, ngay: {chip: '', tu: '', den: ''}});
  for (const id of ['bd-q', 'bd-mkt', 'bd-hang', 'bd-kenh', 'bd-tu', 'bd-den']) $('#' + id).value = '';
  $('#bd-ngay-loi').textContent = '';
  updBaoDon();
}
async function hoiHangTatCa(btn) {
  if (S.dangHoi) return;
  const phien = S, nhan = btn.querySelector('span'), ds = S.don.filter(d => !KET_THUC.has(d.pha));
  S.dangHoi = true; btn.disabled = true; btn.classList.add('dang-quay'); btn.setAttribute('aria-busy', 'true');
  for (let i = 1; i <= 8; i++) { nhan.textContent = `Đang hỏi hãng… ${Math.round(ds.length * i / 8)}/${ds.length}`; await nghi(TRE.hoiHang); if (phien !== S) return; }
  const kq = capNhatHang(ds, 0.45);
  S.dangHoi = false; btn.disabled = false; btn.classList.remove('dang-quay'); btn.removeAttribute('aria-busy'); nhan.textContent = 'Cập nhật từ hãng';
  const them = [kq.giao && `${kq.giao} đơn vừa giao xong (${kq.congNo} đơn vào Công nợ)`, kq.vang && `${kq.vang} khách vắng`, kq.thieu && `${kq.thieu} đơn đứng lại vì kho thiếu hàng`].filter(Boolean);
  toast(`Đã hỏi hãng ${ds.length} đơn đang đi: ${kq.doi} đơn có tin mới${them.length ? ', ' + them.join(', ') : ''}.`);
  capNhat();
  veLaiNgan();
}

// ---------- Công nợ & đối soát ----------
function mountCongNo() {
  $('#v-congno').innerHTML = `
  <header class="trang-dau">
    <div><h1>Công nợ &amp; đối soát</h1><p>Đơn page đã giao chưa thu đủ và tiền về chờ khớp; mọi tổng tách theo loại tiền.</p></div>
    <div class="hanh-dong"><button type="button" class="nut" data-act="cn-xuat">${ICON.tai}<span>Xuất danh sách</span></button></div>
  </header>
  <div class="oms-kpi" id="cn-kpi"></div>
  <div class="bang-hop cq">
    <div class="loc">
      <div class="truong o-tim"><label for="cn-q">Tìm đơn phải thu</label><input id="cn-q" class="o-nhap" type="search" placeholder="Mã đơn, tên khách, SĐT" autocomplete="off"></div>
      <div class="truong"><label for="cn-pttt">Phương thức</label><select id="cn-pttt" class="o-nhap"><option value="">Mọi PTTT</option>${PTTT.map(p => `<option>${h(p)}</option>`).join('')}</select></div>
      ${chonMkt('cn-mkt', 'Thị trường')}
      ${oNgay('cn', 'Giao từ', 'Đến ngày')}
    </div>
    <div class="oms-chips" id="cn-tuoi" role="group" aria-label="Tuổi nợ"></div>
    <div class="oms-thanh-chon" id="cn-thanh-chon" hidden><b id="cn-chon-dem"></b><button type="button" class="nut nut-nho nut-chinh" data-act="cn-nhac-chon"></button><button type="button" class="nut nut-nho" data-act="cn-xuat-chon"></button><button type="button" class="nut nut-nho" data-act="cn-bo-chon">Bỏ chọn</button></div>
    <div class="bang-cuon"><table class="bang">
      <thead><tr><th class="oms-o-chon"><input type="checkbox" id="cn-chon-het" aria-label="Chọn mọi đơn đang lọc"></th><th>Mã đơn</th><th class="an-s">Khách</th><th class="phai">Còn phải thu</th><th class="phai an-s">Trễ</th><th class="an-m">Thanh toán</th><th class="an-l"><span class="vh">Thao tác</span></th></tr></thead>
      <tbody id="cn-than"></tbody>
    </table></div>
    <div class="phan-trang" id="cn-trang"></div>
  </div>
  <div class="luoi luoi-2">
    <section class="the"><div class="the-dau"><h2>Tiền về chưa khớp</h2><span class="oms-mo" id="cn-tv-dem"></span></div><div class="the-than"><ul class="oms-ds" id="cn-tien-ve"></ul></div></section>
    <section class="the"><div class="the-dau"><h2>Tiền sàn chờ về</h2><span class="oms-mo">Sàn trả theo kỳ, đã trừ phí sàn</span></div><div class="the-than"><ul class="ds-san" id="cn-san"></ul></div></section>
  </div>
  <p class="ghi-nho">Bản thật: ai ghi nhận tiền, ai xác nhận "Đã về TK" chưa chốt (câu hỏi H7). Số tiền và người gửi ở đây đều giả.</p>`;
}
function hangNo(d) {
  const k = S.khMap[d.kh], kn = kenhTheoId(d.kenh), t = d.tien, tuoi = tuoiNo(d), con = conLai(d);
  const lopTre = tuoi > 30 ? 'tre cao' : tuoi > 14 ? 'tre vua' : 'tre';
  const nut = con > 0
    ? `<button type="button" class="nut nut-nho" data-act="cn-nhac" data-id="${d.id}">Nhắc</button><button type="button" class="nut nut-nho" data-act="cn-ghi" data-id="${d.id}">Ghi nhận</button>`
    : `<button type="button" class="nut nut-nho" data-act="cn-ve-tk" data-id="${d.id}">Xác nhận về TK</button>`;
  return `<tr class="bam${S.ngan && S.ngan.id === d.id ? ' dang-mo' : ''}" data-don="${d.id}" data-tuoi="${h(nhomTuoi(tuoi))}" data-giao="${isoNgay(d.nhanLuc)}" data-nen="${kn.nen}" tabindex="0">
    <td class="oms-o-chon"><input type="checkbox" data-chon="${d.id}" aria-label="Chọn đơn ${d.id}"${S.cn.chon.has(d.id) ? ' checked' : ''}></td>
    <td><span class="mono dam nw">${d.id}</span><div class="oms-mo">${d.mkt} · ${h(t.pttt || '—')}</div><div class="chi-s">${h(k.ten)} · <span class="${lopTre}">trễ ${tuoi} ngày</span></div></td>
    <td class="an-s">${h(k.ten)}<div class="oms-mo nw">${h(k.sdt)}</div></td>
    <td class="phai"><span class="dam">${tien(con, d.cur)}</span>${t.daThu ? `<div class="oms-mo">đã thu ${tien(t.daThu, d.cur)}</div>` : ''}<div class="chi-hep">${badgeTien(d)}</div></td>
    <td class="phai an-s"><span class="${lopTre}">${tuoi} ngày</span><div class="oms-mo">giao ${ngay(d.nhanLuc).slice(0, 5)}</div></td>
    <td class="an-m">${badgeTien(d)}${t.veTk ? `<div>${chipVeTk}</div>` : ''}${t.nhac ? `<div class="oms-mo">Đã nhắc ${t.nhac} lần</div>` : ''}</td>
    <td class="an-l"><span class="hang-nut">${nut}</span></td></tr>`;
}
function hangTienVe(tv) {
  const dau = `<div><div class="hang-chip"><strong>${tv.id}</strong><span class="oms-mo">${h(tv.kenh)} · ${ngayNgan(tv.t)}</span><span class="dam">${tien(tv.so, tv.cur)}</span>${tv.xong ? '<span class="chip chip-tot"><i></i>Đã khớp</span>' : '<span class="chip chip-cho"><i></i>Chờ khớp</span>'}</div><div class="oms-mo">Từ ${h(tv.gui)} · nội dung "${h(tv.noiDung)}"</div>`;
  if (tv.xong) return `<li class="xong" data-tv="${tv.id}" data-cach="xong">${dau}<div class="goi-y-khop">Đã khớp với <span class="mono">${tv.xong}</span></div></div></li>`;
  const g = goiYKhop(tv);
  if (g.don) {
    const ly = {ma: 'khớp mã đơn và số tiền', ten: 'khớp tên người gửi và số tiền', 'mot-phan': 'khớp mã đơn, khách trả một phần'}[g.cach];
    return `<li data-tv="${tv.id}" data-cach="${g.cach}" data-goi-y="${g.don.id}">${dau}<div class="goi-y-khop">Gợi ý: <span class="mono">${g.don.id}</span> — ${ly}</div></div>
      <div class="oms-nut"><button type="button" class="nut nut-nho nut-chinh" data-act="cn-khop" data-tv="${tv.id}" data-don="${g.don.id}">Khớp</button></div></li>`;
  }
  const chon = g.ung.length
    ? `<select class="o-nhap oms-gon" id="tv-chon-${tv.id}" aria-label="Chọn đơn để khớp ${tv.id}">${g.ung.map(d => `<option value="${d.id}">${d.id} · ${h(S.khMap[d.kh].ten)} · còn ${tien(conLai(d), d.cur)}</option>`).join('')}</select><button type="button" class="nut nut-nho nut-chinh" data-act="cn-khop" data-tv="${tv.id}">Khớp</button>`
    : '<span class="oms-mo">Không có đơn nào cùng loại tiền đang chờ thu.</span>';
  return `<li data-tv="${tv.id}" data-cach="">${dau}<div class="goi-y-khop">Không khớp sẵn đơn nào — chọn tay đơn gần số tiền nhất.</div></div><div class="oms-nut">${chon}</div></li>`;
}
// Các đơn khớp bộ lọc Công nợ: `nhom` cho dải chỉ số, `base` theo nhóm, tìm kiếm, PTTT, thị trường, ngày giao; `ds` thêm tuổi nợ
function locCongNo() {
  const c = S.cn, q = c.q.trim().toLowerCase(), kn = khoangNgay(c.ngay);
  const daGiao = S.don.filter(laPhaiThu), chua = daGiao.filter(d => conLai(d) > 0);
  const nhom = {chua, qua14: chua.filter(d => tuoiNo(d) > 14), motphan: chua.filter(d => d.tien.tt === TT_TIEN.MOT),
    choxn: daGiao.filter(d => d.tien.tt === TT_TIEN.DU && !d.tien.veTk)};
  const base = nhom[c.loc].filter(d => (!c.pttt || d.tien.pttt === c.pttt) && (!c.mkt || d.mkt === c.mkt) && trongKhoang(isoNgay(d.nhanLuc), kn) &&
    (!q || [d.id, S.khMap[d.kh].ten, S.khMap[d.kh].sdt].some(v => v.toLowerCase().includes(q))));
  return {nhom, base, ds: base.filter(d => !c.tuoi || nhomTuoi(tuoiNo(d)) === c.tuoi).sort((a, b) => tuoiNo(b) - tuoiNo(a))};
}
function xuatCongNo(ds) {
  xuatCsv('cong-no', ['Mã đơn', 'Ngày giao', 'Trễ (ngày)', 'Khách hàng', 'SĐT', 'Thị trường', 'PTTT', 'Còn phải thu', 'Đã thu', 'Loại tiền', 'Thanh toán', 'Đã về TK', 'Số lần nhắc'],
    ds.map(d => { const k = S.khMap[d.kh], t = d.tien; return [d.id, ngay(d.nhanLuc), tuoiNo(d), k.ten, k.sdt, d.mkt, t.pttt || '', soCsv(conLai(d), d.cur), soCsv(t.daThu, d.cur), d.cur, t.tt, t.veTk ? 'Có' : 'Chưa', t.nhac]; }));
}
// Thanh thao tác của các đơn đã chọn; ô chọn tất cả tích khi mọi dòng đang lọc đã chọn, gạch khi mới chọn một phần
function updThanhChon(ds) {
  const n = S.cn.chon.size, het = $('#cn-chon-het');
  het.checked = n > 0 && n === ds.length; het.indeterminate = n > 0 && n < ds.length;
  $('#cn-thanh-chon').hidden = !n;
  $('#cn-chon-dem').textContent = `Đã chọn ${n} đơn`;
  $('[data-act="cn-nhac-chon"]').textContent = `Nhắc ${n} đơn`;
  $('[data-act="cn-xuat-chon"]').textContent = `Xuất ${n} đơn`;
}
function updCongNo() {
  const c = S.cn, {nhom, base, ds} = locCongNo();
  const ids = new Set(ds.map(d => d.id));
  for (const id of c.chon) if (!ids.has(id)) c.chon.delete(id);   // chỉ giữ chọn trong các dòng đang lọc
  const o = (loc, nhan, ds, f, lop) => kpiO({nhan, so: ds.length, act: 'cn-kpi', loc, on: c.loc === loc, lop: ds.length ? lop : '', phu: chipTien(tongTheoTien(ds, f)) || 'Không có'});
  $('#cn-kpi').innerHTML = o('chua', 'Đã giao, chưa thu đủ', nhom.chua, conLai, 'cam') + o('qua14', 'Quá 14 ngày', nhom.qua14, conLai, 'do') +
    o('motphan', 'Thu một phần', nhom.motphan, conLai, '') + o('choxn', 'Đã thu, chờ Kế toán xác nhận', nhom.choxn, d => d.tien.daThu, 'xanh-duong');
  const dem = {};
  for (const d of base) { const n = nhomTuoi(tuoiNo(d)); dem[n] = (dem[n] || 0) + 1; }
  $('#cn-tuoi').innerHTML = [['', 'Mọi tuổi nợ', base.length], ...['0-7', '8-14', '15-30', '>30'].map(n => [n, n === '>30' ? 'Trên 30 ngày' : n + ' ngày', dem[n] || 0])]
    .map(([n, t, s]) => chipLoc('cn-tuoi', 'tuoi', n, c.tuoi === n, t, s)).join('');
  const pt = phanTrang(ds, c.trang);
  c.trang = pt.p;
  $('#cn-than').innerHTML = pt.rows.map(hangNo).join('') || hangTrong(7, 'Không có đơn nào khớp bộ lọc.', c.q || c.pttt || c.mkt || c.tuoi || c.ngay.tu || c.ngay.den ? 'cn-bo-loc' : '');
  $('#cn-trang').innerHTML = thanhTrang(pt, ds.length, 'đơn', 'cn');
  updThanhChon(ds);
  $('#cn-tv-dem').textContent = `${S.tienVe.filter(x => !x.xong).length} khoản chờ khớp`;
  $('#cn-tien-ve').innerHTML = S.tienVe.map(hangTienVe).join('') || '<li class="oms-mo">Không có khoản nào.</li>';
  $('#cn-san').innerHTML = tienSan().map(r => `<li><span>${nenChip({nen: r.nen})} · ${r.don} đơn · dự kiến ${ngay(r.dau + 10 * DAY)}</span><span class="tien-o">${tien(lamTron(r.so, r.cur), r.cur)}</span></li>`).join('') || '<li class="oms-mo">Không có tiền sàn chờ về.</li>';
}
function boLocCongNo() {
  Object.assign(S.cn, {q: '', pttt: '', mkt: '', tuoi: '', trang: 1, ngay: {chip: '', tu: '', den: ''}});
  for (const id of ['cn-q', 'cn-pttt', 'cn-mkt', 'cn-tu', 'cn-den']) $('#' + id).value = '';
  $('#cn-ngay-loi').textContent = '';
  updCongNo();
}
function ghiNhac(d) {
  const t = d.tien;
  t.nhac++; t.nhacLuc = Date.now();
  d.sk.push({t: Date.now(), x: `Nhắc khách thanh toán lần ${t.nhac} — còn ${tien(conLai(d), d.cur)}`, n: 'CSKH · ' + d.cskh, noiBo: true});
}
function nhacKhach(d) {
  if (!d || !laPhaiThu(d) || !conLai(d)) return;
  ghiNhac(d);
  toast(`${d.id}: đã nhắc khách lần ${d.tien.nhac} (demo — chưa gửi tin thật).`);
  capNhat();
  veLaiNgan();
}
// Nhắc mọi đơn đã chọn một lần; đơn đã thu đủ (nhóm chờ xác nhận) bỏ qua
function nhacNhieu() {
  let n = 0, bo = 0;
  for (const id of S.cn.chon) { const d = S.donMap[id]; if (d && laPhaiThu(d) && conLai(d)) { ghiNhac(d); n++; } else bo++; }
  S.cn.chon.clear();
  toast(`Đã nhắc ${n} khách (demo — chưa gửi tin thật).${bo ? ` Bỏ qua ${bo} đơn đã thu đủ.` : ''}`);
  capNhat();
}
function xacNhanVeTk(d) {
  if (!d || d.tien.tt !== TT_TIEN.DU || d.tien.veTk) return;
  d.tien.veTk = true;
  d.sk.push({t: Date.now(), x: 'Kế toán xác nhận tiền đã về tài khoản — Đã về TK', n: 'Kế toán', noiBo: true});
  toast(`${d.id}: đã xác nhận Đã về TK.`);
  capNhat();
  veLaiNgan();
}
function khopTienVe(tvId, donId) {
  const tv = S.tienVe.find(x => x.id === tvId);
  if (!tv || tv.xong) return;
  if (!donId) { const chon = $('#tv-chon-' + tvId); donId = chon ? chon.value : ''; }
  const d = S.donMap[donId];
  if (!d || d.cur !== tv.cur || !conLai(d)) return toast('Chọn một đơn cùng loại tiền đang chờ thu.');
  const so = Math.min(tv.so, conLai(d)), thua = tv.so - so;
  ghiNhanTien(d, so, {veTk: true, nguon: `Tiền về ${tv.id} (${tv.kenh})`});
  tv.xong = d.id;
  toast(`Đã khớp ${tv.id} với ${d.id}: ${tien(so, d.cur)}${conLai(d) ? ' — còn ' + tien(conLai(d), d.cur) : ' — đủ tiền, Đã về TK'}${thua ? `; khách chuyển thừa ${tien(thua, tv.cur)}` : ''}.`);
  capNhat();
  veLaiNgan();
}
// Ghi nhận tiền: biểu mẫu trong ngăn kéo, không hộp thoại
function nganGhiTien(id) {
  const d = S.donMap[id], con = conLai(d), viDu = nfTien[DEC[d.cur]].format(con / 10 ** DEC[d.cur]);
  return `<div class="ngan-dau"><div><p class="oms-mo mono">${d.id} · ${h(S.khMap[d.kh].ten)}</p><h2 id="ngan-tieu-de">Ghi nhận tiền</h2><div class="hang-chip">${badgeTien(d)}<span class="oms-mo">còn ${tien(con, d.cur)} · ${h(d.tien.pttt || '—')}</span></div></div>${nutDong}</div>
  <form class="oms-form" id="f-ghi-tien" data-id="${d.id}" novalidate>
    <div class="ngan-than"><div class="bm">
      <div class="truong"><label for="gt-so">Số tiền nhận (${d.cur})</label><input id="gt-so" name="so" class="o-nhap" inputmode="decimal" autocomplete="off" placeholder="Ví dụ: ${viDu}" aria-describedby="gt-loi" data-dau><p class="loi-truong" id="gt-loi" role="alert"></p></div>
      <label class="cong-tac"><input type="checkbox" id="gt-ve" name="ve"> Tiền đã về tài khoản công ty (Kế toán xác nhận)</label>
      <p class="ghi-nho">Bản thật: ai ghi nhận tiền, ai xác nhận "Đã về TK" chưa chốt (câu hỏi H7).</p>
    </div></div>
    <div class="ngan-chan"><button type="button" class="nut" data-act="huy-form">Huỷ</button><button type="submit" class="nut nut-chinh day">Ghi nhận</button></div>
  </form>`;
}
function luuGhiTien(f) {
  const d = S.donMap[f.dataset.id];
  if (!d || !laPhaiThu(d) || !conLai(d)) return veNgan();
  const o = $('#gt-so', f), viDu = nfTien[DEC[d.cur]].format(conLai(d) / 10 ** DEC[d.cur]);
  const loi = t => { $('#gt-loi', f).textContent = t; o.setAttribute('aria-invalid', 'true'); o.focus(); };
  const so = docTien(o.value, d.cur), conNay = conLai(d);
  if (so === null) return loi('Nhập số tiền khách đã trả.');
  if (Number.isNaN(so)) return loi(`Số tiền không hợp lệ — ví dụ ${viDu}.`);
  if (so <= 0) return loi('Số tiền phải lớn hơn 0.');
  if (so > conNay) return loi(`Số tiền lớn hơn số còn phải thu (${tien(conNay, d.cur)}).`);
  ghiNhanTien(d, so, {veTk: $('#gt-ve', f).checked, nguon: `Ghi nhận tay qua ${d.tien.pttt || 'chuyển khoản'}`});
  toast(`${d.id}: đã ghi nhận ${tien(so, d.cur)} — ${d.tien.tt}.`);
  capNhat();
  veNgan();
}

// ---------- Khách rủi ro ----------
function mountRuiRo() {
  $('#v-ruiro').innerHTML = `
  <header class="trang-dau">
    <div><h1>Khách rủi ro</h1><p>Gõ SĐT lúc lên đơn để thấy khách đã nhận, hoàn hay còn nợ — chặn bom hàng trước khi gửi.</p></div>
  </header>
  <div class="rr-luoi">
    <section class="the">
      <div class="the-dau"><h2>Thử lên đơn</h2></div>
      <div class="the-than doc">
        <div class="truong"><label for="rr-sdt">Số điện thoại khách</label><input id="rr-sdt" class="o-nhap" type="tel" inputmode="tel" autocomplete="off" placeholder="Ví dụ: +1 408 555 0142"></div>
        <div class="oms-chips" role="group" aria-label="Số mẫu để thử">${Object.entries(TEN_MAU).map(([m, t]) => chipLoc('rr-mau', 'mau', m, false, t)).join('')}</div>
        <div id="rr-the" aria-live="polite"></div>
        <details class="cach-tinh"><summary>Cách tính (ngưỡng demo, chưa chốt)</summary><ul>
          <li>Hoàn hoặc không nhận từ 2 lần: +3 điểm; 1 lần: +1.</li>
          <li>Khách vắng từ 2 lần: +1.</li>
          <li>Còn nợ quá 30 ngày: +3; 15–30 ngày: +2; 8–14 ngày: +1.</li>
          <li>Đã nhận từ 3 đơn, không hoàn, không nợ: −1.</li>
          <li>Từ 3 điểm: Cao · 1–2 điểm: Cần chú ý · 0 trở xuống: Thấp.</li>
        </ul></details>
      </div>
    </section>
    <section class="the cq">
      <div class="the-dau"><h2>Khách cần chú ý</h2><span class="oms-mo" id="rr-dem"></span></div>
      <div class="oms-chips" id="rr-loc" role="group" aria-label="Lọc mức rủi ro"></div>
      <div class="bang-cuon"><table class="bang bang-nho"><thead><tr><th>Khách</th><th class="an-m">Thị trường</th><th class="phai">Đã nhận</th><th class="phai an-s">Hoàn</th><th class="an-m">Còn nợ</th><th>Mức</th></tr></thead><tbody id="rr-ds"></tbody></table></div>
      <div class="phan-trang" id="rr-them"></div>
    </section>
  </div>`;
}
function theRuiRo() {
  const so = S.rr.sdt.replace(/\D/g, '');
  if (!so) return '<p class="oms-mo">Gõ số điện thoại hoặc bấm một số mẫu để xem cảnh báo.</p>';
  if (so.length < 7) return '<p class="oms-mo">Gõ đủ số điện thoại (ít nhất 7 chữ số).</p>';
  const kh = timTheoSdt(so);
  if (!kh) return '<div class="rr-the" data-muc="moi"><div class="rr-dau"><strong>Chưa có đơn nào với SĐT này</strong><span class="chip chip-tin"><i></i>Khách mới</span></div><p>Lên đơn bình thường; đơn đầu tiên nên gọi xác nhận địa chỉ.</p></div>';
  const r = ruiRo(kh, donTheoKhach());
  return `<div class="rr-the" data-muc="${r.muc}" data-kh="${kh.id}">
    <div class="rr-dau"><div><strong>${h(kh.ten)}</strong> <span class="oms-mo mono">${kh.id}</span><div class="oms-mo">${MARKETS[kh.mkt].ten} · khách từ ${ngay(kh.dau)}</div></div><span class="muc muc-${r.muc}">${MUC_NHAN[r.muc]}</span></div>
    <ul class="ly-do">${r.lyDo.map(x => `<li>${h(x)}</li>`).join('')}</ul>
    <div class="nen-lam"><strong>Nên làm</strong>${r.nenLam.map(h).join('<br>')}</div>${lyDoChan(kh)}
    ${hangDanhDau(kh, 'the')}
  </div>`;
}
function updRrThe() {
  for (const b of $$('[data-act="rr-mau"]')) b.setAttribute('aria-pressed', String(b.dataset.mau === S.rr.mau));
  $('#rr-the').innerHTML = theRuiRo();
}
function updRuiRo() {
  updRrThe();
  const map = donTheoKhach();
  const ds = S.khach.map(k => ({k, r: ruiRo(k, map)})).filter(x => x.r.muc !== 'thap' || x.k.danhDau);
  const dem = {cao: 0, 'chu-y': 0, chan: 0};
  for (const x of ds) { if (x.r.muc in dem) dem[x.r.muc]++; if (x.k.danhDau === 'chan') dem.chan++; }
  $('#rr-loc').innerHTML = [['', 'Tất cả', ds.length], ['cao', 'Cao', dem.cao], ['chu-y', 'Cần chú ý', dem['chu-y']], ['chan', 'Đang chặn', dem.chan]]
    .map(([l, t, n]) => chipLoc('rr-loc', 'loc', l, S.rr.loc === l, t, n)).join('');
  const loc = S.rr.loc;
  const hien = ds.filter(x => !loc || (loc === 'chan' ? x.k.danhDau === 'chan' : x.r.muc === loc)).sort((a, b) => b.r.diem - a.r.diem || b.r.cuoi - a.r.cuoi);
  $('#rr-dem').textContent = `${hien.length} khách`;
  $('#rr-ds').innerHTML = hien.slice(0, S.rr.xem).map(({k, r}) => `<tr class="bam" data-khach="${k.id}" data-kh="${k.id}" data-muc="${r.muc}" tabindex="0">
    <td>${h(k.ten)}${k.danhDau ? ` <span class="danh-dau${k.danhDau === 'chan' ? ' chan' : ''}"${k.lyDoChan ? ` title="${h(k.lyDoChan)}"` : ''}>${k.danhDau === 'chan' ? 'Chặn lên đơn' : 'Theo dõi'}</span>` : ''}<div class="oms-mo nw">${h(k.sdt)}</div>${r.hoan ? `<div class="chi-s oms-mo">Hoàn ${r.hoan} lần</div>` : ''}</td>
    <td class="an-m">${k.mkt}</td><td class="phai">${r.nhan}/${r.tong}</td><td class="phai an-s">${r.hoan || '—'}</td>
    <td class="an-m">${r.noTien ? chuoiTien(r.noTien) : '—'}</td><td><span class="muc muc-${r.muc}">${MUC_NHAN[r.muc]}</span></td></tr>`).join('')
    || hangTrong(6, loc ? 'Không có khách nào ở mức này.' : 'Không có khách nào cần chú ý.', loc ? 'rr-bo-loc' : '');
  $('#rr-them').innerHTML = hien.length > S.rr.xem ? `<span>Đang hiện ${so(S.rr.xem)}/${so(hien.length)} khách</span><button type="button" class="nut nut-nho" data-act="rr-them">Xem thêm ${so(Math.min(20, hien.length - S.rr.xem))} khách</button>` : '';
}
function chonMau(mau) {
  const k = S.khach.find(x => x.mau === mau);
  S.rr.sdt = dinhDangSo(k ? k.sdtSo : SDT_MOI); S.rr.mau = mau; S.rr.chan = null;
  $('#rr-sdt').value = S.rr.sdt;
  updRrThe();
}
// Đổi đánh dấu khách; chặn lên đơn luôn kèm lý do. Mỗi lần đổi ghi một dòng vào dòng thời gian của khách.
function danhDau(id, giaTri, lyDo = '') {
  const kh = S.khMap[id];
  if (!kh) return;
  const cu = kh.danhDau;
  S.rr.chan = null;
  if (cu === giaTri) { capNhat(); veLaiNgan(); return; }
  kh.danhDau = giaTri; kh.lyDoChan = giaTri === 'chan' ? lyDo : '';
  kh.su.push({t: Date.now(), x: giaTri === 'chan' ? `Chặn lên đơn — lý do: ${lyDo}` : giaTri === 'theo-doi' ? 'Đánh dấu theo dõi' : cu === 'chan' ? 'Mở chặn lên đơn' : 'Bỏ đánh dấu theo dõi', n: 'Admin', noiBo: true});
  toast(`${kh.ten}: ${giaTri === 'chan' ? 'đã chặn lên đơn — cần Manager mở' : giaTri === 'theo-doi' ? 'đang theo dõi' : 'bỏ đánh dấu'}.`);
  capNhat();
  veLaiNgan();
}
function moChan(kh, noi) {
  S.rr.chan = {kh, noi};
  if (noi === 'ngan') renderNgan(false); else updRrThe();
  $('#chan-ly-do').focus();
}
function huyChan() {
  const noi = S.rr.chan && S.rr.chan.noi;
  S.rr.chan = null;
  if (noi === 'ngan') renderNgan(false); else updRrThe();
}
function luuChan(f) {
  const ly = $('#chan-ly-do', f).value.trim();
  if (!ly) { $('#chan-loi', f).textContent = 'Ghi lý do chặn — Manager cần biết vì sao mới mở chặn được.'; $('#chan-ly-do', f).setAttribute('aria-invalid', 'true'); return $('#chan-ly-do', f).focus(); }
  danhDau(f.dataset.kh, 'chan', ly);
}

// ---------- Kho ----------
function mountKho() {
  $('#v-kho').innerHTML = `
  <header class="trang-dau">
    <div><h1>Kho</h1><p>Tồn từng kho: đơn mới giữ hàng, giao hãng thì trừ tồn, hàng hoàn về thì cộng lại.</p></div>
    <div class="hanh-dong"><button type="button" class="nut" data-act="mo-phieu" data-loai="nhap">Nhập kho</button><button type="button" class="nut" data-act="mo-phieu" data-loai="xuat">Xuất kho</button><button type="button" class="nut nut-chinh" data-act="mo-phieu" data-loai="chuyen">Chuyển kho</button></div>
  </header>
  <div class="oms-kpi" id="kho-kpi"></div>
  <div class="doc" id="kho-canh"></div>
  <div class="bang-hop cq">
    <div class="oms-chips" id="kho-tab" role="group" aria-label="Chọn kho"></div>
    <div class="bang-cuon"><table class="bang">
      <thead><tr><th>Sản phẩm</th><th class="phai an-m">Tồn</th><th class="phai an-m">Giữ cho đơn</th><th class="phai">Có thể bán</th><th class="phai an-l">Đang về</th><th>Trạng thái</th><th class="an-l"><span class="vh">Thao tác</span></th></tr></thead>
      <tbody id="kho-than"></tbody>
    </table></div>
    <details class="cach-tinh oms-ghi-bang"><summary>Cách tính đủ bán, gợi ý nhập</summary><ul>
      <li>Tốc độ xuất = số đã xuất cho đơn (giao cho hãng) trong 7 ngày qua ÷ 7.</li>
      <li>Đủ bán = có thể bán ÷ tốc độ xuất, làm tròn xuống; chưa xuất trong 7 ngày thì chưa tính.</li>
      <li>Gợi ý nhập = 30 ngày × tốc độ xuất − có thể bán − đang về, làm tròn lên; không âm.</li>
      <li>Tính riêng từng kho. Xem tất cả kho thì mỗi dòng nêu kho cần nhập nhất.</li>
    </ul></details>
  </div>
  <section class="the"><div class="the-dau"><h2>Hàng đang về</h2></div><div class="the-than" id="kho-phieu"></div></section>
  <section class="the cq"><div class="the-dau"><h2>Sổ nhập xuất</h2></div><div class="oms-chips" id="kho-so-loc" role="group" aria-label="Lọc loại phiếu"></div><div id="kho-so"></div></section>`;
}
// Tốc độ xuất = số xuất cho đơn 7 ngày ÷ 7; đủ bán làm tròn xuống, gợi ý nhập đủ 30 ngày làm tròn lên; tính bằng số nguyên
function chiSoKho(p) {
  const cb = p.o.co - p.g;
  return {...p, cb, du: p.x ? Math.max(0, Math.floor(7 * cb / p.x)) : null, goi: p.x ? Math.max(0, Math.ceil((30 * p.x - 7 * (cb + p.v)) / 7)) : 0};
}
function updKho() {
  const giu = bangGiu(), ve = bangVe(), x7 = bangXuat7(), wsel = S.kho.wh, whs = wsel ? [wsel] : Object.keys(KHO);
  $('#kho-tab').innerHTML = [['', 'Tất cả kho'], ...Object.entries(KHO).map(([w, k]) => [w, k.ten])].map(([w, t]) => chipLoc('kho-tab', 'wh', w, w === wsel, h(t))).join('');
  let co = 0, g = 0, v = 0, can = 0;
  const hang = SP.map(sp => {
    const per = whs.map(w => ({w, o: S.ton[w][sp.ma], g: giu[w + '|' + sp.ma] || 0, v: ve[w + '|' + sp.ma] || 0, x: x7[w + '|' + sp.ma] || 0, tt: trangThaiTon(w, sp.ma, giu)}));
    const r = {sp, per, co: 0, g: 0, v: 0, x: 0, xau: per[0]};
    for (const p of per) { r.co += p.o.co; r.g += p.g; r.v += p.v; r.x += p.x; if (p.tt.muc > r.xau.tt.muc) r.xau = p; if (p.tt.muc >= 2) can++; }
    co += r.co; g += r.g; v += r.v;
    return r;
  }).sort((a, b) => b.xau.tt.muc - a.xau.tt.muc);
  $('#kho-kpi').innerHTML = kpiO({nhan: 'Tồn trong kho', so: so(co), phu: 'sản phẩm'}) + kpiO({nhan: 'Giữ cho đơn chờ giao', so: so(g)}) +
    kpiO({nhan: 'Có thể bán', so: so(co - g)}) + kpiO({nhan: 'Đang về', so: so(v), phu: `${S.phieu.filter(p => !wsel || p.wh === wsel).length} phiếu`}) +
    kpiO({nhan: 'Cần nhập thêm', so: can, lop: can ? 'cam' : '', phu: 'mã hàng theo từng kho'});
  const canh = [];
  for (const w of whs) for (const sp of SP) {
    const o = S.ton[w][sp.ma], gg = giu[w + '|' + sp.ma] || 0;
    if (o.co - gg >= 0) continue;
    const nDon = S.don.filter(d => d.pha === 'tao' && d.wh === w && d.items.some(i => i.ma === sp.ma)).length;
    const p = S.phieu.find(x => x.wh === w && x.items.some(i => i.ma === sp.ma));
    canh.push(`<div class="bao bao-xau"><span class="bao-ic">!</span><div class="oms-bao-than"><div><b>${KHO[w].ten} thiếu ${so(gg - o.co)} ${h(sp.ten)}</b> cho ${nDon} đơn đang chờ giao hãng.${p ? ` Phiếu ${p.id} đang về ${so(p.items.find(i => i.ma === sp.ma).sl)}, dự kiến ${ngay(p.eta)}.` : ''}</div>${p
      ? `<button type="button" class="nut nut-nho nut-chinh" data-act="nhan-phieu" data-id="${p.id}">Hàng đã về — nhận phiếu ${p.id}</button>`
      : `<button type="button" class="nut nut-nho nut-chinh" data-act="mo-phieu" data-loai="nhap" data-sp="${sp.ma}" data-kho="${w}">Nhập kho</button>`}</div></div>`);
  }
  $('#kho-canh').innerHTML = canh.join('');
  const LOP_TON = {xanh: 'chip-tot', vang: 'chip-cho', do: 'chip-xau'};
  $('#kho-than').innerHTML = hang.map(r => {
    const cb = r.co - r.g, tt = r.xau.tt, wDau = wsel || r.xau.w;
    const nguong = r.per.reduce((s, p) => s + p.o.nguong, 0);
    const chiTiet = `<div class="oms-mo">${wsel ? `ngưỡng báo ${so(nguong)}` : r.per.map(p => `${KHO[p.w].ngan} ${so(p.o.co)}`).join(' · ')}</div>`;
    // Vạch "có thể bán" theo tổng các kho đang xem; nhãn trạng thái nêu kho tệ nhất.
    const lopVach = cb < 0 ? 'do' : cb <= nguong ? 'vang' : 'xanh';
    // Đủ bán và gợi ý nhập tính riêng từng kho (hàng kho này không bán thay kho kia được); xem tất cả kho thì dòng nêu
    // kho cần nhập nhiều nhất, không kho nào cần thì nêu đúng kho mà nhãn trạng thái đang nói tới
    const ms = r.per.map(chiSoKho), canNhap = ms.reduce((a, b) => b.goi > a.goi ? b : a);
    const xet = canNhap.goi ? canNhap : ms[r.per.indexOf(r.xau)];
    const khoXet = wsel ? '' : `kho ${KHO[xet.w].ngan} `, duBan = xet.du, goiY = xet.goi;
    const chuDu = duBan === null ? `${khoXet}chưa xuất 7 ngày qua` : `${khoXet}đủ bán ${duBan} ngày`;
    return `<tr data-sp="${r.sp.ma}" data-kho-xet="${xet.w}" data-cb-kho="${xet.cb}" data-ve-kho="${xet.v}" data-xuat7="${xet.x}" data-du-ban="${duBan ?? ''}" data-goi-y="${goiY}"><td class="ten-sp"><strong>${h(r.sp.ten)}</strong> <span class="oms-mo mono">${r.sp.ma}</span>${chiTiet}<div class="oms-mo chi-hep">Tồn ${so(r.co)} · giữ cho đơn ${so(r.g)}</div></td>
      <td class="phai an-m">${so(r.co)}</td><td class="phai an-m">${r.g ? so(r.g) : '—'}</td>
      <td class="phai"><span class="${cb < 0 ? 'chu-do' : ''}">${so(cb)}</span><span class="vach" aria-hidden="true"><i class="${lopVach}" style="width:${Math.max(0, Math.min(100, cb / (nguong * 4) * 100))}%"></i></span><div class="oms-mo${duBan !== null && duBan < 7 ? ' chu-do' : ''}">${chuDu}</div></td>
      <td class="phai an-l">${r.v ? '+' + so(r.v) : '—'}</td>
      <td><span class="chip ${LOP_TON[tt.lop]}"><i></i>${tt.nhan}</span>${!wsel && tt.muc > 1 ? `<div class="oms-mo">kho ${KHO[r.xau.w].ngan}</div>` : ''}${goiY ? `<div class="oms-mo">gợi ý nhập ${so(goiY)}${wsel ? '' : ' · kho ' + KHO[xet.w].ngan}</div>` : ''}</td>
      <td class="an-l"><button type="button" class="nut nut-nho nw" data-act="mo-phieu" data-loai="nhap" data-sp="${r.sp.ma}" data-kho="${goiY ? xet.w : wDau}"${goiY ? ` data-sl="${goiY}"` : ''} aria-label="Lập phiếu kho cho ${h(r.sp.ten)}">Phiếu kho</button></td></tr>`;
  }).join('');
  const ph = S.phieu.filter(p => !wsel || p.wh === wsel);
  $('#kho-phieu').innerHTML = ph.length ? `<ul class="oms-ds">${ph.map(p => `<li><div><span class="mono dam">${p.id}</span> → ${h(KHO[p.wh].ten)}<div class="oms-mo">${p.items.map(i => `${h(SPMAP[i.ma].ten)} × ${so(i.sl)}`).join(', ')}</div><div class="oms-mo">Dự kiến ${ngay(p.eta)} · ${h(p.ghi)}</div></div><button type="button" class="nut nut-nho" data-act="nhan-phieu" data-id="${p.id}">Đã về — nhận hàng</button></li>`).join('')}</ul>` : '<p class="oms-mo">Không có phiếu nào đang về.</p>';
  const LOAI = ['Nhập', 'Xuất', 'Xuất cho đơn', 'Chuyển đi', 'Nhận hàng về', 'Hoàn về kho'];
  $('#kho-so-loc').innerHTML = [['', 'Tất cả'], ...LOAI.map(l => [l, l])].map(([l, t]) => chipLoc('so-loc', 'loai', l, S.kho.loai === l, t)).join('');
  const dong = S.so.filter(e => (!S.kho.loai || e.loai === S.kho.loai) && (!wsel || e.wh === wsel || e.wh2 === wsel));
  $('#kho-so').innerHTML = dong.length ? `<div class="bang-cuon"><table class="bang bang-nho"><thead><tr><th>Lúc</th><th class="an-s">Loại</th><th>Sản phẩm</th><th class="phai">SL</th><th>Kho</th><th class="an-m">Người</th><th class="an-l">Ghi chú</th></tr></thead><tbody>${dong.slice(0, S.kho.xem).map(e =>
    `<tr><td class="mono nw">${ngay(e.t).slice(0, 5)}<div class="oms-mo">${gio(e.t)}</div></td><td class="an-s">${e.loai}</td><td>${h(SPMAP[e.ma].ten)}</td><td class="phai ${e.sl > 0 ? 'chu-xanh' : 'chu-do'}">${e.sl > 0 ? '+' : '−'}${so(Math.abs(e.sl))}</td><td>${KHO[e.wh].ngan}${e.wh2 ? ' → ' + KHO[e.wh2].ngan : ''}</td><td class="mono an-m">${e.ai}</td><td class="oms-mo an-l">${h(e.ghi || '')}</td></tr>`).join('')}</tbody></table></div>${dong.length > S.kho.xem ? `<div class="phan-trang"><span>Đang hiện ${so(S.kho.xem)}/${so(dong.length)} dòng</span><button type="button" class="nut nut-nho" data-act="so-them">Xem thêm ${so(Math.min(12, dong.length - S.kho.xem))} dòng</button></div>` : ''}` : '<p class="the-than oms-mo">Chưa có dòng nào.</p>';
}
// Phiếu kho: biểu mẫu trong ngăn kéo, không hộp thoại
function nganPhieu(_, o) {
  const {loai = 'nhap', ma = SP[0].ma, wh = S.kho.wh || 'HN', sl = ''} = o || {};
  const khoOpt = chon => Object.entries(KHO).map(([w, k]) => `<option value="${w}"${w === chon ? ' selected' : ''}>${h(k.ten)}</option>`).join('');
  return `<div class="ngan-dau"><div><p class="oms-mo">Kho · ghi vào sổ nhập xuất</p><h2 id="ngan-tieu-de">Phiếu kho</h2></div>${nutDong}</div>
  <form class="oms-form" id="f-phieu" novalidate>
    <div class="ngan-than"><div class="bm">
      <div class="phan-doan" role="radiogroup" aria-label="Loại phiếu">${[['nhap', 'Nhập kho'], ['xuat', 'Xuất kho'], ['chuyen', 'Chuyển kho']].map(([v, t]) => `<label><input type="radio" name="loai" value="${v}"${v === loai ? ' checked' : ''}><span>${t}</span></label>`).join('')}</div>
      <div class="truong"><label for="p-sp">Sản phẩm</label><select id="p-sp" name="sp" class="o-nhap">${SP.map(s => `<option value="${s.ma}"${s.ma === ma ? ' selected' : ''}>${h(s.ten)} — ${s.ma}</option>`).join('')}</select></div>
      <div class="bm-hang">
        <div class="truong"><label for="p-kho" id="p-kho-nhan">Kho</label><select id="p-kho" name="kho" class="o-nhap">${khoOpt(wh)}</select></div>
        <div class="truong" id="p-kho2-o"><label for="p-kho2">Đến kho</label><select id="p-kho2" name="kho2" class="o-nhap">${khoOpt(wh === 'HN' ? 'US' : 'HN')}</select></div>
      </div>
      <div class="truong"><label for="p-sl">Số lượng</label><input id="p-sl" name="sl" class="o-nhap" inputmode="numeric" autocomplete="off" placeholder="Ví dụ: 50" value="${h(sl || '')}" aria-describedby="p-goi-y p-loi" data-dau><p class="goi-y" id="p-goi-y"></p><p class="loi-truong" id="p-loi" role="alert"></p></div>
      <div class="truong"><label for="p-ghi">Ghi chú</label><input id="p-ghi" name="ghi" class="o-nhap" maxlength="120" autocomplete="off" placeholder="Ví dụ: nhà cung cấp giao, xuất mẫu cho KOL"></div>
    </div></div>
    <div class="ngan-chan"><button type="button" class="nut" data-act="huy-form">Huỷ</button><button type="submit" class="nut nut-chinh day">Lưu phiếu</button></div>
  </form>`;
}
function goiYPhieu(f) {
  const v = new FormData(f), l = v.get('loai'), w = v.get('kho'), m = v.get('sp'), o = S.ton[w][m], gg = bangGiu()[w + '|' + m] || 0;
  $('#p-kho2-o', f).hidden = l !== 'chuyen';
  $('#p-kho-nhan', f).textContent = l === 'chuyen' ? 'Từ kho' : 'Kho';
  $('#p-goi-y', f).textContent = `${KHO[w].ten}: tồn ${so(o.co)} · đang giữ cho đơn ${so(gg)} · có thể bán ${so(o.co - gg)}`;
  $('#p-loi', f).textContent = '';
  $('#p-sl', f).removeAttribute('aria-invalid');
}
function luuPhieu(f) {
  const v = new FormData(f), l = v.get('loai'), m = v.get('sp'), w = v.get('kho'), w2 = v.get('kho2'), ghi = String(v.get('ghi') || '').trim();
  const raw = String(v.get('sl') || '').replace(/[.\s]/g, '');
  const loi = t => { $('#p-loi', f).textContent = t; $('#p-sl', f).setAttribute('aria-invalid', 'true'); $('#p-sl', f).focus(); };
  if (!/^\d+$/.test(raw) || +raw < 1 || +raw > 100000) return loi('Số lượng phải là số nguyên từ 1 đến 100.000.');
  const sl = +raw, o = S.ton[w][m], gg = bangGiu()[w + '|' + m] || 0, sp = SPMAP[m];
  if (l === 'chuyen' && w === w2) return loi('Chọn hai kho khác nhau.');
  if (l !== 'nhap' && sl > o.co - gg) return loi(`${KHO[w].ten} chỉ xuất được ${so(Math.max(0, o.co - gg))} ${sp.ten}: tồn ${so(o.co)}, trong đó ${so(gg)} đang giữ cho đơn chờ giao.`);
  if (l === 'nhap') { o.co += sl; ghiSo({loai: 'Nhập', ma: m, sl, wh: w, ghi: ghi || 'Nhập kho'}); toast(`Đã nhập ${so(sl)} ${sp.ten} vào ${KHO[w].ten}.`); }
  else if (l === 'xuat') { o.co -= sl; ghiSo({loai: 'Xuất', ma: m, sl: -sl, wh: w, ghi: ghi || 'Xuất kho'}); toast(`Đã xuất ${so(sl)} ${sp.ten} khỏi ${KHO[w].ten}.`); }
  else {
    o.co -= sl;
    const id = maPhieu('PC', Date.now(), ++S.demPhieu);
    S.phieu.push({id, wh: w2, items: [{ma: m, sl}], eta: Date.now() + 3 * DAY, ghi: `Chuyển từ ${KHO[w].ten}${ghi ? ' — ' + ghi : ''}`});
    ghiSo({loai: 'Chuyển đi', ma: m, sl: -sl, wh: w, wh2: w2, ghi: 'Phiếu ' + id});
    toast(`Đã tạo phiếu chuyển ${id}: ${so(sl)} ${sp.ten} sang ${KHO[w2].ten}. Hàng nằm ở mục "Hàng đang về" tới khi kho nhận.`);
  }
  capNhat();
  veNgan();
}
function nhanPhieu(id) {
  const p = S.phieu.find(x => x.id === id);
  if (!p) return;
  for (const i of p.items) { S.ton[p.wh][i.ma].co += i.sl; ghiSo({loai: 'Nhận hàng về', ma: i.ma, sl: i.sl, wh: p.wh, ghi: 'Phiếu ' + p.id}); }
  S.phieu = S.phieu.filter(x => x !== p);
  const ket = S.don.some(d => d.thieu && d.pha === 'tao' && d.wh === p.wh);
  toast(`${KHO[p.wh].ten} đã nhận phiếu ${p.id}.${ket ? ' Đơn đang đứng vì thiếu hàng sẽ giao được ở lần "Cập nhật từ hãng" tới.' : ''}`);
  capNhat();
}

// ---------- Kênh bán & Page ----------
function mountKenh() {
  $('#v-kenh').innerHTML = `
  <header class="trang-dau">
    <div><h1>Kênh bán &amp; Page</h1><p>Page và gian hàng nối qua Pancake; số liệu tính từ đơn đã về CRM.</p></div>
    <div class="hanh-dong"><button type="button" class="nut nut-chinh" data-act="them-kenh">+ Thêm kênh</button></div>
  </header>
  <div class="oms-kpi" id="kn-kpi"></div>
  <div class="oms-dong-tien" id="kn-tien"></div>
  <div class="oms-chips" id="kn-loc" role="group" aria-label="Lọc nền tảng"></div>
  <div class="kenh-luoi" id="kn-luoi"></div>
  <section class="the cq"><div class="the-dau"><h2>Đơn 14 ngày theo nền tảng</h2><div class="chu-giai" id="kn-chu-giai"></div></div><div class="the-than" id="kn-bieu-do"></div></section>`;
}
const trangKenh = k => ({ok: '<span class="chip chip-tot"><i></i>Đã kết nối</span>', loi: '<span class="chip chip-xau"><i></i>Mất kết nối</span>', ngat: '<span class="chip chip-nhat"><i></i>Đã ngắt</span>', dang: '<span class="chip chip-cho chip-dang"><i></i>Đang cấp quyền…</span>'})[k.trang];
// "+3 đơn", "−12% doanh số": tăng xanh, giảm đỏ, kèm chữ nên không chỉ dựa vào màu
function soSanh7(s) {
  const lop = x => x > 0 ? 'len' : x < 0 ? 'xuong' : '';
  const don = s.bay - s.bayTruoc, dt = s.dtTruoc ? (s.dt - s.dtTruoc) / s.dtTruoc : null;
  const chuDon = don ? `${don > 0 ? '+' : '−'}${so(Math.abs(don))} đơn` : 'số đơn như cũ';
  const chuDt = dt === null ? (s.dt ? 'mới có doanh số' : 'chưa có doanh số') : `${dt > 0 ? '+' : ''}${phanTram(dt)} doanh số`;
  return `<p class="kenh-so-sanh">So với 7 ngày trước: <span class="${lop(don)}">${chuDon}</span> · <span class="${lop(dt)}">${chuDt}</span></p>`;
}
function theKenh(k) {
  const s = soLieuKenh(k);
  return `<article class="kenh${k.trang === 'loi' ? ' kenh-loi' : ''}" data-kenh="${k.id}" data-don7="${s.bay}" data-don7-truoc="${s.bayTruoc}" tabindex="0" style="--c:${NEN[k.nen].mau}" aria-label="${h(k.ten)}">
    <div class="kenh-dau">${nenChip(k)}${trangKenh(k)}</div>
    <h3 class="kenh-ten">${h(k.ten)}</h3>
    <p class="oms-mo">${MARKETS[k.mkt].ten} · ${MARKETS[k.mkt].cur} · phụ trách <span class="mono">${k.pt}</span></p>
    <dl class="kenh-so"><div><dt>Hôm nay</dt><dd>${s.homNay}</dd></div><div><dt>7 ngày</dt><dd>${s.bay}</dd></div><div><dt>Hoàn</dt><dd>${s.tile}%</dd></div><div><dt>${k.nen === 'fb' ? 'Hội thoại' : 'Tin nhắn'}</dt><dd>${k.hoiThoai}</dd></div></dl>
    <p class="kenh-dt">Doanh số 7 ngày <strong>${tien(s.dt, s.cur)}</strong></p>
    ${soSanh7(s)}
    ${k.trang === 'loi' ? `<p class="kenh-canh">${h(k.loi)}</p>` : ''}${!k.tu && k.trang === 'ok' ? '<p class="kenh-canh nhe">Đang tắt tự kéo đơn</p>' : ''}
  </article>`;
}
function bieuDo() {
  const now = Date.now(), ngayDs = Array.from({length: 14}, (_, i) => ngay(now - (13 - i) * DAY)), nens = S.kn.nen ? [S.kn.nen] : Object.keys(NEN);
  const idx = Object.fromEntries(ngayDs.map((n, i) => [n, i])), dem = ngayDs.map(() => Object.fromEntries(nens.map(n => [n, 0])));
  for (const d of S.don) { const i = idx[d.nt]; if (i === undefined) continue; const nen = kenhTheoId(d.kenh).nen; if (nen in dem[i]) dem[i][nen]++; }
  const tong = dem.map(o => Object.values(o).reduce((a, b) => a + b, 0)), max = Math.max(1, ...tong);
  const bang = `<details class="cach-tinh"><summary>Số liệu đối chiếu</summary><div class="bang-cuon"><table class="bang bang-nho"><thead><tr><th>Ngày</th><th class="phai">Tổng</th>${nens.map(n => `<th class="phai an-l">${NEN[n].ten}</th>`).join('')}</tr></thead><tbody>${dem.map((o, i) =>
    `<tr><td>${ngayDs[i].slice(0, 5)}</td><td class="phai">${tong[i]}</td>${nens.map(n => `<td class="phai an-l">${o[n]}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
  return `<div class="bieu-do" role="img" tabindex="0" aria-label="Số đơn mỗi ngày trong 14 ngày qua, chia theo nền tảng: tổng ${so(tong.reduce((a, b) => a + b, 0))} đơn, ngày nhiều nhất ${so(Math.max(...tong))} đơn">${dem.map((o, i) =>
    `<div class="cot" title="${ngayDs[i].slice(0, 5)}: ${tong[i]} đơn${nens.filter(n => o[n]).map(n => ` · ${NEN[n].ten} ${o[n]}`).join('')}"><b>${tong[i] || ''}</b><div class="chong" style="height:${tong[i] / max * 100}%">${nens.filter(n => o[n]).map(n => `<span style="flex:${o[n]} 1 0;--c:${NEN[n].mau}"></span>`).join('')}</div></div>`).join('')}</div>
    <div class="truc" aria-hidden="true">${ngayDs.map(n => `<span>${n.slice(0, 5)}</span>`).join('')}</div>${bang}`;
}
function updKenh() {
  const ds = S.kenh.filter(k => !S.kn.nen || k.nen === S.kn.nen);
  let homNay = 0, bay = 0;
  const dt = {};
  for (const k of ds) { const s = soLieuKenh(k); homNay += s.homNay; bay += s.bay; if (s.dt) dt[s.cur] = (dt[s.cur] || 0) + s.dt; }
  const ok = ds.filter(k => k.trang === 'ok').length, loi = ds.filter(k => k.trang === 'loi').length;
  $('#kn-kpi').innerHTML = kpiO({nhan: 'Kênh đang kết nối', so: `${ok}/${ds.length}`}) + kpiO({nhan: 'Đơn hôm nay', so: homNay}) + kpiO({nhan: 'Đơn 7 ngày', so: bay}) +
    kpiO({nhan: 'Kênh cần xử lý', so: loi, lop: loi ? 'do' : '', phu: loi ? 'Mất kết nối với Pancake' : 'Không có'});
  $('#kn-tien').innerHTML = `<span>Doanh số 7 ngày theo loại tiền</span>${chipTien(dt) || '<span>— chưa có đơn</span>'}`;
  $('#kn-loc').innerHTML = [['', 'Tất cả', S.kenh.length], ...Object.entries(NEN).map(([n, x]) => [n, x.ten, S.kenh.filter(k => k.nen === n).length])]
    .map(([n, t, c]) => chipLoc('kn-loc', 'nen', n, S.kn.nen === n, (n ? `<i class="cham" style="--c:${NEN[n].mau}"></i>` : '') + t, c)).join('');
  $('#kn-luoi').innerHTML = ds.map(theKenh).join('') || '<p class="oms-mo">Chưa có kênh nào ở nền tảng này.</p>';
  $('#kn-chu-giai').innerHTML = Object.entries(NEN).filter(([n]) => !S.kn.nen || n === S.kn.nen).map(([, x]) => `<span class="nen" style="--c:${x.mau}"><i></i>${x.ten}</span>`).join('');
  $('#kn-bieu-do').innerHTML = bieuDo();
}
// Thêm kênh: biểu mẫu trong ngăn kéo; lưu xong ngăn kéo chuyển sang kênh mới đang chờ cấp quyền
function nganThemKenh() {
  return `<div class="ngan-dau"><div><p class="oms-mo">Kênh nối qua Pancake · bản demo giả lập bước cấp quyền</p><h2 id="ngan-tieu-de">Thêm kênh bán</h2></div>${nutDong}</div>
  <form class="oms-form" id="f-kenh" novalidate>
    <div class="ngan-than"><div class="bm">
      <div class="truong"><label for="k-nen">Nền tảng</label><select id="k-nen" name="nen" class="o-nhap">${Object.entries(NEN).map(([n, x]) => `<option value="${n}">${x.ten}</option>`).join('')}</select></div>
      <div class="truong"><label for="k-ten">Tên page hoặc gian hàng</label><input id="k-ten" name="ten" class="o-nhap" maxlength="60" autocomplete="off" placeholder="Ví dụ: KN Beauty Canada 2" aria-describedby="k-loi" data-dau><p class="loi-truong" id="k-loi" role="alert"></p></div>
      <div class="bm-hang">
        <div class="truong"><label for="k-mkt">Thị trường</label><select id="k-mkt" name="mkt" class="o-nhap">${Object.entries(MARKETS).map(([m, x]) => `<option value="${m}">${m} — ${x.ten} (${x.cur})</option>`).join('')}</select></div>
        <div class="truong"><label for="k-pt">Phụ trách</label><select id="k-pt" name="pt" class="o-nhap">${MKT.map(c => `<option>${c}</option>`).join('')}</select></div>
      </div>
    </div></div>
    <div class="ngan-chan"><button type="button" class="nut" data-act="huy-form">Huỷ</button><button type="submit" class="nut nut-chinh day">Kết nối qua Pancake</button></div>
  </form>`;
}
function luuKenh(f) {
  const v = new FormData(f), ten = String(v.get('ten') || '').trim(), o = $('#k-ten', f);
  const loi = t => { $('#k-loi', f).textContent = t; o.setAttribute('aria-invalid', 'true'); o.focus(); };
  if (!ten) return loi('Nhập tên page hoặc gian hàng.');
  if (S.kenh.some(k => k.ten.toLowerCase() === ten.toLowerCase())) return loi('Đã có kênh trùng tên.');
  const nen = v.get('nen');
  const k = {id: 'k' + (++S.demKenh), nen, ten, mkt: v.get('mkt'), pt: v.get('pt'), w: 6, tu: true, trang: 'dang', hoiThoai: 0, ma: (nen === 'fb' ? 'pg_' : 'shop_') + '••••' + digits(4)};
  S.kenh.push(k); S.qc[k.id] = Array(KY_QC).fill(0); S.kn.nen = '';
  toast(`Đang chờ cấp quyền cho ${ten} trên Pancake…`);
  S.ngan = {loai: 'kenh', id: k.id, o: null, ve: null};
  renderNgan(true);
  capNhat();
  setTimeout(() => {
    if (!S.kenh.includes(k)) return;
    k.trang = 'ok';
    toast(`Đã kết nối ${ten}. Đơn của kênh này về ở lần đồng bộ tới.`);
    capNhat();
    if (S.ngan && S.ngan.id === k.id) renderNgan(false);
  }, TRE.themKenh);
}
function ketNoiLai(k) {
  k.trang = 'dang'; renderNgan(false); capNhat();
  setTimeout(() => {
    if (!S.kenh.includes(k)) return;
    k.trang = 'ok'; delete k.loi;
    toast(`Đã kết nối lại ${k.ten}. Lần đồng bộ tới kéo cả những đơn bị lỡ.`);
    capNhat();
    if (S.ngan && S.ngan.id === k.id) renderNgan(false);
  }, TRE.ketNoi);
}
function ngatKenh(k) {
  k.trang = 'ngat';
  toast(`Đã ngắt ${k.ten}. Đơn của kênh này không còn kéo về CRM.`);
  renderNgan(false); capNhat();
}

// ---------- Lãi theo page ----------
function mountLai() {
  $('#v-lai').innerHTML = `
  <header class="trang-dau">
    <div><h1>Lãi theo page</h1><p>Đơn đã giao trừ phí sàn, giá vốn, cước, quảng cáo và hoàn: page nào lãi, page nào lỗ.</p></div>
    <div class="hanh-dong"><div class="oms-chips" role="group" aria-label="Kỳ">${[7, 30].map(n => chipLoc('lp-ky', 'ky', n, false, n + ' ngày')).join('')}</div></div>
  </header>
  <div class="oms-kpi" id="lp-kpi"></div>
  <div class="oms-dong-tien" id="lp-tien"></div>
  <section class="the" id="lp-xu">
    <div class="the-dau"><h2>Lãi theo ngày</h2><div class="phai"><label class="oms-nhan-chon" for="lp-xu-page">Page</label><select id="lp-xu-page" class="o-nhap oms-gon"></select></div></div>
    <div class="the-than doc">
      <div id="lp-xu-hinh"></div>
      <p class="oms-mo" id="lp-xu-diem" aria-live="polite">Bấm vào biểu đồ rồi dùng phím ← → để xem từng ngày.</p>
      <details class="cach-tinh"><summary>Số liệu đối chiếu</summary><div class="bang-cuon"><table class="bang bang-nho" id="lp-xu-bang"></table></div></details>
    </div>
  </section>
  <div class="bang-hop cq">
    <div class="oms-chips" id="lp-xem-nhom" role="group" aria-label="Xem theo"></div>
    <div class="bang-cuon"><table class="bang"><thead id="lp-dau"></thead><tbody id="lp-than"></tbody></table></div>
    <p class="oms-ghi-bang" id="lp-ghi"></p>
  </div>
  <details class="cach-tinh"><summary>Cách tính (số minh hoạ, chưa chốt)</summary><ul>
    <li>Doanh số: đơn đã giao trong kỳ, quy về VND theo tỉ giá tạm cuối màn; thiếu tỉ giá thì không tính, không đoán.</li>
    <li>Phí sàn: TikTok Shop 8%, Shopee 9%, Lazada 10% doanh số; page Facebook và website không có.</li>
    <li>Giá vốn theo từng sản phẩm; cước theo tuyến và thị trường; đơn hoàn tính cước hai chiều.</li>
    <li>Quảng cáo lấy theo page từ báo cáo Marketing, nộp bằng tiền Việt (ADR-047).</li>
    <li>Theo sản phẩm là lãi gộp: chưa trừ quảng cáo, vì quảng cáo tính theo page.</li>
  </ul></details>
  <section class="the">
    <div class="the-dau"><h2>Tỉ giá tạm (chỉ để minh hoạ)</h2></div>
    <div class="the-than doc">
      <p class="oms-mo">Khởi đầu bằng tỉ giá của bảng xếp hạng doanh số (settings); KRW cố ý để trống như ở đó. Sửa tại đây chỉ có hiệu lực trong trang này.</p>
      <div class="ti-gia">${TI_GIA_CO.map(c => `<label for="lp-tg-${c}">1 ${c} =<input id="lp-tg-${c}" class="o-nhap oms-gon${S.tiGia[c] ? '' : ' thieu'}" inputmode="numeric" autocomplete="off" value="${S.tiGia[c] ? so(S.tiGia[c]) : ''}" placeholder="chưa có"> ₫</label>`).join('')}</div>
      <p class="loi-truong" id="lp-tg-loi" role="alert"></p>
    </div>
  </section>`;
}
const laiO = (lai, cur) => lai === null ? `<span class="thieu-tg">Thiếu tỉ giá ${cur}</span>`
  : `<span class="${lai < 0 ? 'lo' : 'lai-duong'}">${vndGon(lai)}</span>${lai < 0 ? '<div><span class="tac">Lỗ</span></div>' : ''}`;
function updLai() {
  const l = S.lp;
  for (const b of $$('[data-act="lp-ky"]')) b.setAttribute('aria-pressed', String(+b.dataset.ky === l.ky));
  $('#lp-xem-nhom').innerHTML = [['page', 'Theo page'], ['sp', 'Theo sản phẩm'], ['tt', 'Theo thị trường']]
    .map(([x, t]) => chipLoc('lp-xem', 'xem', x, l.xem === x, t)).join('');
  const trang = S.kenh.map(k => laiKhoang(k, 0, l.ky)), coTg = trang.filter(r => r.dsVnd !== null);
  // Ô Lãi là tổng lãi từng ngày (làm tròn từng ngày), đúng bằng tổng của biểu đồ; cột Lãi của page tính cả kỳ một lần
  const ds = coTg.reduce((s, r) => s + r.dsVnd, 0), qc = trang.reduce((s, r) => s + r.qc, 0), lai = chuoiLai(l.ky, '').tong;
  const lo = coTg.filter(r => r.lai < 0);
  $('#lp-kpi').innerHTML = kpiO({nhan: 'Doanh số (≈ VND)', so: `<span title="${vnd(ds)}">${vndGon(ds)}</span>`, phu: `${l.ky} ngày, đơn đã giao`, loc: 'ds'}) +
    kpiO({nhan: 'Quảng cáo', so: vndGon(qc), phu: `ROAS ${qc ? nf1.format(ds / qc) : '—'}`, loc: 'qc'}) +
    kpiO({nhan: 'Lãi', so: `<span title="${vnd(lai)}">${vndGon(lai)}</span>`, lop: lai < 0 ? 'do' : 'xanh', phu: ds ? 'Biên ' + phanTram(lai / ds) : '', loc: 'lai', soTho: lai}) +
    kpiO({nhan: 'Page lỗ', so: lo.length, lop: lo.length ? 'do' : '', loc: 'lo', phu: lo.length ? lo.map(r => h(r.k.ten)).join(', ') : 'Không có'});
  const goc = {};
  for (const r of trang) if (r.dsMinor) goc[r.cur] = (goc[r.cur] || 0) + r.dsMinor;
  $('#lp-tien').innerHTML = `<span>Doanh số gốc trong kỳ</span>${chipTien(goc) || '<span>— chưa có đơn giao</span>'}`;
  const thieu = trang.filter(r => r.dsVnd === null && r.dsMinor).map(r => `${r.k.ten} (thiếu tỉ giá ${r.cur})`);
  let ghi = thieu.length ? `Chưa tính: ${thieu.join(', ')}.` : '';
  if (l.xem === 'page') {
    $('#lp-dau').innerHTML = '<tr><th>Page</th><th class="phai an-s">Doanh số</th><th class="phai an-l">Giá vốn, cước, phí</th><th class="phai an-m">Quảng cáo</th><th class="phai">Lãi</th><th class="phai an-m">Biên</th><th class="phai an-l">ROAS</th></tr>';
    $('#lp-than').innerHTML = [...trang].sort((a, b) => (b.lai ?? -Infinity) - (a.lai ?? -Infinity)).map(r => {
      const am = r.lai !== null && r.lai < 0;
      return `<tr class="bam${S.ngan && S.ngan.id === r.k.id ? ' dang-mo' : ''}" data-lai="${r.k.id}" data-lai-vnd="${r.lai ?? ''}" data-lo="${am ? 1 : 0}" tabindex="0">
        <td>${nenChip(r.k)}<div class="dam">${h(r.k.ten)}</div><div class="oms-mo">${r.k.mkt} · ${r.don} đơn giao</div>${r.dsMinor ? `<div class="oms-mo chi-s">${tien(r.dsMinor, r.cur)}</div>` : ''}</td>
        <td class="phai an-s">${r.dsMinor ? tien(r.dsMinor, r.cur) : '—'}<div class="oms-mo">${r.dsVnd !== null && r.dsMinor ? '≈ ' + vndGon(r.dsVnd) : ''}</div></td>
        <td class="phai an-l">${vndGon(r.von + r.cuoc + r.phiSan + r.hoan)}</td><td class="phai an-m">${vndGon(r.qc)}</td>
        <td class="phai">${laiO(r.lai, r.cur)}</td>
        <td class="phai an-m">${r.lai !== null && r.dsVnd ? phanTram(r.lai / r.dsVnd) : '—'}</td>
        <td class="phai an-l">${r.qc && r.dsVnd !== null ? nf1.format(r.dsVnd / r.qc) : '—'}</td></tr>`;
    }).join('');
  } else if (l.xem === 'sp') {
    const kq = laiTheoSp(l.ky);
    if (kq.thieu) ghi = `Chưa tính ${kq.thieu} đơn thiếu tỉ giá.`;
    ghi = (ghi ? ghi + ' ' : '') + 'Theo sản phẩm là lãi gộp: chưa trừ quảng cáo (quảng cáo tính theo page).';
    $('#lp-dau').innerHTML = '<tr><th>Sản phẩm</th><th class="phai an-m">Bán</th><th class="phai">Doanh số ≈</th><th class="phai an-l">Giá vốn</th><th class="phai an-m">Cước, phí, hoàn</th><th class="phai">Lãi gộp</th><th class="phai an-m">Biên</th></tr>';
    $('#lp-than').innerHTML = kq.ds.sort((a, b) => b.lai - a.lai).map(r => `<tr data-sp="${r.sp.ma}">
      <td><strong>${h(r.sp.ten)}</strong> <span class="oms-mo mono">${r.sp.ma}</span></td><td class="phai an-m">${so(r.sl)}</td><td class="phai">${vndGon(r.dsVnd)}</td>
      <td class="phai an-l">${vndGon(r.von)}</td><td class="phai an-m">${vndGon(r.phi)}</td><td class="phai">${laiO(r.lai, '')}</td>
      <td class="phai an-m">${r.dsVnd ? phanTram(r.lai / r.dsVnd) : '—'}</td></tr>`).join('');
  } else {
    $('#lp-dau').innerHTML = '<tr><th>Thị trường</th><th class="phai">Doanh số gốc</th><th class="phai an-m">≈ VND</th><th class="phai an-l">Chi phí (gồm quảng cáo)</th><th class="phai">Lãi</th><th class="phai an-m">Biên</th></tr>';
    $('#lp-than').innerHTML = laiTheoTt(l.ky).sort((a, b) => (b.lai ?? -Infinity) - (a.lai ?? -Infinity)).map(r => `<tr data-tt="${r.m}">
      <td><strong>${MARKETS[r.m].ten}</strong> <span class="oms-mo">${r.m} · ${r.don} đơn giao</span></td><td class="phai">${r.dsMinor ? tien(r.dsMinor, r.cur) : '—'}</td>
      <td class="phai an-m">${r.dsVnd !== null ? vndGon(r.dsVnd) : '—'}</td><td class="phai an-l">${vndGon(r.chiPhi)}</td><td class="phai">${laiO(r.lai, r.cur)}</td>
      <td class="phai an-m">${r.lai !== null && r.dsVnd ? phanTram(r.lai / r.dsVnd) : '—'}</td></tr>`).join('');
  }
  $('#lp-ghi').textContent = ghi;
  updXuHuong();
}
// Biểu đồ đường lãi theo ngày: khuôn SVG của màn Thống kê (statistics_charts.line, viewBox 680×210), thêm đường 0 vì lãi
// âm được; nhãn số ở điểm đầu, cuối, cao nhất, thấp nhất; phím ← → Home End đi từng ngày.
const XU = {w: 680, h: 210, l: 38, t: 14, pw: 624, ph: 162};
function hinhXuHuong(c, ten) {
  const n = c.lai.length, max = Math.max(0, ...c.lai), min = Math.min(0, ...c.lai), rong = max - min || 1;
  const x = i => XU.l + XU.pw * i / Math.max(n - 1, 1), y = v => XU.t + XU.ph * (max - v) / rong;
  const nhan = (v, i) => n <= 12 || i === 0 || i === n - 1 || v === max || v === min;
  const ngang = i => n <= 12 || i % 7 === (n - 1) % 7;
  const neo = i => n > 1 && i === 0 ? 'start' : n > 1 && i === n - 1 ? 'end' : 'middle';   // nhãn ở hai mép không lòi ra ngoài
  const tieuDe = `Lãi theo ngày · ${ten} · ${n} ngày: tổng ${vnd(c.tong)}, cao nhất ${vnd(max)}, thấp nhất ${vnd(min)}`;
  return `<svg class="oms-xu" viewBox="0 0 ${XU.w} ${XU.h}" role="img" tabindex="0" aria-label="${h(tieuDe)}" aria-describedby="lp-xu-diem"><title>${h(tieuDe)}</title>
    <line x1="${XU.l}" y1="${y(0).toFixed(2)}" x2="${XU.l + XU.pw}" y2="${y(0).toFixed(2)}" class="oms-xu-truc"/>
    <polyline points="${c.lai.map((v, i) => `${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ')}" class="oms-xu-duong"/>
    ${c.lai.map((v, i) => `<circle cx="${x(i).toFixed(2)}" cy="${y(v).toFixed(2)}" r="4" data-i="${i}" class="${v < 0 ? 'am' : ''}${S.lp.diem === i ? ' dang-chon' : ''}"><title>${ngay(c.ngay[i])}: ${vnd(v)}</title></circle>${nhan(v, i) ? `<text x="${x(i).toFixed(2)}" y="${(v < 0 ? Math.min(XU.t + XU.ph + 14, y(v) + 18) : Math.max(10, y(v) - 9)).toFixed(2)}" text-anchor="${neo(i)}" class="oms-xu-so">${vndGon(v).replace(' ₫', '')}</text>` : ''}${ngang(i) ? `<text x="${x(i).toFixed(2)}" y="${XU.h - 8}" text-anchor="${neo(i)}" class="oms-xu-ngay">${ngay(c.ngay[i]).slice(0, 5)}</text>` : ''}`).join('')}
  </svg>`;
}
function updXuHuong() {
  const l = S.lp, chon = $('#lp-xu-page');
  if (l.page && !kenhTheoId(l.page)) l.page = '';
  chon.innerHTML = '<option value="">Tất cả page có tỉ giá</option>' + S.kenh.map(k => `<option value="${k.id}">${h(k.ten)}</option>`).join('');
  chon.value = l.page;
  const c = chuoiLai(l.ky, l.page), ten = l.page ? kenhTheoId(l.page).ten : 'tất cả page';
  if (l.diem !== null && l.diem >= c.lai.length) l.diem = null;
  $('#lp-xu-hinh').innerHTML = c.coTg ? hinhXuHuong(c, ten)
    : `<div class="bao bao-cho"><span class="bao-ic">!</span><div>Chưa vẽ được: ${h(ten)} thiếu tỉ giá ${MARKETS[kenhTheoId(l.page).mkt].cur}. Nhập ở bảng "Tỉ giá tạm" cuối màn.</div></div>`;
  $('#lp-xu-bang').innerHTML = `<thead><tr><th>Ngày</th><th class="phai">Lãi</th></tr></thead><tbody>${c.lai.map((v, i) =>
    `<tr data-ngay="${isoNgay(c.ngay[i])}" data-lai="${v}"><td>${ngay(c.ngay[i])}</td><td class="phai${v < 0 ? ' lo' : ''}">${vnd(v)}</td></tr>`).join('')}</tbody><tfoot><tr><td>Tổng ${c.lai.length} ngày</td><td class="phai">${vnd(c.tong)}</td></tr></tfoot>`;
  if (l.diem !== null) docDiem(c);
}
function docDiem(c = chuoiLai(S.lp.ky, S.lp.page)) {
  const i = S.lp.diem;
  $('#lp-xu-diem').textContent = `${ngay(c.ngay[i])}: lãi ${vnd(c.lai[i])}`;
  for (const o of $$('#lp-xu-hinh circle')) o.classList.toggle('dang-chon', +o.dataset.i === i);
}
function diDiem(buoc) {
  const n = S.lp.ky, i = S.lp.diem;
  S.lp.diem = buoc === 'dau' ? 0 : buoc === 'cuoi' ? n - 1 : Math.min(n - 1, Math.max(0, (i ?? (buoc > 0 ? -1 : n)) + buoc));
  docDiem();
}
function doiTiGia(input) {
  const cur = input.id.slice('lp-tg-'.length), raw = input.value.replace(/[\s.]/g, ''), loi = $('#lp-tg-loi');
  if (!raw) { delete S.tiGia[cur]; loi.textContent = ''; }
  else if (!/^\d+$/.test(raw) || +raw <= 0 || +raw > 1e7) {
    loi.textContent = `Tỉ giá ${cur} phải là số nguyên dương (₫), ví dụ 25.500.`;
    input.value = S.tiGia[cur] ? so(S.tiGia[cur]) : '';
    return;
  } else { S.tiGia[cur] = +raw; input.value = so(+raw); loi.textContent = ''; }
  input.classList.toggle('thieu', !S.tiGia[cur]);
  capNhat();
}

// ---------- Ngăn kéo chi tiết ----------
function khoiThanhToan(d) {
  if (d.nguon === 'san') {
    const nen = kenhTheoId(d.kenh).nen;
    return `<div class="khoi-tt"><p>${badgeTien(d)} Tiền do ${NEN[nen].ten} thu hộ, về theo kỳ trả của sàn sau khi trừ phí ${phanTram(PHI_SAN[nen])}.</p></div>`;
  }
  const t = d.tien, con = conLai(d);
  if ((NHOM.hoan.includes(d.tt) || d.tt === 'Hủy trước giao') && !t.daThu) return `<div class="khoi-tt"><p>${badgeTien(d)} Đơn không giao thành công — không tính công nợ.</p></div>`;
  const phaiThu = laPhaiThu(d), nut = [];
  if (phaiThu && con > 0) nut.push(`<button type="button" class="nut nut-nho" data-act="cn-nhac" data-id="${d.id}">Nhắc khách</button>`, `<button type="button" class="nut nut-nho nut-chinh" data-act="cn-ghi" data-id="${d.id}">Ghi nhận tiền</button>`);
  if (t.tt === TT_TIEN.DU && !t.veTk) nut.push(`<button type="button" class="nut nut-nho" data-act="cn-ve-tk" data-id="${d.id}">Xác nhận về TK</button>`);
  return `<div class="khoi-tt"><dl class="tt-luoi">
      <dt>Trạng thái</dt><dd>${badgeTien(d)}${t.veTk ? ' ' + chipVeTk : ''}</dd>
      <dt>PTTT</dt><dd>${h(t.pttt || '—')}</dd>
      <dt>Đã thu</dt><dd>${tien(t.daThu, d.cur)}</dd>
      <dt>Còn phải thu</dt><dd class="dam">${tien(con, d.cur)}${phaiThu && con ? ` · trễ ${tuoiNo(d)} ngày` : ''}</dd>
      ${t.nhac ? `<dt>Đã nhắc</dt><dd>${t.nhac} lần · lần cuối ${ngay(t.nhacLuc)}</dd>` : ''}
    </dl>${nut.length ? `<div class="hang">${nut.join('')}</div>` : ''}${!phaiThu && con > 0 ? '<p class="ghi-nho">Đơn chưa giao xong nên chưa tính vào công nợ.</p>' : ''}<p class="ghi-nho">Bản thật: ai ghi nhận tiền, ai xác nhận Đã về TK chưa chốt (H7).</p></div>`;
}
function nganDon(id) {
  const d = S.donMap[id], k = S.khMap[d.kh], kn = kenhTheoId(d.kenh), tac = laTac(d);
  const nut = [];
  if (!KET_THUC.has(d.pha)) nut.push(`<button type="button" class="nut nut-chinh" data-act="buoc-don">${d.pha === 'vang' ? 'Đã gọi khách — hẹn phát lại' : 'Cập nhật từ hãng'}</button>`);
  if (d.pha === 'hoanve') nut.push('<button type="button" class="nut" disabled>Nhận hàng hoàn vào kho</button><span class="oms-mo">Chờ hãng báo đã hoàn về kho.</span>');
  if (d.pha === 'daHoan' && !d.daNhanHoan) nut.push('<button type="button" class="nut nut-chinh" data-act="nhan-hoan">Nhận hàng hoàn vào kho</button>');
  if (KET_THUC.has(d.pha) && !(d.pha === 'daHoan' && !d.daNhanHoan)) nut.push('<span class="oms-mo">Đơn đã kết thúc — hãng không còn gửi tin.</span>');
  return `<div class="ngan-dau"><div><p class="oms-mo mono">${d.pck} · từ Pancake</p><h2 id="ngan-tieu-de">${d.id}</h2><div class="hang-chip">${badge(d.tt)}${tac ? `<span class="tac">Tắc ${soNgayIm(d)} ngày</span>` : ''}</div></div>${nutDong}</div>
  <div class="ngan-than">
    ${d.thieu && d.pha === 'tao' ? `<div class="bao bao-xau"><span class="bao-ic">!</span><div class="oms-bao-than"><div>${KHO[d.wh].ten} chưa đủ hàng cho đơn này. Nhập kho hoặc nhận phiếu đang về rồi bấm "Cập nhật từ hãng".</div><button type="button" class="nut nut-nho" data-view="kho">Mở Kho</button></div></div>` : ''}
    <dl class="tt-luoi">
      <dt>Khách</dt><dd><button type="button" class="link" data-act="mo-khach" data-id="${k.id}">${h(k.ten)}</button> <span class="oms-mo">${h(k.sdt)}</span></dd>
      <dt>Giao tới</dt><dd>${h(k.city)}, ${MARKETS[d.mkt].ten}</dd>
      <dt>Kênh</dt><dd>${nenChip(kn)} ${h(kn.ten)}</dd>
      <dt>Sale · CSKH</dt><dd><span class="mono">${d.sale}</span> · <span class="mono">${d.cskh}</span></dd>
      <dt>Kho xuất</dt><dd>${KHO[d.wh].ten}</dd>
      <dt>Hãng</dt><dd>${h(d.hang)} · <span class="mono">${h(d.trk)}</span></dd>
    </dl>
    <table class="bang-sp"><tbody>${d.items.map(i => `<tr><td>${h(SPMAP[i.ma].ten)} <span class="oms-mo mono">${i.ma}</span></td><td class="phai">× ${i.sl}</td><td class="phai">${tien(i.gia * i.sl, d.cur)}</td></tr>`).join('')}<tr class="tong"><td>Tổng</td><td></td><td class="phai">${tien(d.tong, d.cur)}</td></tr></tbody></table>
    <h3 class="tieu-de-nho">Thanh toán</h3>
    ${khoiThanhToan(d)}
    <h3 class="tieu-de-nho">Hành trình</h3>
    <ol class="dong-tg">${[...d.sk].reverse().map(e => `<li${e.noiBo ? ' class="noi-bo"' : ''}><div class="sk">${h(e.x)}</div><div class="tg">${ngayGio(e.t)} · <span class="nguon">${h(e.n)}</span></div></li>`).join('')}</ol>
    <h3 class="tieu-de-nho">Ghi chú CSKH</h3>
    <div class="ghi-chu"><label class="vh" for="ghi-chu">Ghi chú CSKH</label><textarea id="ghi-chu" class="o-nhap" rows="2" placeholder="Ví dụ: đã gọi, khách hẹn nhận chiều thứ Bảy"></textarea><button type="button" class="nut nut-nho" data-act="luu-ghi-chu">Lưu ghi chú</button></div>
  </div>
  <div class="ngan-chan">${nut.join('')}</div>`;
}
function nganKenh(id) {
  const k = kenhTheoId(id), s = soLieuKenh(k), ds = S.don.filter(d => d.kenh === id).sort((a, b) => b.tao - a.tao).slice(0, 6);
  const san = k.nen === 'tt' || k.nen === 'sp' || k.nen === 'lz';
  return `<div class="ngan-dau"><div>${nenChip(k)}<h2 id="ngan-tieu-de">${h(k.ten)}</h2><div class="hang-chip">${trangKenh(k)}</div></div>${nutDong}</div>
  <div class="ngan-than">
    ${k.trang === 'loi' ? `<div class="bao bao-xau"><span class="bao-ic">!</span><div>${h(k.loi)}</div></div>` : ''}
    <dl class="tt-luoi">
      <dt>Thị trường</dt><dd>${MARKETS[k.mkt].ten} · ${MARKETS[k.mkt].cur}</dd>
      <dt>Mã ở Pancake</dt><dd class="mono">${k.ma}</dd>
      <dt><label for="k-phu-trach">Phụ trách</label></dt><dd><select id="k-phu-trach" class="o-nhap oms-gon" data-sua="phu-trach">${MKT.map(c => `<option${c === k.pt ? ' selected' : ''}>${c}</option>`).join('')}</select></dd>
      <dt>${k.nen === 'fb' ? 'Hội thoại' : 'Tin nhắn'} hôm nay</dt><dd>${k.hoiThoai} <span class="oms-mo">(từ Pancake)</span></dd>
      <dt>Đơn hôm nay · 7 ngày</dt><dd>${s.homNay} · ${s.bay} <span class="oms-mo">(7 ngày trước: ${s.bayTruoc})</span></dd>
      <dt>Doanh số 7 ngày</dt><dd class="dam">${tien(s.dt, s.cur)}</dd>
      <dt>Tỉ lệ hoàn</dt><dd>${s.tile}%</dd>
    </dl>
    <label class="cong-tac"><input type="checkbox" data-sua="tu-keo"${k.tu ? ' checked' : ''}> Tự kéo đơn của kênh này về bảng Vận đơn</label>
    ${san ? '<div class="bao oms-bao-nho"><div>Sàn có thể che SĐT và địa chỉ người mua; khi đó hai cột này để trống, CSKH liên hệ khách qua tin nhắn của sàn.</div></div>' : ''}
    <h3 class="tieu-de-nho">Đơn gần nhất</h3>
    <ul class="ds-don">${ds.map(d => `<li><button type="button" class="dong-don" data-act="mo-don" data-id="${d.id}"><span class="mono">${d.id}</span><span>${h(S.khMap[d.kh].ten)}</span>${badge(d.tt)}</button></li>`).join('') || '<li class="oms-mo">Chưa có đơn.</li>'}</ul>
  </div>
  <div class="ngan-chan">${k.trang === 'loi' || k.trang === 'ngat' ? '<button type="button" class="nut nut-chinh" data-act="ket-noi-lai">Kết nối lại</button>' : k.trang === 'dang' ? '<span class="oms-mo">Đang chờ cấp quyền trên Pancake…</span>' : '<button type="button" class="nut nut-nguy" data-act="ngat">Ngắt kết nối</button>'}</div>`;
}
function nganKhach(id) {
  const k = S.khMap[id], ds = S.don.filter(d => d.kh === id).sort((a, b) => b.tao - a.tao), kn = kenhTheoId(k.kenhDau), r = ruiRo(k, donTheoKhach());
  return `<div class="ngan-dau"><div><p class="oms-mo mono">${k.id} · từ Pancake</p><h2 id="ngan-tieu-de">${h(k.ten)}</h2><div class="hang-chip">${ds.length >= 2 ? '<span class="chip chip-tot"><i></i>Mua lại</span>' : ''}<span class="oms-mo">${MARKETS[k.mkt].ten}</span></div></div>${nutDong}</div>
  <div class="ngan-than">
    <dl class="tt-luoi">
      <dt>SĐT</dt><dd>${h(k.sdt)}</dd>
      <dt>Địa chỉ</dt><dd>${h(k.city)}, ${MARKETS[k.mkt].ten}</dd>
      <dt>Kênh đầu tiên</dt><dd>${nenChip(kn)} ${h(kn.ten)}</dd>
      <dt>Khách từ</dt><dd>${ngay(k.dau)}</dd>
      <dt>Số đơn</dt><dd>${ds.length}</dd>
      <dt>Tổng mua</dt><dd class="dam">${tien(ds.reduce((s, d) => s + d.tong, 0), MARKETS[k.mkt].cur)}</dd>
    </dl>
    <div class="rr-the" data-muc="${r.muc}"><div class="rr-dau"><strong>Mức rủi ro</strong><span class="muc muc-${r.muc}">${MUC_NHAN[r.muc]}</span></div>
      <ul class="ly-do">${r.lyDo.map(x => `<li>${h(x)}</li>`).join('')}</ul>${lyDoChan(k)}${hangDanhDau(k, 'ngan')}</div>
    <h3 class="tieu-de-nho">Các đơn</h3>
    <ul class="ds-don">${ds.map(d => `<li><button type="button" class="dong-don" data-act="mo-don" data-id="${d.id}"><span class="mono">${d.id}</span><span>${ngay(d.tao)} · ${tien(d.tong, d.cur)}</span>${badge(d.tt)}</button></li>`).join('')}</ul>
    <h3 class="tieu-de-nho">Dòng thời gian</h3>
    ${dongThoiGianKhach(k)}
  </div>`;
}
function nganLai(id) {
  const k = kenhTheoId(id), r = laiKhoang(k, 0, S.lp.ky);
  const dau = `<div class="ngan-dau"><div>${nenChip(k)}<h2 id="ngan-tieu-de">${h(k.ten)}</h2><div class="hang-chip"><span class="oms-mo">${S.lp.ky} ngày · ${r.don} đơn giao · ${MARKETS[k.mkt].ten}</span></div></div>${nutDong}</div>`;
  if (r.dsVnd === null) return dau + `<div class="ngan-than"><div class="bao bao-xau"><span class="bao-ic">!</span><div>Chưa tính được lãi: thiếu tỉ giá ${r.cur}. Nhập ở bảng "Tỉ giá tạm" cuối màn.</div></div></div>`;
  const phi = PHI_SAN[k.nen];
  const buoc = [['cong', `Doanh số: ${tien(r.dsMinor, r.cur)} × ${so(r.tg)} ₫`, r.dsVnd]];
  if (phi) buoc.push(['tru', `Phí sàn ${phanTram(phi)}`, r.phiSan]);
  buoc.push(['tru', 'Giá vốn hàng', r.von], ['tru', 'Cước vận chuyển', r.cuoc], ['tru', 'Quảng cáo', r.qc], ['tru', 'Chi phí hoàn (cước hai chiều)', r.hoan]);
  const goc = Math.max(r.dsVnd, buoc.slice(1).reduce((s, b) => s + b[2], 0), 1);
  const li = buoc.map(([loai, nhan, v]) => `<li class="${loai}"><span>${nhan}</span><span class="dam">${loai === 'tru' && v ? '−' + vnd(v) : vnd(v)}</span><span class="vach-thac" aria-hidden="true"><i style="width:${Math.min(100, v / goc * 100)}%"></i></span></li>`).join('');
  const ket = `<li class="ket${r.lai < 0 ? ' am' : ''}"><span>Lãi${r.dsVnd ? ' · biên ' + phanTram(r.lai / r.dsVnd) : ''}</span><span>${vnd(r.lai)}</span><span class="vach-thac" aria-hidden="true"><i style="width:${Math.min(100, Math.abs(r.lai) / goc * 100)}%"></i></span></li>`;
  const lon = buoc.slice(1).sort((a, b) => b[2] - a[2])[0];
  const nhanXet = r.dsVnd ? `Khoản ăn nhiều nhất: ${lon[1].toLowerCase()} — ${phanTram(lon[2] / r.dsVnd)} doanh số.${r.qc ? ` ROAS ${nf1.format(r.dsVnd / r.qc)}.` : ''}` : 'Chưa có đơn giao trong kỳ.';
  return dau + `<div class="ngan-than"><ol class="thac">${li}${ket}</ol>
    <div class="bao bao-nhan nhan-xet"><div>${nhanXet}</div></div>
    <p class="ghi-nho">Số minh hoạ: giá vốn, cước, phí sàn, quảng cáo là số giả; tỉ giá là tỉ giá tạm cuối màn.</p></div>`;
}
const NGAN = {don: nganDon, kenh: nganKenh, khach: nganKhach, lai: nganLai, 'ghi-tien': nganGhiTien, phieu: nganPhieu, 'them-kenh': nganThemKenh};
// Ba ngăn kéo là biểu mẫu: vẽ lại khi đang gõ thì mất chữ, nên việc chạy nền không vẽ lại chúng
const LA_FORM = new Set(['ghi-tien', 'phieu', 'them-kenh']);
// Ngăn kéo đang mở thì phần phía sau không bấm, không Tab tới được
function khoaNen() { $('.app').inert = !!S.ngan; }
function renderNgan(focus) {
  const el = $('#ngan'), phu = $('#phu');
  if (!S.ngan) { el.hidden = true; phu.hidden = true; el.innerHTML = ''; khoaNen(); return; }
  el.innerHTML = NGAN[S.ngan.loai](S.ngan.id, S.ngan.o);
  el.hidden = false; phu.hidden = false;
  khoaNen();
  if (S.ngan.loai === 'phieu') goiYPhieu($('#f-phieu', el));
  if (focus) ($('[data-dau]', el) || $('[data-act="dong-ngan"]', el)).focus();
}
function veLaiNgan() { if (S.ngan && !LA_FORM.has(S.ngan.loai)) renderNgan(false); }
function danhDauHang() {
  for (const r of $$('tr.dang-mo')) r.classList.remove('dang-mo');
  if (!S.ngan) return;
  const l = S.ngan.loai, r = l === 'don' || l === 'ghi-tien' ? $(`tr[data-don="${S.ngan.id}"]`) : l === 'lai' ? $(`tr[data-lai="${S.ngan.id}"]`) : null;
  if (r) r.classList.add('dang-mo');
}
// Biểu mẫu mở từ ngăn kéo đơn thì Huỷ, Esc hay lưu xong đều quay về ngăn kéo đó
function moNgan(loai, id = null, o = null) {
  if (!S.ngan) S.truocNgan = document.activeElement;
  const ve = S.ngan && LA_FORM.has(loai) && !LA_FORM.has(S.ngan.loai) ? {loai: S.ngan.loai, id: S.ngan.id} : null;
  S.ngan = {loai, id, o, ve};
  renderNgan(true);
  danhDauHang();
}
function veNgan() {
  if (S.ngan && S.ngan.ve) { S.ngan = {...S.ngan.ve, o: null, ve: null}; renderNgan(true); danhDauHang(); }
  else dongNgan();
}
function dongNgan() {
  if (!S.ngan) return;
  S.ngan = null; renderNgan(); danhDauHang();
  const t = S.truocNgan; S.truocNgan = null;
  if (t && t.isConnected) t.focus();
}
function buocDon() {
  const d = S.donMap[S.ngan.id];
  if (!d || KET_THUC.has(d.pha)) return;
  const n = d.sk.length, thieuTruoc = d.thieu, truocTT = d.tt;
  buocTiep(d, Date.now(), true);
  if (d.sk.length === n || (d.thieu && !thieuTruoc)) toast(`${KHO[d.wh].ten} chưa đủ hàng — nhập kho hoặc nhận phiếu đang về rồi thử lại.`);
  else toast(`${d.id}: ${cuoi(d).x}${d.tt === 'Đã nhận hàng' && truocTT !== d.tt && laPhaiThu(d) && conLai(d) ? ` — vào Công nợ, chờ thu ${tien(conLai(d), d.cur)}` : ''}`);
  renderNgan(false);
  capNhat();
}
function nhanHoan() {
  const d = S.donMap[S.ngan.id];
  if (!d || d.pha !== 'daHoan' || d.daNhanHoan) return;
  for (const i of d.items) { S.ton[d.wh][i.ma].co += i.sl; ghiSo({loai: 'Hoàn về kho', ma: i.ma, sl: i.sl, wh: d.wh, ghi: d.id}); }
  d.daNhanHoan = true;
  d.sk.push({t: Date.now(), x: `Kho đã nhận lại hàng hoàn — cộng ${d.items.reduce((s, i) => s + i.sl, 0)} sản phẩm vào tồn`, n: 'Kho', noiBo: true});
  toast(`Đã nhận hàng hoàn của ${d.id} vào ${KHO[d.wh].ten}. Số tồn ở màn Kho đã cộng lại.`);
  renderNgan(false);
  capNhat();
}
function luuGhiChu() {
  const d = S.donMap[S.ngan.id], o = $('#ghi-chu'), v = o.value.trim();
  if (!v) { o.focus(); return toast('Gõ ghi chú trước khi lưu.'); }
  d.sk.push({t: Date.now(), x: 'Ghi chú: ' + v, n: 'CSKH · ' + d.cskh, noiBo: true});
  toast('Đã lưu ghi chú vào hành trình đơn.');
  renderNgan(false);
  capNhat();
}

// ---------- Màn, địa chỉ, vẽ lại ----------
const MAN = {
  baodon: {hash: 'bao-don', ten: 'Báo đơn', mount: mountBaoDon, upd: updBaoDon},
  congno: {hash: 'cong-no', ten: 'Công nợ & đối soát', mount: mountCongNo, upd: updCongNo},
  ruiro: {hash: 'khach-rui-ro', ten: 'Khách rủi ro', mount: mountRuiRo, upd: updRuiRo},
  kho: {hash: 'kho', ten: 'Kho', mount: mountKho, upd: updKho},
  kenh: {hash: 'kenh-ban', ten: 'Kênh bán & Page', mount: mountKenh, upd: updKenh},
  lai: {hash: 'lai-theo-page', ten: 'Lãi theo page', mount: mountLai, upd: updLai},
};
const THEO_HASH = Object.fromEntries(Object.entries(MAN).map(([v, m]) => [m.hash, v]));
const manTuHash = () => THEO_HASH[location.hash.slice(1)] || 'baodon';
function setDem(v, n, lop, title) { const el = $('#dem-' + v); el.textContent = n || ''; el.className = 'oms-dem' + (n ? ' ' + lop : ''); el.title = n ? title : ''; }
function renderNav() {
  const tac = S.don.filter(laTac).length, giu = bangGiu();
  let can = 0;
  for (const w in KHO) for (const sp of SP) if (trangThaiTon(w, sp.ma, giu).muc >= 2) can++;
  setDem('baodon', tac, 'do', `${tac} đơn tắc`);
  setDem('kho', can, 'vang', `${can} mã hàng cần nhập thêm`);
  const loi = S.kenh.filter(k => k.trang === 'loi').length;
  setDem('kenh', loi, 'do', `${loi} kênh mất kết nối`);
  const qua14 = S.don.filter(d => laPhaiThu(d) && conLai(d) > 0 && tuoiNo(d) > 14).length;
  setDem('congno', qua14, 'do', `${qua14} đơn nợ quá 14 ngày`);
  const map = donTheoKhach(), cao = S.khach.filter(k => ruiRo(k, map).muc === 'cao').length;
  setDem('ruiro', cao, 'do', `${cao} khách rủi ro cao`);
  const lo = S.kenh.filter(k => { const r = laiKhoang(k, 0, S.lp.ky); return r.lai !== null && r.lai < 0; }).length;
  setDem('lai', lo, 'do', `${lo} page đang lỗ`);
}
function capNhat() { renderNav(); MAN[S.view].upd(); }
// Thanh bên trên điện thoại: ☰ mở, chọn màn hay Esc thì đóng
function moBen(mo) { $('#oms-ben').classList.toggle('mo', mo); $('#nut-nav').setAttribute('aria-expanded', String(mo)); }
function hienMan(v) {
  if (!MAN[v]) v = 'baodon';
  dongNgan(); moBen(false);
  S.view = v;
  for (const s of $$('.view')) s.hidden = s.id !== 'v-' + v;
  for (const a of $$('.nav-muc')) { if (a.dataset.view === v) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); }
  $('#ten-man').textContent = MAN[v].ten;
  document.title = `KN OMS · ${MAN[v].ten} · Kim Ngân JSC`;
  if (!S.mounted[v]) { MAN[v].mount(); S.mounted[v] = true; }
  capNhat();
  window.scrollTo(0, 0);
}
function diToi(v) { const hash = '#' + MAN[v].hash; if (location.hash === hash) hienMan(v); else location.hash = hash; }
// Nền: cùng khoá với KN CRM nên đổi ở bên nào thì bên kia theo
function apNen(nen) {
  document.documentElement.dataset.theme = nen;
  $('#nut-nen').setAttribute('aria-pressed', String(nen === 'dark'));
}
function doiNen() {
  const moi = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('knjsc-nen', moi); } catch (_) { /* không lưu được thì chỉ đổi trong trang này */ }
  apNen(moi);
}
function datLai() {
  const v = S.view;
  dongNgan();
  khoiTao();
  for (const s of $$('.view')) s.innerHTML = '';
  hienMan(v);
  toast('Đã đặt lại dữ liệu demo.');
}

const ACT = {
  'nen': () => doiNen(),
  'dat-lai': () => datLai(),
  'hoi-hang': el => hoiHangTatCa(el),
  'bd-kpi': (el, d) => {
    if (d.loc === 'tac') { S.bd.tac = !S.bd.tac; S.bd.tt = ''; }
    else { S.bd.tt = !S.bd.tac && S.bd.tt === d.loc ? '' : d.loc; S.bd.tac = false; }
    S.bd.trang = 1; updBaoDon();
  },
  'bd-tt': (el, d) => { S.bd.tt = d.tt; S.bd.tac = false; S.bd.trang = 1; updBaoDon(); },
  'bd-bo-loc': () => boLocBaoDon(),
  'bd-ngay': (el, d) => chonChipNgay('bd', d.ngay),
  'bd-xuat': () => xuatBaoDon(),
  'cn-xuat': () => xuatCongNo(locCongNo().ds),
  'cn-xuat-chon': () => xuatCongNo(locCongNo().ds.filter(d => S.cn.chon.has(d.id))),
  'cn-nhac-chon': () => nhacNhieu(),
  'cn-bo-chon': () => { S.cn.chon.clear(); updCongNo(); },
  'rr-chan-huy': () => huyChan(),
  'trang': (el, d) => { S[d.pham].trang += +d.buoc; ({bd: updBaoDon, cn: updCongNo})[d.pham](); },
  'dong-ngan': () => dongNgan(),
  'huy-form': () => veNgan(),
  'buoc-don': () => buocDon(),
  'nhan-hoan': () => nhanHoan(),
  'luu-ghi-chu': () => luuGhiChu(),
  'mo-don': (el, d) => moNgan('don', d.id),
  'mo-khach': (el, d) => moNgan('khach', d.id),
  'mo-phieu': (el, d) => moNgan('phieu', null, {loai: d.loai, ma: d.sp, wh: d.kho, sl: d.sl}),
  'nhan-phieu': (el, d) => nhanPhieu(d.id),
  'kho-tab': (el, d) => { S.kho.wh = d.wh; S.kho.xem = 12; updKho(); },
  'so-loc': (el, d) => { S.kho.loai = d.loai; S.kho.xem = 12; updKho(); },
  'so-them': () => { S.kho.xem += 12; updKho(); },
  'kn-loc': (el, d) => { S.kn.nen = d.nen; updKenh(); },
  'them-kenh': () => moNgan('them-kenh'),
  'ket-noi-lai': () => ketNoiLai(kenhTheoId(S.ngan.id)),
  'ngat': () => ngatKenh(kenhTheoId(S.ngan.id)),
  'cn-kpi': (el, d) => { S.cn.loc = d.loc; S.cn.trang = 1; updCongNo(); },
  'cn-tuoi': (el, d) => { S.cn.tuoi = d.tuoi; S.cn.trang = 1; updCongNo(); },
  'cn-bo-loc': () => boLocCongNo(),
  'cn-nhac': (el, d) => nhacKhach(S.donMap[d.id]),
  'cn-ghi': (el, d) => { const x = S.donMap[d.id]; if (x && laPhaiThu(x) && conLai(x)) moNgan('ghi-tien', x.id); },
  'cn-ve-tk': (el, d) => xacNhanVeTk(S.donMap[d.id]),
  'cn-khop': (el, d) => khopTienVe(d.tv, d.don),
  'rr-mau': (el, d) => chonMau(d.mau),
  'rr-loc': (el, d) => { S.rr.loc = d.loc; S.rr.xem = 20; updRuiRo(); },
  'rr-bo-loc': () => { S.rr.loc = ''; S.rr.xem = 20; updRuiRo(); },
  'rr-them': () => { S.rr.xem += 20; updRuiRo(); },
  'rr-danh-dau': (el, d) => { const kh = S.khMap[d.kh]; if (d.giaTri === 'chan' && kh && kh.danhDau !== 'chan') moChan(d.kh, el.closest('#ngan') ? 'ngan' : 'the'); else danhDau(d.kh, d.giaTri); },
  'lp-ky': (el, d) => { S.lp.ky = +d.ky; S.lp.diem = null; capNhat(); },
  'lp-xem': (el, d) => { S.lp.xem = d.xem; updLai(); },
};
document.addEventListener('click', e => {
  if (e.target.closest('#nut-nav')) return moBen(!$('#oms-ben').classList.contains('mo'));
  // Ô tích chọn đơn: không mở ngăn kéo; bấm vào khoảng trống quanh ô cũng tích
  const oChon = e.target.closest('.oms-o-chon');
  if (oChon) { if (e.target.tagName !== 'INPUT') $('input', oChon).click(); return; }
  const diem = e.target.closest('#lp-xu-hinh circle');
  if (diem) { S.lp.diem = +diem.dataset.i; return docDiem(); }
  const el = e.target.closest('[data-act],[data-view],[data-don],[data-kenh],[data-khach],[data-lai]');
  if (!el || el.disabled) return;
  const d = el.dataset;
  if (d.act) { const f = ACT[d.act]; if (f) f(el, d); return; }
  if (d.view) { if (el.tagName !== 'A') diToi(d.view); return; }   // liên kết #màn để trình duyệt tự đổi địa chỉ
  if (d.don) return moNgan('don', d.don);
  if (d.kenh) return moNgan('kenh', d.kenh);
  if (d.khach) return moNgan('khach', d.khach);
  if (d.lai) return moNgan('lai', d.lai);
});
document.addEventListener('submit', e => {
  const f = e.target, luu = {'f-ghi-tien': luuGhiTien, 'f-phieu': luuPhieu, 'f-kenh': luuKenh, 'f-chan': luuChan}[f.id];
  if (!luu) return;
  e.preventDefault();
  luu(f);
});
document.addEventListener('input', e => {
  const t = e.target;
  if (t.id === 'bd-q') { S.bd.q = t.value; S.bd.trang = 1; updBaoDon(); }
  else if (t.id === 'cn-q') { S.cn.q = t.value; S.cn.trang = 1; updCongNo(); }
  else if (t.id === 'rr-sdt') { S.rr.sdt = t.value; S.rr.mau = ''; updRrThe(); }
});
document.addEventListener('change', e => {
  const t = e.target, loc = {'bd-mkt': 'mkt', 'bd-hang': 'hang', 'bd-kenh': 'kenh', 'bd-sx': 'sx'}[t.id];
  if (loc) { S.bd[loc] = t.value; S.bd.trang = 1; return updBaoDon(); }
  if (t.id === 'bd-nguong') { S.bd.nguong = +t.value; return capNhat(); }
  if (t.id === 'cn-pttt' || t.id === 'cn-mkt') { S.cn[t.id.slice(3)] = t.value; S.cn.trang = 1; return updCongNo(); }
  if (/^(bd|cn)-(tu|den)$/.test(t.id)) return doiNgay(t.id.slice(0, 2));
  if (t.id === 'lp-xu-page') { S.lp.page = t.value; S.lp.diem = null; return updXuHuong(); }
  if (t.id === 'cn-chon-het') { const ds = locCongNo().ds; if (t.checked) for (const d of ds) S.cn.chon.add(d.id); else S.cn.chon.clear(); for (const o of $$('#cn-than [data-chon]')) o.checked = S.cn.chon.has(o.dataset.chon); return updThanhChon(ds); }
  if (t.dataset.chon) { if (t.checked) S.cn.chon.add(t.dataset.chon); else S.cn.chon.delete(t.dataset.chon); return updThanhChon(locCongNo().ds); }
  if (t.id.startsWith('lp-tg-')) return doiTiGia(t);
  if (t.form && t.form.id === 'f-phieu') return goiYPhieu(t.form);
  const k = S.ngan && S.ngan.loai === 'kenh' ? kenhTheoId(S.ngan.id) : null;
  switch (t.dataset.sua) {
    case 'tu-keo': if (!k) return; k.tu = t.checked; toast(k.tu ? `Đã bật tự kéo đơn của ${k.ten}.` : `Đã tắt tự kéo đơn của ${k.ten} — đơn mới ở kênh này không vào bảng Vận đơn.`); return capNhat();
    case 'phu-trach': if (!k) return; k.pt = t.value; toast(`${k.ten}: người phụ trách mới là ${k.pt}.`); return capNhat();
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { if (S.ngan) veNgan(); else if ($('#oms-ben').classList.contains('mo')) { moBen(false); $('#nut-nav').focus(); } return; }
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('tr[data-don],article[data-kenh],tr[data-khach],tr[data-lai]')) { e.preventDefault(); e.target.click(); }
  const buoc = {ArrowLeft: -1, ArrowRight: 1, Home: 'dau', End: 'cuoi'}[e.key];
  if (buoc !== undefined && e.target.matches('#lp-xu-hinh svg')) { e.preventDefault(); diDiem(buoc); }
});
window.addEventListener('hashchange', () => hienMan(manTuHash()));
window.addEventListener('storage', e => { if (e.key === 'knjsc-nen') apNen(e.newValue === 'dark' ? 'dark' : 'light'); });

apNen(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
khoiTao();
hienMan(manTuHash());
})();
