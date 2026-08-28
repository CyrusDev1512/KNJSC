/* ══════════════════════════════════════════════════════════════════
   LAYOUT — khung chung cho mọi màn hình
   Bản dựng tĩnh. Sau này phần này thành base.html của Django,
   phần phân quyền thành core/scope.py và core/permissions.py.
   ══════════════════════════════════════════════════════════════════ */

/* ── Chín vai trò: bộ phận nhân cấp bậc, cộng Admin (ADR-003) ── */
const CAP = { Staff: 1, Leader: 2, Manager: 3, Admin: 4 };

const VAI_TRO = [
  { ma: "sale_staff",   bo_phan: "Sale",     cap_bac: "Staff",   team: "Sale 1",     ten: "Nguyễn Thị Hà" },
  { ma: "sale_leader",  bo_phan: "Sale",     cap_bac: "Leader",  team: "Sale 1",     ten: "Trần Văn Dũng" },
  { ma: "sale_mgr",     bo_phan: "Sale",     cap_bac: "Manager", team: "—",          ten: "Lê Quốc Bảo" },
  { ma: "mkt_staff",    bo_phan: "Marketing", cap_bac: "Staff",  team: "MKT 2",      ten: "Phạm Minh Anh" },
  { ma: "mkt_leader",   bo_phan: "Marketing", cap_bac: "Leader", team: "MKT 2",      ten: "Vũ Hoài Nam" },
  { ma: "mkt_mgr",      bo_phan: "Marketing", cap_bac: "Manager", team: "—",         ten: "Đỗ Thu Trang" },
  { ma: "vd_staff",     bo_phan: "Vận đơn",  cap_bac: "Staff",   team: "Vận đơn 1",  ten: "Hoàng Văn Tú" },
  { ma: "vd_leader",    bo_phan: "Vận đơn",  cap_bac: "Leader",  team: "Vận đơn 1",  ten: "Ngô Thanh Sơn" },
  { ma: "vd_mgr",       bo_phan: "Vận đơn",  cap_bac: "Manager", team: "—",          ten: "Bùi Kim Chi" },
  { ma: "admin",        bo_phan: "Quản trị", cap_bac: "Admin",   team: "—",          ten: "Quản trị viên" }
];

/* ── Phạm vi quyền cho từng màn hình ──────────────────────────────
   Đây là bản nháp của core/permissions.py. Mỗi hàm trả về true nếu
   vai trò được vào. Không màn hình nào tự viết điều kiện lọc riêng. */
const QUYEN = {
  "bao-cao-ngay":     v => v.cap_bac !== "Admin",
  "bao-cao-lich-su":  () => true,
  "bao-cao-tong-hop": v => CAP[v.cap_bac] >= CAP.Leader,
  "len-don":          v => v.bo_phan === "Sale" || v.cap_bac === "Admin",
  "bang-van-don":     v => v.bo_phan === "Vận đơn" || v.cap_bac === "Admin",
  "bang-tinh":        v => v.cap_bac !== "Admin",
  "quan-ly-bieu-mau": v => CAP[v.cap_bac] >= CAP.Manager,
  "tao-bieu-mau":     v => CAP[v.cap_bac] >= CAP.Manager,
  "phan-quyen":       () => true,
  "tu-choi":          () => true
};

const DIEU_HUONG = [
  { nhom: "Báo cáo", mucs: [
    { ma: "bao-cao-ngay",     ten: "Nộp báo cáo ngày", href: "bao-cao-ngay.html" },
    { ma: "bao-cao-lich-su",  ten: "Lịch sử báo cáo",  href: "bao-cao-lich-su.html" },
    { ma: "bao-cao-tong-hop", ten: "Báo cáo tổng hợp", href: "bao-cao-tong-hop.html" }
  ]},
  { nhom: "Đơn hàng", mucs: [
    { ma: "len-don",      ten: "Lên đơn",       href: "len-don.html" },
    { ma: "bang-van-don", ten: "Bảng vận đơn",  href: "bang-van-don.html" }
  ]},
  { nhom: "Biểu mẫu và bảng", mucs: [
    { ma: "quan-ly-bieu-mau", ten: "Quản lý biểu mẫu",  href: "quan-ly-bieu-mau.html" },
    { ma: "tao-bieu-mau",     ten: "Trình tạo biểu mẫu", href: "tao-bieu-mau.html" }
  ]},
  { nhom: "Bảng tính", mucs: [
    { ma: "bang-tinh", ten: "Bảng tính", href: "bang-tinh.html" }
  ]},
  { nhom: "Quản trị", mucs: [
    { ma: "phan-quyen",  ten: "Ma trận phân quyền",  href: "phan-quyen.html" }
  ]}
];

