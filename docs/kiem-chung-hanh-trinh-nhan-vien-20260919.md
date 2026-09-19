# Biên bản — Bài đầu-cuối đi trọn hành trình nhân viên (19.09.2026, đêm)

## Vì sao có bài này

Hai lỗi chủ dự án báo sáng 19.09 (hộp lọc cột sót mục của cột trước; lên đơn khách cũ giữ tên cũ)
đều nằm **giữa** các màn hình. Bộ kiểm hiện có cắt hệ thống theo từng mảnh nên không mảnh nào nhìn
thấy chỗ nối.

Rà 50 script `scripts/kiem-thu-*.cjs` trước khi viết, để không làm trùng:

| Script | Có sẵn | Thiếu |
|---|---|---|
| `kiem-thu-erp-hub.cjs` | đăng nhập, lưới, gõ ô, 5 tài khoản, lên đơn | chặn cứng `luu-json/` (dòng 77) nên không kiểm ghi; không hộp lọc cột; không lời nhắc khách; đòi fixture pytest cổng 8811/8812 |
| `kiem-thu-master-manual-ui.cjs` | gõ ô → reload → giá trị còn; hộp lọc cột thật | không lên đơn; một tài khoản; đòi fixture cổng 8031 |
| `kiem-thu-van-don-ui.cjs` | script duy nhất chạy trên server thường 8021, chạm cả lưới lẫn form lên đơn | tự khai "chỉ kiểm đọc"; không thao tác ghi nào |

`grep -l "nhac-khach\|nhac_khach" scripts/*` → **rỗng**. Lời nhắc khách chưa từng đi qua trình duyệt.

## Vì sao là bài pytest, không phải script `.cjs` thứ 51

Kho **không có CI** (`.github/` không tồn tại), nên 50 script kia chỉ chạy tay và gần như cái nào cũng
đòi một fixture pytest dựng sẵn server ở cổng riêng (8031, 8035, 8811/8812, 8858…). `app/tests/e2e/`
ngược lại chạy cùng `pytest` mỗi lượt và **tự bỏ qua** khi máy thiếu Chromium.

Đánh đổi đã chấp nhận: bài chạy trên **DB test dựng sẵn**, không phải 120.545 dòng dev. Lặp lại được,
nhưng không phản ánh dữ liệu thật của công ty.

## Bài làm gì

`app/tests/e2e/test_hanh_trinh_nhan_vien.py`, dấu `trinh_duyet` + `cham`, URLconf `knjsc.urls_bangtinh`:

1. `staff_vd` đăng nhập, mở lưới `van_don`.
2. Gõ thẳng vào ô Thành phố rồi Enter (ADR-033), chờ tự lưu.
3. Kiểm **hai chiều**: `DataRecord` trong DB mang giá trị mới, **và** tải lại trang thì ô vẫn còn.
4. Mở hộp lọc cột Tên khách, gõ vào ô tìm, rồi mở hộp lọc cột Quốc gia — tiêu đề phải là Quốc gia và
   không còn ô tích nào của cột trước.
5. Mở phiên thứ hai, `staff_sale_1` đăng nhập, vào Lên đơn, gõ số của khách đã có — ô Tên khách tự điền.
6. Sửa tên đi — phải hiện cảnh báo nêu đủ số điện thoại, tên cũ và tên mới.
7. Không lỗi JavaScript nào trên cả đường đi.

Không thêm mã tiêu chí mới. Docstring ghi AC-11.43, AC-11.42, AC-6.10 — xác nhận lại chúng ở chỗ nối.

## Đã đo gì

| Việc | Kết quả |
|---|---|
| `pytest tests/e2e/test_hanh_trinh_nhan_vien.py` | **xanh** |
| Đưa lỗi trở lại: `hx-target` của `_loc_cot.html` về `#hop-loc` | **đỏ** đúng bước 4 |
| Đưa lỗi trở lại: vô hiệu listener `htmx:afterSwap` tự điền tên (`order-entry.js:106`) | **đỏ** đúng bước 5 |
| `pytest tests/test_truy_vet.py tests/e2e` sau khi khôi phục | **43 đạt, 0 đỏ** |

Lần chạy tay trước đó trên DB dev 120.545 dòng (không phải bài này, không lặp lại được): mở lưới 780 ms
tới ô đầu tiên, mở hộp lọc cột 817 ms, hộp lọc Tên khách ghi "94.554 giá trị — quá nhiều để chọn tay".

## Chưa kiểm

- Bài chạy trên DB test, **không** trên dữ liệu thật và **không** trên VPS.
- Chỉ một cỡ màn hình 1366×800; bản điện thoại 390px vẫn do `tests/e2e/test_dien_thoai.py` lo.
- Nhánh "cột nhiều giá trị" của hộp lọc (ngưỡng `GRID_FILTER_LIST_MAX`) do bài đơn vị AC-11.43 lo;
  bài này chỉ kiểm việc đổi cột không sót mục.
