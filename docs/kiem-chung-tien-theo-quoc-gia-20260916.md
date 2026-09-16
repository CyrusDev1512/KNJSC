# Kiểm chứng tiền theo quốc gia — 16.09.2026

Nền `7b827a6`, nhánh `codex/crm-update-solar-ui`. Bàn giao local, chưa commit,
push hoặc phát hành VPS. Quyết định: [ADR-031](quyet-dinh/031-tien-theo-quoc-gia-va-pttt.md).

## Phạm vi

Hoa Kỳ/USD, Canada/CAD, Philippines/PHP; chỉ chọn Zelle/PayPal. Loại tiền trên
form/lưới không sửa độc lập. Xác nhận đổi quốc gia giữ số tiền, không quy đổi;
đồng bộ loại tiền trong giao dịch, kiểm CAS/quyền và giữ đơn gốc bất biến.
Giữ dữ liệu lịch sử; không seed hoặc ghi thử vào database đang sử dụng.

## Bằng chứng

Docker PostgreSQL 16 riêng `knjsc-market-db`, network `knjsc-market-test`.
Các lệnh pytest chạy image `knjsc-bangtinh`, mount app hiện hành, môi trường
`POSTGRES_HOST=knjsc-market-db`, `RUN_MIGRATIONS=0`, `--ds=knjsc.settings.test`.
DB pytest có tiền tố `test_`; không dùng DB vận hành/local làm kiểm thử.

| Lượt | Kết quả |
|---|---|
| TDD: `crm/tests/test_market_currency.py` trước sửa | 8 thất bại đúng hành vi thiếu |
| Tập mới sau hoàn thiện, gồm quyền Vận đơn/profile khác | 15 đạt |
| `pytest crm/tests orders/tests forms_builder/tests --tb=short -o addopts= --ds=knjsc.settings.test -q` | 533 đạt, 1 lỗi nền, 17 skip |
| `pytest crm/tests/test_market_currency.py tests/test_luong_ba_bo_phan.py --tb=short -o addopts= --ds=knjsc.settings.test -q` | 15 đạt, 2 lỗi nền |
| Chrome thật 1440/390, `scripts/kiem-thu-tien-theo-quoc-gia.cjs` | Cả hai kích thước đạt, không pageerror |
| `crm/tests/test_market_currency_browser.py`, `MARKET_CURRENCY_BROWSER=1` | 1 đạt; đối chiếu Order và DataRecord sau thao tác Chrome |
| Node `kiem-thu-master-queue-unit.cjs` | Đạt debounce/retry, chấp nhận/hủy xác nhận tiền |
| Node working-copy, autosave-unit, conflict-unit | Đạt |
| Migration orders 0007→0008→0007→0008 trên DB riêng | Đạt; `sqlmigrate 0008` no-op |
| `makemigrations orders --check --dry-run`, Django check, Node syntax | Đạt |

Chrome: Lên đơn đổi US→CA (hủy rồi nhận)→PH, giá giữ 12.50, hai sản phẩm tổng
25 PHP, PayPal; vào lưới hủy rồi xác nhận US→CA, giữ 10.00; kiểm khóa cột tiền,
sửa PTTT thực tế và đối chiếu DB. Dùng điều khiển Cột để đưa ba cột cần kiểm
vào vùng nhìn; không sửa trực tiếp state JS. Tiếp tục dùng Ctrl+S sau khi hủy.
Mở/đóng ô lịch sử “Thẻ” giữ giá trị; chỉ hai lựa chọn mới được bật để chọn.

Functional thêm: xác nhận hết hiệu lực khi dòng thay đổi, nhiều dòng trong một
giao dịch, hoàn tác quốc gia, biên nhận replay/compact, giả mạo loại tiền,
phương thức cũ, dòng 0 tiền, nhập tệp sai tiền và nhân sự ngoài phạm vi.

## Lỗi nền và giới hạn

Ba lỗi đều tái hiện trên archive Git nguyên trạng `7b827a6` trong DB riêng:

- `crm/tests/test_waybill_new.py::test_export_import_roundtrip_and_preview_ambiguous`:
  test kỳ vọng nhập lại mã đơn đã có; service nhập hiện hành chặn mã trùng.
- `tests/test_luong_ba_bo_phan.py::test_mot_ngay_cua_cong_ty` và
  `test_moi_bo_phan_chi_thay_phan_cua_minh`: test kỳ vọng form ERP `/len-don/`
  trả 200, trong khi quyết định đã chuyển form sang CRM nên GET trả 302.

Không sửa các hợp đồng cũ này trong tác vụ tiền tệ. Không báo toàn suite đạt.
17 skip ở lượt hồi quy không được tính là kiểm chứng; Chrome tính riêng ở trên.
Lượt hồi quy cảnh báo dọn DB test còn hai connection từ kiểm đồng thời;
container DB tạm được dọn ở cuối, không đụng volume DB thật.

Không chạy kiểm tải 100.000 dòng/lâu dài trong tác vụ này; không tuyên bố tăng
tốc. Các test ngân sách truy vấn hiện có trong nhóm CRM/forms_builder đã chạy.
Log/screenshot ở `storage/market-currency` (gitignore), không chứa mật khẩu
người dùng thật. Báo cáo này lưu kết quả để theo dõi ở các máy khác.

Local ERP/CRM `manage.py check` đều đạt; migration 0008 đã có, không còn bước
áp dụng. Đã nạp lại worker local sau khi kiểm không có tác vụ đang chạy
(`RUN_MIGRATIONS=0`), để nhập nền dùng cùng danh mục. Container/network DB test
đã dọn; giữ log/screenshot, không sửa VPS. Lệnh xóa archive nguồn đối chứng
bị công cụ từ chối “blocked by policy”; `storage/market-currency/baseline`
và `baseline.zip` vẫn còn (được gitignore, không thuộc diff bàn giao).

## Cách kiểm tra local

1. Lên đơn: chọn quốc gia, kiểm Loại tiền tự đổi và không gõ được; PTTT chỉ
   có Zelle/PayPal, mặc định chưa chọn.
2. Nhập giá rồi đổi quốc gia: hủy giữ lựa chọn cũ, đồng ý giữ số tiền.
3. Trong bảng có profile Vận đơn: sửa Quốc gia ở dòng có tiền; kiểm xác nhận,
   tiền tệ, lịch sử và dữ liệu giữ nguyên khi hủy. Đơn gốc không đổi theo.

Thêm phương thức sau này theo danh mục chung tại ADR-031; chưa có nút tự thêm.
