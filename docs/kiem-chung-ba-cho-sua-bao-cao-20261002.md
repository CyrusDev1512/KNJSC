# Kiểm chứng — Ba chỗ sửa Báo cáo tổng hợp (02.10.2026)

Chủ dự án duyệt mockup "Ba chỗ sửa Báo cáo tổng hợp" và bảo sửa ba chỗ này trước. Quyết định ghi ở ADR-042 (bổ sung
02.10.2026). Tiêu chí nghiệm thu: AC-22.24, AC-22.25, AC-22.26.

- **Nhánh:** `claude/ba-cho-sua-bao-cao`, tách từ `Staging` (`8a505ea`). PR nháp về `Staging`.
- **Phạm vi:** chỉ đổi cách hiển thị. Số liệu, cách tính, quyền xem và tệp Excel giữ nguyên. Không migration, không
  thêm thư viện.

## Môi trường

- **Máy:** máy ảo Claude Code trên web. Postgres 16 cổng 5434, Python 3.11 (pytest) và 3.12 (máy chủ thử), Chromium
  bản Playwright 1.56.
- **Dữ liệu đo:** DB nháp `knjsc_bc_perf`.
  - 22 marketer trong 4 team, 30 ngày, khoảng 720 lần nộp.
  - Bốn loại tiền USD, CAD, PHP, AUD, và 5 dòng "Chưa rõ".
- **Cách đo:** máy chủ thử `runserver` cổng 8030, tài khoản `mkt.manager`, kỳ 22–28.09.2026. Khung nhìn 1366×768,
  bộ lọc mở như mặc định, nền sáng.
- **Số "trước":** đo trên mã cũ cùng dữ liệu, cùng khung nhìn (02.10.2026, trước khi sửa), và lấy thêm từ biên bản
  cuộn 28.09.

## Số đo trước và sau

| | Trước | Sau |
|---|---|---|
| ① Khung bảng bắt đầu ở (lúc mở trang) | 603 px | **402 px** |
| ① Lúc mở thấy được | khoảng 80 px, chưa trọn hàng tiêu đề cột | **trọn hàng tiêu đề cột và 4/5 dòng TỔNG CỘNG** (dòng thứ năm "Chưa rõ" cần cuộn) |
| ② Vùng đứng yên khi kéo ngang | 522 px (khối toàn kỳ), 638 px (khối ngày) | **262 px** ở cả hai (STT 44 + Nhân sự 130 + Loại tiền 88) |
| ② Cột số thấy trọn sau khi kéo | 2–4, có cột bị che dở ("PQC") | **7, không cột nào bị che dở** (bảng tự nhích) |
| ② Điện thoại 390 px, kéo ngang | không thấy cột số nào (vùng đứng yên 433 px > khung 350 px) | vùng đứng yên 220 px, thấy trọn 1 cột số (chỉ ghi lại, không thuộc lượt này) |
| ③ Bấm Gộp | tải cả trang (0,4–0,55 s ngày 28.09; 0,74 s hôm nay) và nhảy về đầu bảng | **0,49 s**, trang không tải lại, vẫn ở ngày 26.09 đang xem |
| ③ Bấm Không gộp | như trên | **0,39 s**, vẫn ở ngày 26.09 |
| ③ Bấm Back sau khi Gộp | tải cả trang | đổi bảng tại chỗ, vẫn ở ngày 26.09 |

Còn một giới hạn: mỗi khối là một bảng riêng, nên cột lệch nhau giữa khối toàn kỳ và khối ngày (khối ngày có thêm
Lần nộp). Bảng chỉ nhích cho khối đang nằm giữa màn hình hiện trọn; khối khác có thể vẫn có cột vắt qua mép cho tới
khi cuộn tới nó rồi kéo ngang lại.

## Bài kiểm

**Bài mới**

| AC | Phía máy chủ (`reports/tests/`) | Phía trình duyệt (`test_bo_cuc_bao_cao_e2e.py`) |
|---|---|---|
| AC-22.24 | `test_bo_cuc_bao_cao.py::test_dau_bang_gon_mot_hang_va_giai_thich_so_lieu` | `test_mo_trang_da_thay_so` |
| AC-22.25 | `test_bo_cuc_khoi.py::test_chi_ghim_cot_dau_nhan_su_loai_tien` | `test_keo_ngang_khong_con_cot_bi_che` |
| AC-22.26 | `test_bo_cuc_khoi.py::test_gop_giu_trang_va_moc_ngay`, `test_gop_van_don_van_ve_trang_dau` | `test_gop_khong_tai_lai_trang` |

