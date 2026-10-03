/* Form Nộp báo cáo ngày, sửa báo cáo và điền biểu mẫu.
   1) Loại tiền tự theo Thị trường (ô chỉ đọc).
   2) Ô số (`.o-nhap.tien`) viết theo cách Việt Nam: chấm ngăn nghìn, phẩy thập phân (chủ dự án 28.09,
      ADR-046). Gõ toàn chữ số (có thể kèm khoảng trắng) thì dấu chấm tự chèn ngay khi gõ. Người dùng tự
      gõ "." hay "," thì để nguyên cho gõ xong, rời ô mới viết lại theo đúng luật `core.money.parse_money`
      của máy chủ — "8000.50" thành "8.000,5", không bao giờ thành 800.050. Chữ trên ô luôn là đúng số
      máy chủ sẽ lưu. Số nguyên (Số Mess, Số đơn) không có phần lẻ: máy chủ bỏ mọi dấu, ô cũng vậy.
   3) Xem trước chỉ số (AC-43.6): mỗi thẻ `.cs` mang công thức của một cột tính sẵn; gõ số là tính ngay, làm
      tròn như máy chủ (nửa về chẵn), hậu tố loại tiền theo ô Loại tiền; form không có ô đó (MKT luôn VND, ADR-048)
      thì theo `data-tien` của khung thẻ. Chỉ là xem trước — máy chủ tự tính lại khi nộp. */
