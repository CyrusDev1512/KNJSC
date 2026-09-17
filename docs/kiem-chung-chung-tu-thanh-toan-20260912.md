# Kiểm chứng trạng thái và chứng từ thanh toán — 12.09.2026

> Cập nhật 12.09.2026: theo yêu cầu chủ dự án, đã chuyển nhánh codex/chung-tu-thanh-toan về checkout chính C:/KNJSC/KNJSC và kích hoạt app local 8021. Đã áp dụng orders 0007, org 0004; không chạy seed. Các mô tả chưa kích hoạt bên dưới ghi trạng thái bàn giao trước bước này. Chưa commit/push; bản sao checkout cũ giữ nguyên nội dung, ở detached HEAD.

## Mã và phạm vi

- Nhánh `codex/chung-tu-thanh-toan`, gốc `95988c9`.
- Checkout `C:/KNJSC/KNJSC-chung-tu-thanh-toan`; checkout gốc giữ nguyên.
- Chưa commit/push, chưa áp migration vào database/app local 8021.
- [ADR-025](quyet-dinh/025-trang-thai-va-chung-tu-thanh-toan.md) thay quy tắc trạng thái
  tự tính; H7 chỉ chốt chứng từ, không mở quyền nhập tiền/xác nhận đối soát.

## Đã triển khai

| Nhóm | Kết quả |
|---|---|
| Trạng thái | Bỏ khóa riêng; dùng autosave/CAS/history/Undo hiện có; sửa chi tiết không ghi đè trạng thái; nhập trạng thái rõ ràng được giữ |
| Kho chứng từ | Danh sách/Kho ảnh, tìm/lọc, phân trang 50; tạo từ chọn/dán ảnh; Ref thủ công |
| Quản lý | Vận đơn thêm trong scope; Kế toán/Admin sửa, bổ sung/gỡ ảnh, xóa mềm/khôi phục; phiên bản chống ghi đè |
| Quyền đọc | Kế toán xem toàn bộ Vận đơn mới; không mở quyền sửa ô/phân công/ERP; ảnh kiểm quyền riêng |
| Bill | Tối đa hai Ref và đường mở đủ; giữ Bill cũ; đọc metadata một truy vấn cả khối; xuất Ref không nhúng ảnh |
| Lưu | Hai bảng `orders_paymentdocument`/`orders_paymentimage`; file UUID riêng tư; replay tạo, dọn file khi rollback; journal Bill |
| Migration | Bổ sung orders 0007 và org 0004; reverse/forward trên DB test giữ nguyên dữ liệu dòng cũ |

## Kiểm thử

TDD ban đầu: **3 fail** đúng ba hành vi: không sửa được trạng thái, chi tiết đổi trạng thái,
chưa có URL kho chứng từ. Sau triển khai:

- Suite CRM/orders/forms_builder/documents/core: **1.129 passed, 4 failed, 10 skipped**,
  144,71 giây. Không coi skip là đạt.
- Nhóm mới có 11 bài: trạng thái/Undo/CAS, nhập rõ trạng thái, quyền,
  tạo lặp, Ref trùng, private image, xóa/khôi phục, Bill/Excel/filter,
  rollback/file, metadata không N+1, migration và hai thread sửa cùng chứng từ.
- Hai thread cùng phiên bản: **1 saved + 1 conflict**, phiên bản chỉ tăng một lần.
- Chrome thật qua Playwright, headless trên Windows, DB test 10.000 dòng: **1 passed**,
  29,49 giây. Kiểm 1440/1280/390 px, hình chụp được rà; sửa bố cục hẹp và kiểm lại.
  Bill mở đúng ảnh, Escape đóng, tạo/sửa Ref, chọn file và Ctrl+V dán thêm ảnh đạt.
  Chọn ảnh 2 mới có request ảnh 2. Không có pageerror.
- Kiểm cú pháp JS và `git diff --check` đạt; cảnh báo đổi LF/CRLF không phải lỗi nội dung.

Bốn lỗi đều tái hiện khi chạy trên checkout gốc `95988c9`:

1. `test_dich_vu_bangtinh_chi_co_bang_tinh_va_dang_nhap` — kỳ vọng markup điều hướng.
2. `test_erp_chi_con_lien_ket_sang_kn_crm` — kỳ vọng markup liên kết CRM.
3. `test_moi_lop_css_dung_trong_template_deu_ton_tai[statistics.html]`.
4. `test_moi_o_nhap_deu_co_nhan[statistics.html]`.