**Chạy đỏ trên mã cũ trước khi sửa.** Bài Vận đơn là bài giữ cách cũ, nên xanh cả trước và sau.
- Máy chủ ①: hàng tiêu đề còn đoạn (TT).
- Máy chủ ②: chưa có cờ `sticky`.
- Máy chủ ③: link Gộp bỏ `trang`.
- Trình duyệt ①: khung bảng ở 583 px, đáy dòng tổng cuối 841 > 669.
- Trình duyệt ②: vùng đứng yên 522 px.
- Trình duyệt ③: không có mốc `data-ngay`.

**Bài cũ sửa theo hành vi mới:**
- `test_bo_cuc_bao_cao.py::test_cot_dinh_danh_ghim_theo_cach_xem` (AC-22.13)
- `test_bo_cuc_khoi.py::test_bang_toan_ky_va_moi_ngay_mot_bang` (AC-42.6)
- `test_activity.py` (AC-22.10, AC-22.15)
- `test_quy_vnd_va_tt.py::test_tien_giu_nguyen_moi_dong_mot_loai_tien`

## Lệnh đã chạy

```
pytest reports forms_builder core/tests/test_giao_dien.py tests/test_truy_vet.py -m "not trinh_duyet"
pytest reports/tests/test_bo_cuc_bao_cao_e2e.py reports/tests/test_o_nhap_so_e2e.py -o faulthandler_timeout=300
pytest -m "not trinh_duyet"                          # toàn bộ, như job "bộ chính" của CI
pytest tests/e2e -m trinh_duyet -vv -o faulthandler_timeout=120          # bước e2e 1 của CI
pytest -m trinh_duyet --ignore=tests/e2e -vv -o faulthandler_timeout=120 # bước e2e 2 của CI
```

## Kết quả

Chạy trên máy ảo, từng lượt một, cùng một database kiểm thử.

| Lượt | Kết quả |
|---|---|
| `reports`, `forms_builder`, `test_giao_dien`, `test_truy_vet` | đạt hết |
| Bài trình duyệt Báo cáo tổng hợp (`test_bo_cuc_bao_cao_e2e.py`, `test_o_nhap_so_e2e.py`) | 10 đạt, chạy chung một lượt |
| Toàn bộ `-m "not trinh_duyet"` (job "bộ chính" của CI) | **2.869 đạt, 0 đỏ**, 7 bỏ qua. Bảy bài bỏ qua này cũng bỏ qua trên nền, vì cần fixture tải riêng hay Chrome host |
| Bước e2e 1 của CI (`tests/e2e`) | 37 đạt, **9 đỏ**, 2 bỏ qua. Cả 9 bài đỏ đều ở `tests/e2e/test_pha_luoi_ghi_chu.py` (lưới ghi chú KN CRM) và cùng một lỗi. Trang tải phông chữ Google qua proxy của máy ảo nên báo `net::ERR_CERT_AUTHORITY_INVALID`, mà bài coi mọi lỗi console là đỏ. Ngày 01.10, trên mã chưa sửa, máy ảo cũng ra đúng 9 bài đỏ này. CI không đi qua proxy, nên PR này chạy lại chúng ở đó. Lượt này không đụng mã của lưới |
| Bước e2e 2 của CI (bài trình duyệt còn lại) | **12 đạt, 0 đỏ**, 9 bỏ qua. Chín bài bỏ qua là giá đỡ cần Chrome host, như CI ghi. Ba bài mới cho AC-22.24, 22.25, 22.26 nằm trong 12 bài đạt |

**Ảnh trước và sau.** Chụp cùng điều kiện: máy chủ thử, tài khoản Quản trị viên, nền tối, 1366×768, kỳ
22–28.09.2026. Ảnh không đưa lên kho mã. Trang so sánh có ảnh (riêng tư, chủ dự án mở được): https://claude.ai/artifact/65naYVSZzGp6VB3Bm4PspC.
- ① Khung bảng ở 402 px, thấy 4/5 dòng TỔNG CỘNG.
- ② Kéo ngang 300 px: vùng đứng yên STT · Nhân sự · Loại tiền rộng 262/941 px, 7 cột số thấy trọn, 0 cột bị che dở.
- ③ Cuộn tới ngày 26.09 rồi bấm Gộp: trang không tải lại (dấu `window.__moc` còn nguyên). Dòng đầu tiên dưới phần
  dính là 26.09.

## Chưa kiểm

- Safari và Firefox. Firefox có `scrollend`, Safari chưa, nên dùng nhánh dự phòng chờ 160 ms; chưa thử tay.
- Điện thoại thật, chế độ tối trên máy thật. Bài trình duyệt chỉ chụp nền sáng; quy tắc CSS mới đều dùng token
  theo chế độ.
- Dữ liệu thật trên VPS. Bản web không vào được VPS.
- Kiểm tay ở máy chủ dự án theo quy trình `Staging` (chặng 2): việc của chủ dự án sau khi gộp vào `Staging`.
