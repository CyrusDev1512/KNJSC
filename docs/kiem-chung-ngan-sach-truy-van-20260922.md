# Biên bản — Cắt ba lượt hỏi thừa mỗi trang, đóng K24 (22.09.2026)

## Vì sao có lượt này

Hai bài `tests/test_hieu_nang.py` mang dấu `xfail` từ lâu: thời gian đạt (0,4 s và 1,1 s
trên 50.000 dòng) nhưng đếm **12 lệnh truy vấn**, hơn ngân sách 10 của quy tắc Q2. Ghi nợ
là K24. Đây là món 5 trong bảng nợ kỹ thuật.

Đính chính một chỗ tài liệu sai: `docs/handoff/project-brief.md` mục 8 ghi **hai** chỗ
`xfail` (K23 hộp lọc cột trong Playwright, K24 ngân sách truy vấn). Thực tế trong mã chỉ
còn **một** dấu `xfail` ở mức module, phủ hai bài — K23 không còn.

## Ba lượt hỏi thừa, tìm bằng cách nào

Không đoán: bọc `connection.execute_wrapper` in ra ngăn xếp Python của từng truy vấn khớp
mẫu, chạy trên dữ liệu nhỏ (số lệnh không phụ thuộc số dòng).

| # | Thừa ở đâu | Ai gọi |
|---|---|---|
| 1 | `/bang-tinh/` hỏi phạm vi quyền **ba lần** cho cùng một bảng: `exists()` chọn bảng mặc định, `exists()` kiểm riêng bảng vận đơn, rồi `get_object_or_404` lấy bảng | `crm/views.py` `_ma_bang_mac_dinh` → `bang_tinh_xem` → `_bang` |
| 2 | `user.profile` nạp lười ở mọi yêu cầu đã đăng nhập | Django `ModelBackend.get_user` |
| 3 | `user.profile.department` nạp lười thêm một lượt nữa | `org_service.is_accountant`, gọi từ `forms_builder/managers.py` `in_scope` |

Hai lượt 2 và 3 trả ở **mọi trang**, không riêng lưới.

## Đã sửa gì

1. `crm/views.py`: `_ma_bang_mac_dinh` trả **chính bảng** thay vì mã (`_bang_mac_dinh`), và
   `bang_tinh_xem` hỏi phạm vi quyền đúng một lượt rồi tự phân nhánh 404 / chuyển sang Lên
   đơn cho Sale / `OutOfScopeError`. Hành vi giữ nguyên từng nhánh.
2. `core/auth_backends.py`: thêm `get_user` lấy kèm `profile__department` và `profile__team`
   trong cùng một lượt hỏi.
3. `tests/test_hieu_nang.py`: bỏ `xfail`, và thêm `_vao_lam()` — mở một trang bỏ đi sau khi
   đăng nhập rồi mới bấm giờ. Lý do: yêu cầu **đầu tiên** sau đăng nhập ghi `last_seen_at`
   vào phiên (SAVEPOINT + UPDATE + RELEASE). Đó là giá của lần đăng nhập, không phải giá
   của màn hình — `SessionTimeoutMiddleware.GHI_LAI_SAU` chỉ ghi lại mỗi 60 giây nên người
   dùng thật không trả khoản đó ở từng trang.

**Ngân sách vẫn là 10, không nới một lệnh nào.**

## Số đo

Đếm trên máy ảo, PostgreSQL 16, cùng một tài khoản nhân viên Vận đơn:

| Màn hình | Trước | Sau |
|---|---|---|
| Bảng dữ liệu ERP `/bang/van_don/` | 11 | **9** |
| Lưới CRM `/bang-tinh/` | 13 | **9** |
| Lưới CRM `?trung=1` | 13 | **9** |

Trên đúng bộ 50.000 dòng của bài `cham` cũng **9 lệnh** (đo riêng bằng `CaptureQueriesContext`
sau một lượt làm nóng).

| Bài | Kết quả |
|---|---|
| `pytest tests/test_hieu_nang.py` (bỏ `xfail`, 50.000 dòng thật) | **2 đạt** |
| `pytest -m "not trinh_duyet"` toàn bộ, gồm cả `cham` | **2.549 bài, 0 đỏ, 7 bỏ qua** |

## Vòng review nội bộ (cùng ngày, trước khi bàn giao)

Chạy review mức high trên chính diff này — 6 phát hiện, sửa 5:

1. `_bang_mac_dinh` từng duyệt **cả phạm vi** trong bộ nhớ để chọn một bảng → đổi thành một
   truy vấn `LIMIT 1` xếp bảng vận đơn lên trước (`Case/When`), không kéo trăm bảng về chỉ
   để lấy một.
2. Bỏ `profile__team` khỏi `get_user`: phạm vi quyền đọc `department_id` và
   `scope_team_ids()` (truy vấn riêng của Leader), số đo K24 không thấy team bị nạp lười —
   join đó không được số nào chống lưng.
3. Lượt làm nóng đổi từ *chính trang sắp đo* sang `/dang-nhap/`: mở trước đúng trang đó thì
   mọi truy vấn "lượt xem đầu" của nó cũng bị nuốt theo, ngân sách thành đo lượt xem thứ hai.
4. Bỏ dòng `nav_current` trùng ở `bang_tinh_xem` (đã có trong `_luoi`).
5. `docs/handoff/project-brief.md` sửa thẳng dòng "hai bài xfail" — lượt trước chỉ đính
   chính trong backlog mà để nguyên tệp sai, đúng kiểu lệch tài liệu mà chính biên bản này
   phàn nàn.

**Từ chối một phát hiện:** đổi tên `_luoi`, `_bang_mac_dinh`, `_vao_lam` sang tiếng Anh theo
quy ước đặt tên. Cả `crm/views.py` và tệp đo đang đặt tên tiếng Việt (`_cac_bang`, `_bang`,
`bang_tinh_xem`, `_bam_gio`…); đổi riêng ba hàm mới thì tệp thành hai thứ tiếng trộn. Dọn
tên cả tệp là quyết định riêng của chủ dự án, không giấu vào PR hiệu năng.

Sau vòng sửa, đo lại: **cả ba màn hình vẫn 9 lệnh**, hai bài 50.000 dòng vẫn xanh.

## Chưa kiểm

- Chưa đo lại thời gian trên VPS; số ở đây là máy ảo.
- Hai lượt hỏi cắt được (hồ sơ và bộ phận) có lợi cho **mọi trang**, nhưng chưa đo mức lợi
  đó dưới tải nhiều người — việc đó thuộc phần đo p95 trên VPS, do nhánh KNGUARD lo.
- Không có thao tác trình duyệt trong lượt này.