/* ── Trạng thái phiên, lưu tạm ở trình duyệt ── */
function docLuu(khoa, mac_dinh) {
  try { return localStorage.getItem(khoa) || mac_dinh; } catch (e) { return mac_dinh; }
}
function ghiLuu(khoa, gia_tri) {
  try { localStorage.setItem(khoa, gia_tri); } catch (e) { /* trình duyệt chặn lưu */ }
}

function vaiTroHienTai() {
  const ma = docLuu("knjsc-vai-tro", "sale_staff");
  return VAI_TRO.find(v => v.ma === ma) || VAI_TRO[0];
}

function duocVao(ma_trang, vai_tro) {
  const kiem = QUYEN[ma_trang];
  return kiem ? kiem(vai_tro) : true;
}

const thoat = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/* ══ Dựng khung ═══════════════════════════════════════════════════ */

function dungKhung() {
  const body = document.body;
  const trang = body.dataset.trang || "tong-quan";
  const tieu_de = body.dataset.tieuDe || "";
  const vai = vaiTroHienTai();

  /* Gọi thẳng đường dẫn vẫn phải bị kiểm quyền — AC-3.7.
     Bản thật kiểm ở máy chủ, không chỉ ẩn chức năng trên giao diện (P1). */
  if (!duocVao(trang, vai)) {
    document.querySelector(".chinh").innerHTML =
      '<div style="padding:64px 32px;max-width:520px"><div class="nhan-nho" style="color:var(--critical)">Lỗi 403</div>' +
      '<h1 style="font-size:26px;font-weight:800;margin:8px 0">Bạn không có quyền truy cập</h1>' +
      '<p style="color:var(--ink-2)">Bản thật của màn hình từ chối nằm ở ứng dụng Django, cổng 8020.</p></div>';
    return;
  }

  /* ── Thanh bên ── */
  const nav_html = DIEU_HUONG.map(nhom => {
    const mucs = nhom.mucs.map(m => {
      const ok = duocVao(m.ma, vai);
      const day = m.ma === trang ? ' aria-current="page"' : "";
      const lop = ok ? "nav-muc" : "nav-muc khoa";
      const dich = ok ? m.href : `index.html#khong-co-quyen`;
      const khoa = ok ? "" : '<span class="khoa-ic" title="Ngoài phạm vi quyền">khoá</span>';
      return `<a class="${lop}" href="${dich}"${day}>${thoat(m.ten)}${khoa}</a>`;
    }).join("");
    return `<div class="nav-nhom">${thoat(nhom.nhom)}</div>${mucs}`;
  }).join("");

  const aside = document.createElement("aside");
  aside.className = "nav";
  aside.id = "thanh-ben";
  aside.innerHTML = `
    <div class="nav-dau">
      <a class="nav-hieu" href="index.html">
        <span>KN</span>
        <div>Kim Ngân JSC<small>Hệ thống vận hành</small></div>
      </a>
    </div>
    <nav class="nav-than" aria-label="Điều hướng chính">${nav_html}</nav>
    <div class="nav-chan">
      <div class="ma nho">Phase 1 · bản dựng giao diện</div>
    </div>`;

  /* ── Thanh trên ── */
  const chon_vai = VAI_TRO.map(v =>
    `<option value="${v.ma}"${v.ma === vai.ma ? " selected" : ""}>${thoat(v.cap_bac)} · ${thoat(v.bo_phan)}</option>`
  ).join("");

  const top = document.createElement("div");
  top.className = "topbar";
  top.innerHTML = `
    <button class="nut nut-nho nut-nav" type="button" id="nut-nav" aria-label="Mở điều hướng">☰</button>
    <div class="duong-dan"><span>Kim Ngân JSC</span><span>/</span><b>${thoat(tieu_de)}</b></div>
    <div class="topbar-phai">
      <div class="doi-vai-tro">
        <label for="chon-vai-tro">Xem theo vai trò</label>
        <select id="chon-vai-tro">${chon_vai}</select>
      </div>
      <button class="nut nut-nho" type="button" id="nut-nen" title="Đổi nền sáng tối">Nền</button>
      <div class="nguoi-dung">
        <div class="avatar">${thoat(vai.ten.trim().split(/\s+/).pop().charAt(0))}</div>
        <div><b>${thoat(vai.ten)}</b><small>${thoat(vai.cap_bac)} · ${thoat(vai.bo_phan)}</small></div>
      </div>
    </div>`;

  document.querySelector(".app").prepend(aside);
  document.querySelector(".chinh").prepend(top);

  /* Đổi vai trò — nếu vai trò mới không có quyền vào màn hình này
     thì chuyển sang màn hình từ chối, đúng như FR-3.5 */
  document.getElementById("chon-vai-tro").addEventListener("change", e => {
    ghiLuu("knjsc-vai-tro", e.target.value);
    const moi = VAI_TRO.find(v => v.ma === e.target.value);
    location.href = location.pathname;
  });

  document.getElementById("nut-nen").addEventListener("click", () => {
    const toi = document.documentElement.dataset.theme === "dark";
    document.documentElement.dataset.theme = toi ? "light" : "dark";
    ghiLuu("knjsc-nen", toi ? "light" : "dark");
  });

  document.getElementById("nut-nav").addEventListener("click", () => {
    aside.classList.toggle("mo");
  });

  /* Điền tên vai trò vào các chỗ đánh dấu sẵn trong nội dung trang */
  document.querySelectorAll("[data-dien]").forEach(el => {
    el.textContent = vai[el.dataset.dien] ?? "";
  });
  document.querySelectorAll("[data-chi-cho]").forEach(el => {
    const cho = el.dataset.chiCho.split(",").map(s => s.trim());
    if (!cho.includes(vai.bo_phan) && !cho.includes(vai.cap_bac)) el.hidden = true;
  });
}

