# Kịch bản nghiệm thu

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1, sau Giai đoạn 7 |
| Ngày | 03.09.2026 |
| Tài liệu liên quan | `04-tieu-chi-nghiem-thu.md` · `06-ke-hoach-kiem-thu.md` · `backlog.md` mục V4, V5 |

> `docs/04` nói *thế nào là xong*, `docs/06` nói *máy kiểm cái gì*. Tài liệu
> này nói **người kiểm cái gì, bằng tay, theo thứ tự nào, và ghi kết quả ở đâu.**
> Backlog **V4** và **V5** chốt: dồn nghiệm thu về một đợt — đợt đó là đây.

---

## 1. Ai kiểm, bao lâu, cần gì

| Mục | Nội dung |
|---|---|
| Người kiểm | Anh/chị chủ dự án, cộng một người mỗi bộ phận Sale, Marketing, Vận đơn nếu có |
| Dữ liệu | `manage.py du_lieu_mau` (12 tài khoản, mật khẩu in ra cuối lệnh) và tệp `docs/tham-khao/vandon-mau.xlsx` |
| Máy | Máy cá nhân đã `scripts/cap-nhat-local` — mở `localhost:8020` và `localhost:8021/bang-tinh/` |
| Thời gian | Khoảng **2 giờ** cho ba vai, thêm **30 phút** cho phần vận hành |
| Ghi kết quả | Đánh ☐ → ☑ ngay trong tệp này, hoặc chụp màn hình vào `storage/e2e/` |
| Đạt khi | Mọi ô ☐ ở mục 3 và 4 đều ☑, không ô nào ghi "Hỏng" |
| Không đạt thì | Ghi vào `backlog.md` mục 1 kèm ảnh chụp; việc nhỏ sửa ngay, việc lớn xếp Giai đoạn 8 |

**Nguyên tắc:** kiểm bằng mắt người thật, trên dữ liệu thật hoặc gần thật.
Máy đã kiểm 1.060 bài tự động; ở đây chỉ làm những gì máy **không** làm được:
nhìn có đúng không, bấm có thuận tay không, số có khớp Excel không.

---

## 2. Trước khi bắt đầu

```
scripts/cap-nhat-local.sh            (Windows: scripts\cap-nhat-local.bat)
```

Xong thì mở `http://localhost:8020` và đăng nhập `quantri`. Chưa lên được thì
xem `docs/05` mục B5, đừng kiểm tiếp.

| ☐ | Việc | Đạt khi |
|---|---|---|
| ☐ | Mở `localhost:8020` | Thấy màn hình đăng nhập tiếng Việt |
| ☐ | Mở `localhost:8021/bang-tinh/` | Thấy màn hình đăng nhập (dịch vụ Bảng tính chạy) |
| ☐ | Đăng nhập `quantri`, mở Tổng quan | Ô "Sao lưu đêm qua" hiện — có thể ghi "Chưa từng sao lưu", không sao |

---

## 3. Kịch bản theo vai

### 3.1. Sale — `sale.staff`

| ☐ | Bước | Đạt khi | Mã |
|---|---|---|---|
| ☐ | Đăng nhập, nhìn thanh bên | Có Lên đơn, Đơn hàng, Bảng dữ liệu, Bảng tính (mở bảng của Sale, không thấy bảng vận đơn); **không** có Nhân sự, Nhật ký | AC-3.6, AC-11.12 |
| ☐ | Lên đơn cho khách mới, thị trường Canada, 2 sản phẩm, tiền CAD | Đơn lưu, mã `DH-…`, tổng tiền đúng | AC-6.1, AC-6.2 |
| ☐ | Mở Bảng dữ liệu → Bảng vận đơn | Thấy dòng vừa lên: đủ tên khách, số điện thoại, **số lượng từng sản phẩm** ở đúng cột, Quốc gia Canada, Loại tiền CAD, trạng thái "Đã lên đơn" | AC-6.3, AC-11.8 |
| ☐ | Bấm vào một ô trên bảng vận đơn | Ô **không** sửa được, có dòng báo "Bảng này chỉ xem ở đây" và nút Mở Bảng tính | AC-11.7 |
| ☐ | Lên đơn lần hai cùng số điện thoại | Cột "Mua lại lần" của dòng mới là 2 | AC-11.8 |
| ☐ | Gõ thẳng `localhost:8020/bang-tinh/` | Trang từ chối 403 tiếng Việt | AC-11.4 |
| ☐ | Gõ thẳng `localhost:8020/nhan-su/` | Trang từ chối | AC-3.7 |