(() => {
  const map = document.getElementById('report-currency-map');
  const output = document.querySelector('[data-report-currency]');
  const market = document.querySelector('[data-report-market] select');
  if (map && output && market) {
    const currencies = JSON.parse(map.textContent);
    const sync = () => { output.value = currencies[market.value] || 'Chọn quốc gia'; };
    market.addEventListener('change', sync); sync();
  }

  const nhom = digits => digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

  // Đọc như parse_money: hai loại dấu → dấu đứng sau là thập phân; chỉ phẩy → thập phân; chỉ chấm →
  // đúng một chấm và 1–2 chữ số sau nó là thập phân, còn lại là ngăn nghìn. Không đọc được → null.
  const docSo = (text, kieu) => {
    let s = String(text).replace(/[\s ₫$€₩¥]/g, '');
    if (!s) return null;
    const am = s.startsWith('-');
    s = s.replace(/^[-+]/, '');
    if (kieu === 'integer') {
      // parse_value của cột Số nguyên bỏ mọi dấu chấm, phẩy
      s = s.replace(/[.,]/g, '');
    } else {
      const cham = s.includes('.'), phay = s.includes(',');
      if (cham && phay) {
        s = s.lastIndexOf(',') > s.lastIndexOf('.') ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
      } else if (phay) {
        s = s.replace(',', '.');
      } else if (cham) {
        const phan = s.split('.');
        if (!(phan.length === 2 && phan[1].length >= 1 && phan[1].length <= 2)) s = s.replace(/\./g, '');
      }
    }
    if (!/^\d+(\.\d+)?$/.test(s)) return null;
    const [nguyen, le = ''] = s.split('.');
    return {am, nguyen: nguyen.replace(/^0+(?=\d)/, ''), le};
  };
  // Viết theo cách Việt Nam; `gon` bỏ số 0 thừa cuối phần lẻ (13.250.000,0 → 13.250.000) — cùng giá trị
  const vietSo = (so, gon) => {
    const le = gon ? so.le.replace(/0+$/, '') : so.le;
    return (so.am ? '-' : '') + nhom(so.nguyen) + (le ? ',' + le : '');
  };

  // Viết lại cả ô theo luật máy chủ; không đọc được thì để nguyên cho máy chủ báo lỗi
  const chuanHoa = o => {
    const so = docSo(o.value, o.dataset.kieu);
    if (so) o.value = vietSo(so, true);
    o.dataset.tuGo = '';
  };

  // Số ký tự có nghĩa (chữ số và dấu phẩy) đứng trước vị trí `vt` của chuỗi `v`
  const demCoNghia = (v, vt) => v.slice(0, vt).replace(/[^\d,]/g, '').length;
  const viTriSau = (v, n) => {
    let dem = 0, i = 0;
    while (i < v.length && dem < n) { if (/[\d,]/.test(v[i])) dem++; i++; }
    return i;
  };

  for (const o of document.querySelectorAll('input.o-nhap.tien')) {
    chuanHoa(o);
    o.addEventListener('input', event => {
      if (event.inputType === 'insertFromPaste' || event.inputType === 'insertFromDrop') {
        chuanHoa(o);
        return;
      }
      const v = o.value;
      const vt = o.selectionStart ?? v.length;
      if (event.inputType === 'insertText' && /[.,]/.test(event.data || '')) {
        if (!o.dataset.tuGo) {
          // Người dùng tự gõ dấu: mọi dấu chấm đang có là dấu nhóm tự chèn — bỏ đi, chỉ giữ dấu vừa gõ,
          // không thì "8000.50" gõ dần thành "8.000.50" và bị đọc thành 800.050
          const truoc = v.slice(0, vt - 1).replace(/\./g, ''), sau = v.slice(vt).replace(/\./g, '');
          o.value = truoc + v[vt - 1] + sau;
          o.setSelectionRange(truoc.length + 1, truoc.length + 1);
          o.dataset.tuGo = '1';
        }
        return;
      }
      if (o.dataset.tuGo) return;   // đang tự gõ dấu: chờ rời ô rồi viết lại theo luật máy chủ
      // Tự chèn dấu chấm cho phần nguyên; phần lẻ sau dấu phẩy (đã có từ lần viết lại trước) giữ nguyên
      const am = v.trimStart().startsWith('-');
      const phay = v.indexOf(',');
      const nguyenTho = (phay >= 0 ? v.slice(0, phay) : v).replace(/\D/g, '');
      const nguyen = nguyenTho.replace(/^0+(?=\d)/, '');
      const le = phay >= 0 ? v.slice(phay + 1).replace(/\D/g, '') : null;
      const moi = (am ? '-' : '') + nhom(nguyen) + (le === null ? '' : ',' + le);
      if (moi === v) return;
      const n = Math.max(0, demCoNghia(v, vt) - (nguyenTho.length - nguyen.length));
      o.value = moi;
      const i = viTriSau(moi, n) + (am && n === 0 ? 1 : 0);
      o.setSelectionRange(i, i);
    });
    o.addEventListener('change', () => chuanHoa(o));
  }

  const theXemTruoc = [...document.querySelectorAll('#xem-truoc-chi-so .cs')];
  if (theXemTruoc.length) {
    const oSo = [...document.querySelectorAll('input.o-nhap.tien[data-cot]')];
    const giaTri = o => {
      const so = docSo(o.value, o.dataset.kieu);
      return so ? Number((so.am ? '-' : '') + so.nguyen + (so.le ? '.' + so.le : '')) : null;
    };
    // Làm tròn nửa về chẵn như Decimal.quantize của máy chủ
    const lamTron = (x, le) => {
      const f = 10 ** le, v = x * f, duoi = Math.floor(v);
      if (Math.abs(v - duoi - 0.5) < 1e-9) return (duoi % 2 === 0 ? duoi : duoi + 1) / f;
      return Math.round(v) / f;
    };
    const vietKetQua = (x, le) => {
      const [nguyen, phan = ''] = Math.abs(x).toFixed(le).split('.');
      const gon = phan.replace(/0+$/, '');
      return (x < 0 ? '-' : '') + nhom(nguyen) + (gon ? ',' + gon : '');
    };
    const tinh = (phep, a, b) => {
      if (phep === 'add') return a + b;
      if (phep === 'subtract') return a - b;
      if (phep === 'multiply') return a * b;
      if (b === 0) return NaN;
      return phep === 'percent' ? a / b * 100 : a / b;
    };
    const xemTruoc = vuaSua => {
      const so = {};
      for (const o of oSo) so[o.dataset.cot] = giaTri(o);
      const tien = output && /^[A-Z]{3}$/.test(output.value) ? output.value
        : (document.getElementById('xem-truoc-chi-so').dataset.tien || '');
      for (const the of theXemTruoc) {
        const a = so[the.dataset.trai], b = so[the.dataset.phai], o = the.querySelector('.gt');
        const kq = a == null || b == null ? null : tinh(the.dataset.phep, a, b);
        const co = kq !== null && Number.isFinite(kq);
        the.classList.toggle('trong', !co);
        the.classList.toggle('vua', co && !!vuaSua && (the.dataset.trai === vuaSua || the.dataset.phai === vuaSua));
        the.classList.toggle('canh-bao', co && the.dataset.donVi === 'phan-tram' && kq > 100);
        if (!co) { o.textContent = kq === null ? '— chưa đủ số' : '— chia cho 0'; continue; }
        o.textContent = vietKetQua(lamTron(kq, Number(the.dataset.le)), Number(the.dataset.le));
        const donVi = the.dataset.donVi === 'phan-tram' ? '%' : the.dataset.donVi === 'tien' ? tien : '';
        if (donVi) {
          const nho = document.createElement('small');
          nho.textContent = donVi;
          o.append(' ', nho);
        }
      }
    };
    for (const o of oSo) {
      o.addEventListener('input', () => xemTruoc(o.dataset.cot));
      o.addEventListener('change', () => xemTruoc(o.dataset.cot));
    }
    if (market) market.addEventListener('change', () => xemTruoc());
    xemTruoc();
  }
})();
