# Biên bản — Cột sản phẩm mặc định ẩn (22.09.2026)

## Vì sao có lượt này

Chủ dự án mở màn hình **Cấu trúc cột** của bảng Vận đơn mới và thấy ba cột `sl_yuna`,
`sl_sda`, `sl_ada` — cột của ba sản phẩm gõ thử. Câu hỏi: *"rõ ràng tôi cũng đã có commit
để cắt rồi mà"*, và nhắc rằng điều đã chốt là **tương lai cột sản phẩm không hiện ra nữa**.

Đối chiếu lại thì chủ dự án nhớ đúng ý, còn bản dựng 19.09 làm **có điều kiện**:

- ADR-039 quyết định 6 chỉ ẩn cột sản phẩm mới **khi cả nhóm đã ẩn**
  (`an_ca_nhom = bool(cu) and all(c.is_hidden for c in cu)`, `dispatch_service.py:156`).
- Biên bản phát hành `kiem-chung-phat-hanh-vps-20260919-gop.md` ghi `is_hidden` **0/72 cột**
  và để lại "Việc 5: Admin bấm ẩn nhóm cột sản phẩm một lần".
- Chưa ai bấm → điều kiện luôn sai → mỗi sản phẩm mới lại mọc một cột hiện trên lưới.

Hai chỗ **không phải lỗi**: màn hình Cấu trúc cột cố ý liệt kê đủ mọi cột kể cả cột ẩn
(`forms_builder/views.py:146`, chú thích ở `views.py:188`) vì đó là chỗ bật lại; và nút bấm
ẩn/hiện thì chạy đúng từ 19.09.

## Đã làm gì

| # | Thay đổi |
|---|---|
| 1 | `dispatch_service.sync_product_columns` tạo cột sản phẩm với `is_hidden=True` luôn, bỏ điều kiện `an_ca_nhom` |
| 2 | Migration dữ liệu `orders/0011_an_cot_san_pham_dang_co`: ẩn mọi cột `sl_*` đang hiện của bảng `workflow="waybill"`; chạy ngược là `RunPython.noop` |
| 3 | ADR-039 thêm mục "Bổ sung 22.09.2026"; CLAUDE.md mục lưới CRM ghi mặc định mới |
| 4 | `crm/tests/test_an_cot.py`: AC-39.1, 39.2, 39.3, 39.6 đổi sang cột `thanh_pho` (dùng `sl_*` thì không còn chứng minh được gì vì nó đã ẩn sẵn); AC-39.5 viết lại theo mặc định mới; thêm AC-39.8 và AC-39.9 |
| 5 | `crm/tests/test_bang_tinh.py`: bài lọc số nguyên chuyển từ `sl_retinol_cream` sang `so_luong`, fixture thêm `so_luong` |

Không xoá cột nào, không đụng một ô dữ liệu nào — không phạm BR-4.

## Hệ quả đã biết, chưa sửa

`grid_service.build_grid` đọc bộ lọc từ `display_columns`, tức danh sách **đã loại cột ẩn**.
Nên đường dẫn cũ lọc theo `?f_sl_x__trong=…` giờ **trả về mọi dòng chứ không báo lỗi** — lọc
bị bỏ qua lặng lẽ. Đây là hành vi có từ ADR-039 (19.09), nhưng từ lượt này nó áp vào cả nhóm
cột sản phẩm nên dễ gặp hơn. Chính bài lọc ở `test_bang_tinh.py:125` đỏ vì điều này, và đó là
cách tôi phát hiện.

Bài **AC-39.9** khoá hành vi lại để nó không trôi. Sửa hay không chờ chủ dự án quyết: cho lọc
theo cột ẩn thì lưới lọc bằng thứ người dùng không thấy và không có chip bộ lọc; còn báo lỗi
thì mọi đường dẫn cũ vỡ.

## Đã đo gì

| Việc | Kết quả |
|---|---|
| `pytest crm orders forms_builder -m "not trinh_duyet and not cham"` | xanh sau khi sửa hai bài nêu ở trên |
| `pytest tests/test_truy_vet.py` | xanh; bộ đếm `docs/06` lên **241 / 228 / 204 trên 228** |
| `pytest` toàn bộ `-m "not trinh_duyet and not cham"` | ghi ở mục dưới |

## Chưa kiểm

- **Chưa chạy trên VPS.** Máy ảo Claude Code trên web không tới được VPS; phát hành và kiểm
  trên domain thật vẫn do chủ dự án hoặc Claude Code CLI ở máy chủ dự án làm.
- Chưa kiểm bằng trình duyệt trên dữ liệu dev; lượt này chỉ có bài kiểm tự động.
- Ba sản phẩm gõ thử "YUNA", "sda", "áda" **vẫn còn** trong danh mục sản phẩm. Cột của chúng
  nay ẩn, nhưng bản thân sản phẩm vẫn hiện ở ô chọn Sản phẩm của Lên đơn. Muốn dọn thì tắt bán
  (`is_active = False`) — chưa làm, chờ chủ dự án xác nhận chúng không dùng cho đơn thật.