### 3.2. Marketing — `mkt.staff` rồi `mkt.manager`

| ☐ | Bước | Đạt khi | Mã |
|---|---|---|---|
| ☐ | `mkt.staff` nộp báo cáo ngày | Lưu được; nộp lại cùng ngày thì ghi đè, không sinh dòng đôi | AC-4.1, AC-4.2 |
| ☐ | Cột CPO, giá mess trên biểu mẫu | Tự tính khi gõ số, không sửa tay được | AC-7.10 |
| ☐ | `mkt.manager` mở Báo cáo tổng hợp, nhóm theo ngày rồi theo nhân viên | Có dòng tổng cộng, số khớp bảng Báo cáo Marketing | AC-5.2, AC-5.3 |
| ☐ | Bấm Xuất Excel, mở tệp bằng Excel | Số trong tệp khớp số trên màn hình, tiền là số thật (không phải chữ) | **AC-5.6** |
| ☐ | Mở Bảng dữ liệu → Báo cáo Marketing → **Nhập tệp**, chọn chính tệp vừa xuất | Xem trước ghi đúng cột khớp cột; Xác nhận → tác vụ chạy, "Không có dòng lỗi" | AC-7.7 |
| ☐ | Nhập một tệp `.exe` đổi đuôi `.xlsx` (tạo bằng cách đổi tên bất kỳ tệp nào) | Bị từ chối ngay, thông báo tiếng Việt | AC-7.9 |
| ☐ | Tắt wifi giữa lúc bấm Lọc, rồi bật lại | Trình duyệt báo mất mạng, bật lại bấm lại thì chạy tiếp, không mất dữ liệu đã lưu | mục 12.7 |
| ☐ | `mkt.manager` vào **Bảng tính** trên thanh bên (`localhost:8020/bang-tinh/`) | Mở bảng Báo cáo Marketing; mọi ô có viền; thanh công cụ đủ: Nhập, Xuất Excel, Thêm dòng, Thêm cột, Thư mục mới, B, Màu nền, Cỡ, căn lề, Gỡ định dạng, Lọc theo ô này, Bỏ mọi lọc, Ẩn/hiện cột | **AC-11.12**, **AC-11.18** |
| ☐ | Thanh bên trái: bấm **Hôm qua**, rồi gõ Từ ngày / Đến ngày, rồi tích hai sản phẩm và Áp dụng | Số dòng đổi theo, chip lọc hiện ở trên; Xuất Excel khi đang lọc ra đúng số dòng đó | AC-11.13 |
| ☐ | Gõ vào dòng trống cuối lưới: ngày, marketer, sản phẩm; nhấn Enter | Dòng thành dòng thật ngay, không tải lại trang; vẫn còn dòng trống để gõ tiếp; gõ ngày sai thì ô đỏ kèm lý do, giá trị đã gõ còn nguyên | AC-11.14 |
| ☐ | Bấm một ô, Shift+bấm ô khác để chọn vùng, bấm **B** rồi **Màu nền → vàng**, chọn **Cỡ 16**, căn giữa | Cả vùng đổi ngay; đăng nhập `mkt.staff` mở cùng bảng thấy y hệt; Gỡ định dạng thì về như cũ | **AC-11.15** |
| ☐ | Bấm **Thư mục mới**, đặt tên, rồi chọn thư mục đó ở ô "Bảng này ở thư mục" | Cây bên trái có thư mục chứa bảng; `mkt.staff` thấy cây nhưng không có nút tạo; đổi tên, xoá thư mục thì bảng về không thư mục | AC-11.17 |
| ☐ | Ẩn hai cột bằng **Ẩn/hiện cột**, tải lại trang; thu gọn thanh bên | Cột vẫn ẩn, thanh bên vẫn gọn (nhớ trên trình duyệt); chữ cột A B C đánh lại theo cột đang hiện | AC-11.18 |
| ☐ | Kéo mép phải tiêu đề một cột sang phải; kéo thả tiêu đề cột Sản phẩm ra trước Marketer; tải lại | Cột rộng ra, thứ tự đổi ở cả tiêu đề lẫn mọi dòng; tải lại vẫn giữ; **Đặt lại cột** thì về mặc định | AC-11.18 |
| ☐ | Nhìn cả trang Bảng tính | Không có thanh bên hệ thống; thanh trên chỉ có tên bảng, ô đổi bảng, nút Nền, tên mình; ☰ mở được menu về Tổng quan, Bảng dữ liệu | AC-11.18 |