Không sửa tiện các lỗi nền này. Bài quét CSS được bổ sung file CSS chứng từ;
bài trạng thái cũ được đổi kỳ vọng theo quyết định thay thế. Kiểm cấm COUNT toàn bảng
vẫn giữ, cho phép COUNT cửa sổ trên chứng từ **trong khối** và có test một truy vấn riêng.

Các lỗi harness đã sửa trước kết quả cuối: đợi `<option>` phải dùng trạng thái attached;
đóng FileResponse trong TestCase gây đóng connection; teardown thread cần đóng connection
riêng; test dọn file phải có thư mục riêng từng test. Không tính các lượt đó là đạt.

## Đo giới hạn với dữ liệu 10k

Fixture: 10.000 dòng có metadata chứng từ/ảnh synthetic; file test nhỏ được dùng chung
cho phần seed. Đây không phải phép đo dung lượng hay tải 10.000 ảnh thật.

| Phép đo | Trước metadata | Sau metadata |
|---|---:|---:|
| Đọc khối phía Python, p50, 30 mẫu | 27,56 ms | 31,39 ms |
| Đọc khối phía Python, p95, 30 mẫu | 85,48 ms | 78,93 ms |
| Request ảnh khi chỉ mở/cuộn lưới | Không có tính năng | **0** |
| Cache trong 12 lượt cuộn xuyên khối | Không đo lại | Tối đa **10 khối** |
| Ô DOM trong vùng dựng | Không đo lại | **540–690** |

So trước/sau chỉ thay serializer lấy từ commit `95988c9` trên cùng fixture và code còn lại;
không phải chạy hai bản toàn hệ thống độc lập. Trung vị tăng 3,83 ms; p95 dao động,
không dùng chênh lệch đó để tuyên bố nhanh hơn. Docker local có tải nền kiểm thử.

HTTP đọc khối 100 dòng: 12 mẫu, p50 **40 ms**, p95 **94 ms**.
Từ bấm Ref đến ảnh synthetic sẵn sàng: **132 ms**, một mẫu; không phải p95,
không đại diện ảnh bill điện thoại nhiều MB. [Dữ liệu thô](evidence/payment-20260912/result.json).

## Lệnh tái hiện

Từ checkout mới, dùng project Docker đang có, không chạy entrypoint seed:

```powershell
docker compose -p knjsc -f deploy/docker-compose.yml run --rm --no-deps -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_payment_test web pytest crm/tests orders/tests forms_builder/tests documents/tests core/tests --tb=short
```

Chrome dùng database test khác, cổng riêng:

```powershell
git show 95988c9:app/crm/services/master_grid_service.py > app/.payment-baseline.py
docker compose -p knjsc -f deploy/docker-compose.yml run --rm --no-deps -p 8858:8858 -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_payment_browser -e KN_PAYMENT_BROWSER=1 web pytest crm/tests/test_payment_browser_server.py --liveserver=0.0.0.0:8858 -s
# Khi app/.payment-ready.json xuất hiện, chạy từ terminal khác với Playwright đã có:
node scripts/kiem-thu-payment-ui.cjs
```

Node cần `NODE_PATH` trỏ tới runtime Playwright sẵn có; không cài dependency mới.
Baseline tạm có thể bỏ sau phép đo. File test đi vào thư mục tạm của settings.test;
không dùng khách thật, 20 khách mẫu hoặc đơn Phạm Thái Hưng.

## Bằng chứng và giới hạn

- Theo Git: mã/test/script, ADR/tài liệu và JSON số đo trong `docs/evidence/payment-20260912/`.
- Ảnh và log đầy đủ: `.agents/design-state/review/payment/` (gitignore), gồm
  `library-1440.png`, `library-1280.png`, `library-390.png`, `viewer.png` và `logs/`.
- Hai ảnh bill thực tế trước đó không truy cập được; không triển khai OCR hoặc suy cấu trúc ảnh.
- Chưa kiểm trên điện thoại/bộ gõ thật, ảnh bill thực dung lượng lớn, hay thao tác thu quyền
  đúng lúc popup đang mở bằng hai trình duyệt; đường ảnh bị từ chối sau mất scope đã có test server.
- Chưa chạy tải nhiều người/upload nặng hoặc phục hồi bản sao lưu thực tế.
  Không tuyên bố toàn bộ ma trận UI/performance hoặc toàn bộ suite đã đạt.
- Bản sử dụng 8021 chưa chuyển sang checkout này; cần triển khai mã và migration mới
  trước khi người dùng thấy chức năng. Không tự đổi dữ liệu/tài khoản đang dùng để minh chứng.