/* ══ Tương tác nhỏ dùng chung ═════════════════════════════════════ */

function gapTuongTac() {
  /* Tab trong trang */
  document.querySelectorAll("[data-tab-nhom]").forEach(thanh => {
    thanh.addEventListener("click", e => {
      const nut = e.target.closest("[data-tab]");
      if (!nut) return;
      e.preventDefault();
      thanh.querySelectorAll("[data-tab]").forEach(t => t.setAttribute("aria-selected", "false"));
      nut.setAttribute("aria-selected", "true");
      const nhom = thanh.dataset.tabNhom;
      document.querySelectorAll(`[data-tab-noi-dung="${nhom}"] > *`).forEach(v => {
        v.hidden = v.dataset.tabTen !== nut.dataset.tab;
      });
    });
  });

  /* Sắp xếp bảng bằng cách bấm tiêu đề cột */
  document.querySelectorAll("table.bang th.sap-xep").forEach(th => {
    th.addEventListener("click", () => {
      const bang = th.closest("table");
      const cot = [...th.parentNode.children].indexOf(th);
      const nguoc = th.getAttribute("aria-sort") === "ascending";
      bang.querySelectorAll("th").forEach(x => x.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", nguoc ? "descending" : "ascending");
      const than = bang.tBodies[0];
      const hang = [...than.rows];
      hang.sort((a, b) => {
        const x = a.cells[cot]?.innerText.trim() ?? "";
        const y = b.cells[cot]?.innerText.trim() ?? "";
        const sx = parseFloat(x.replace(/[^\d.-]/g, ""));
        const sy = parseFloat(y.replace(/[^\d.-]/g, ""));
        const kq = (!isNaN(sx) && !isNaN(sy)) ? sx - sy : x.localeCompare(y, "vi");
        return nguoc ? -kq : kq;
      });
      hang.forEach(h => than.appendChild(h));
    });
  });

  /* Ô sửa tại chỗ — bản thật sẽ gửi bằng HTMX rồi ghi nhật ký */
  document.querySelectorAll("td.o-sua").forEach(td => {
    const goc = td.textContent.trim();
    td.addEventListener("blur", () => {
      if (td.textContent.trim() !== goc) td.dataset.doi = "1";
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  dungKhung();
  gapTuongTac();
});

/* Đặt nền trước khi vẽ để tránh nháy sáng */
(function () {
  const nen = docLuu("knjsc-nen", "");
  if (nen) document.documentElement.dataset.theme = nen;
})();