### 3.3. Vận đơn — `vd.staff`

Mở `http://localhost:8021/bang-tinh/`. Đây là màn hình làm việc của bộ phận.

| ☐ | Bước | Đạt khi | Mã |
|---|---|---|---|
| ☐ | Đăng nhập, nhìn thanh bên | Chỉ có Tổng quan, Bảng tính, Tác vụ nền — không có Lên đơn, Báo cáo | AC-11.4 |
| ☐ | Cuộn ngang lưới | Cột Trùng, Mã đơn, Ngày, Tên khách, Số điện thoại **đứng yên**; cuộn dọc thì hàng tiêu đề đứng yên | **AC-11.1** |
| ☐ | Bấm ▾ ở cột Trạng thái vận chuyển, chọn hai trạng thái, Lọc | Số dòng đổi, dòng "Đang hiện x trên y" đúng, có chip lọc ở trên; bấm × trên chip thì bỏ lọc đó | AC-11.2 |
| ☐ | Thêm lọc cột Tên khách "chứa" một chữ | Hai lọc cộng dồn, chip hiện cả hai | AC-11.2 |
| ☐ | Bấm ô Trạng thái vận chuyển, chọn "Đang giao" | Ô đổi ngay, không tải lại trang; mở Nhật ký bằng `quantri` thấy dòng "Sửa ô van_don.trang_thai_vc" | AC-11.3 |
| ☐ | Bấm ô Ghi chú, gõ hai dòng, Ctrl+Enter | Ghi chú hiện hai dòng trong ô | AC-11.3 |
| ☐ | Dùng phím: mũi tên đi giữa các ô, Enter sửa, Esc huỷ, Tab sang ô kế | Đúng như mô tả, không mất vị trí | AC-11.10 |
| ☐ | Cột Trùng | Hai dòng cùng số điện thoại hiện số 2 tô đỏ; tích "Chỉ số điện thoại trùng" thì còn đúng các dòng đó | AC-11.5 |
| ☐ | Đổi một dòng sang "Hủy trước giao" | Cả dòng tô đỏ nhạt; đổi lại "Đã nhận hàng" thì hết | AC-11.6 |
| ☐ | Bấm Nhập tệp → chọn `docs/tham-khao/vandon-mau.xlsx` → Xác nhận | Tác vụ xong: **Đã nhập 221 dòng, Không có dòng lỗi**; xem trước có báo cột "Lọc trùng" và "Định dạng Ngày" bị bỏ qua | **AC-11.9**, mục 12.3 |
| ☐ | Sau khi nhập, lọc cột Nhân viên vận đơn | Danh sách có PHUONGVH, TIENNLT… kèm số dòng | AC-11.2 |
| ☐ | Bấm Xuất Excel khi đang lọc, mở bằng Excel | Chỉ có các dòng đang lọc, tiêu đề là tên cột tiếng Việt, ngày là ngày thật | AC-7.7, ADR-002 |
| ☐ | Mở lưới trên điện thoại (hoặc thu cửa sổ còn 400px) | Không tràn ngang cả trang, lưới cuộn trong khung, bấm được ô | **AC-11.11**, AC-10.4 |
| ☐ | Bấm **⌕** cạnh một Mã đơn | Lưới còn đúng đơn đó, chip lọc "Mã đơn = …" ở trên, bộ lọc cũ vẫn giữ | AC-11.16 |
| ☐ | Gõ vào dòng trống cuối lưới một vận đơn mới (mã, tên khách, số điện thoại), Enter | Dòng thật xuất hiện, cột Trùng tính ngay nếu trùng số; ở `localhost:8020/bang-tinh/van_don/` thì **không** có dòng trống (chỉ xem) | AC-11.14, AC-11.7 |
| ☐ | Tô nền đỏ một ô Ghi chú ở 8021, rồi mở cùng bảng ở 8020 bằng `quantri` | Ô đỏ ở cả hai nơi; ở 8020 nút định dạng không làm gì (bảng chỉ xem) | AC-11.15 |

### 3.4. Quản trị — `quantri`

| ☐ | Bước | Đạt khi | Mã |
|---|---|---|---|
| ☐ | Bộ phận và team → thêm team mới → sang Nhân sự gán ngay | Team mới hiện ở ô chọn trong cùng phiên | **AC-2.4** |
| ☐ | Tổng quan | Thấy ô Sao lưu đêm qua, Tác vụ nền, Nhật ký | — |
| ☐ | Ma trận phân quyền | Đủ 45 ô, khớp `docs/04` mục 3 | AC-3.x |
| ☐ | Gõ đường dẫn sai `localhost:8020/khong-co/` | Ghi nhận trang hiện gì. **Chưa làm** trang 404 tiếng Việt — backlog K9; đây là điểm biết trước | AC-10.3 |

---

## 4. Vận hành — người vận hành

| ☐ | Bước | Đạt khi | Mã |
|---|---|---|---|
| ☐ | `scripts/backup.sh` | In "Đã sao lưu: knjsc-….dump", tệp xuất hiện trong `storage/backups/` | AC-10.6 |
| ☐ | Chạy `scripts/backup.sh` thêm 30 lần (hoặc chép tệp thành 35 bản đổi tên) rồi chạy lại | Thư mục còn đúng 30 bản mới nhất | AC-10.6 |
| ☐ | Sửa một ô bất kỳ trên Bảng tính, rồi `scripts/restore.sh --toi-chac-chan` với bản sao lưu **trước** khi sửa | Đăng nhập lại: ô trở về giá trị cũ, mọi thứ khác còn nguyên | **AC-10.5**, mục 12.6 |
| ☐ | Tắt Docker Desktop, mở lại, chờ 1 phút | `localhost:8020` và `8021` tự lên, không cần gõ lệnh | docs/05 B5 |
| ☐ | Đo tải: `manage.py seed_perf` rồi Locust 50 người 1 phút (xem `app/tests/perf/README.md`) | Kịch bản in **ĐẠT** — p99 dưới 3 giây | **AC-10.1** |
| ☐ | Trong lúc Locust chạy, mở Bảng tính bằng tay | Vẫn dùng được, không chờ quá vài giây | NFR-2 |
| ☐ | Cài từ đầu trên máy sạch theo `docs/05` B2 | Tới màn hình đăng nhập không cần hỏi ai | mục 12.1 |

---

## 5. Sau khi kiểm

| Kết quả | Việc tiếp |
|---|---|
| Mọi ô ☑ | Ghi ngày nghiệm thu vào `backlog.md` mục 6, đóng **V4** và **V5**; sang Giai đoạn 8 |
| Có ô "Hỏng" | Mỗi ô một dòng trong `backlog.md` mục 1 kèm mã AC và ảnh chụp; sửa xong chạy lại đúng ô đó |
| Có ô "Không rõ đúng hay sai" | Đó là câu hỏi nghiệp vụ — ghi vào `backlog.md` mục 5 (H1 tới H6 đang ở đó) |

Điều kiện hoàn thành phase 1 (`docs/04` mục 13) cần cả bảy điều; tài liệu này
lo điều 3, 4, 5 và 6. Điều 7 — bàn giao tài liệu — là `docs/05` phần B.
