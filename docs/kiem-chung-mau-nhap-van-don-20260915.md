# Tải mẫu Excel vận đơn — 15.09.2026

## Bổ sung trạng thái Git — 15.09.2026

Code mẫu Excel đã lên GitHub trong `c41d8f0`, được hợp nhất tại `f971683`.
Các mô tả local/chưa push phía dưới là bằng chứng tại thời điểm kiểm, không
phải trạng thái phát hành mới nhất. Lỗi nhập trên VPS chỉ tạo 6.667/10.000
dòng được điều tra riêng trong [daily tasks](daily-tasks.md); không dùng
kết quả nhập 10.000 dòng local để kết luận file trên VPS nhập đủ.

## Chuẩn bị push GitHub

Bản phát hành tách riêng 15 file của mẫu nhập trên nền `072cee4`, không kèm
chức năng Bảng nhận đơn đang làm ở checkout chính. Kiểm đúng bản tách riêng:
30 passed trong 20.51s; một cảnh báo dọn DB test do hai kết nối khác còn mở.
Không cưỡng chế đóng kết nối hay xóa DB. `git diff --check` đạt.

**Trạng thái mới nhất:** đã sửa và kiểm lại trên local; xem mục
“Cập nhật 15.09.2026 — Sửa theo yêu cầu sau kiểm thử” ở cuối tài liệu.
Các lỗi ghi ngay dưới đây là lịch sử trước sửa.

## Bổ sung kiểm thử như người dùng — chưa đạt nghiệm thu toàn luồng

Kiểm qua trình duyệt Codex trên cổng **18031**, database riêng
`test_template_user_qa_20260915_0940`. Tài khoản và khách hàng đều là dữ liệu
kiểm thử; không nhập vào local 8021 hoặc VPS. Các kết quả bên dưới bổ sung và
giới hạn kết luận “đạt” của vòng kiểm tự động ban đầu.

### Đã thao tác và xác nhận

| Ca | Kết quả |
|---|---|
| Bấm tải cả ba mẫu trên thẻ | Có download đúng bảng, không chứa khách hàng |
| Điền và nhập 3 khách/bảng qua chọn file → xem trước → xác nhận | Cả ba tác vụ đều tạo 3 dòng, 0 lỗi |
| Kiểm lại lưới | Ngày, mã đơn, khách, điện thoại, Zipcode đúng; giữ số 0 đầu |
| Vận đơn với chi tiết sản phẩm hợp lệ | Lưới hiện sản phẩm ×2; không phát sinh lỗi nhập |
| File DB có 1 dòng đúng, 1 thiếu điện thoại, 1 Đã về TK không hợp lệ | Nhập 1, bỏ 2; báo đúng hàng Excel 3 và 4 |
| File DB đúng 10.000 dòng, khoảng 428 KB | Nhập đủ 10.000, 0 lỗi; lưới đi tới dòng 10.004 (gồm 4 dòng thử trước đó), thêm một dòng trống nhập mới |
| Nhập lại file DB đã nhập | Tạo thêm 3 dòng; DB xác nhận 3 nhóm mã đơn trùng, mỗi nhóm 2 dòng |
| Đổi nhãn/lựa chọn cột trên DB test rồi tải lại | File tải mới phản ánh đúng nhãn và dropdown; đã trả cấu hình test về ban đầu |
| Tải mẫu rỗng lên rồi Huỷ | Xem trước 0 dòng, hủy không tăng số bản ghi |

Tệp kiểm thử được điền bằng openpyxl từ chính file tải qua trình duyệt, lưu
ở `storage/template-user-qa/`. Chưa thao tác nhập ô/dropdown trong Microsoft
Excel. Worker chạy eager trong môi trường test: đã kiểm giao diện upload,
preview, confirm, kết quả và dữ liệu, chưa kiểm sự cố worker/Redis thật.

### Phát hiện cần xử lý

1. **Lỗi xem trước sai cột (ưu tiên cao):** `_mau()` sắp giá trị theo tên cột,
   còn tiêu đề theo thứ tự file. Ở file DB, mã đơn nằm dưới Số điện thoại,
   ghi chú nằm dưới Bang. Dữ liệu ghi vào DB đúng; màn hình xác nhận sai.
   Đã có trong HEAD trước tác vụ download.
2. **Mẫu Vận đơn kèm 4 trường không nhận nhập:** các cột Mã Sale tạo đơn,
   Mã nhân viên Vận đơn/CSKH/Marketing được thêm từ `extra_columns` dù là
   `is_computed`. Dùng mẫu của ứng dụng vẫn gặp cảnh báo 4 cột bị bỏ qua.
   Đây là điểm chưa tốt của chức năng mẫu mới, cần loại các cột bổ sung chỉ xuất.
3. **Xem trước chưa kiểm đầy đủ lỗi giá trị:** file có hai dòng chắc chắn sai
   vẫn ghi “3 dòng dữ liệu sẽ được thêm”; lỗi chỉ xuất hiện sau xác nhận.
   Trang tiến độ vẫn ghi Xong/100% dù chỉ nhập 1/3. Đã xác nhận trực tiếp.
4. **Rủi ro nhập trùng:** Vận đơn DB cho nhập lại cùng file/mã đơn thành bản
   ghi mới. Cần quyết định quy tắc phát hiện/xử lý trùng trước khi đổi nghiệp vụ;
   không tự gộp, ghi đè hay xóa dữ liệu.

Không sửa các hành vi trên trong lượt kiểm thử. Đã cập nhật hai assertion cũ
đòi nhãn Sửa trong `crm/tests/test_trang_chu.py` theo yêu cầu bỏ nhãn đã duyệt.
Lần chạy bốn nhóm ban đầu: 27 passed, 1 failed do assertion cũ thứ hai.
Sau cập nhật, chạy riêng `crm/tests/test_trang_chu.py -ra`: **3 passed**.
Các nhóm template/nhập-xuất/thư mục còn lại đã đạt trong lần chạy đó.

Không kết luận toàn luồng sẵn sàng cho người dùng chỉ dựa vào test tự động.

Phạm vi được duyệt: nút **Tải mẫu Excel** trước **Mở** trên ba thẻ Vận đơn,
Vận đơn DB, Vận đơn mới; bỏ nhãn **Sửa**, giữ quyền hiện tại. Chỉ local.

GET `/bang/<code>/mau-nhap.xlsx` kiểm cùng quyền nhập tệp, trả file đính kèm
`mau-nhap-<code>.xlsx`, không lấy bản ghi khách hàng. Mẫu lấy thứ tự/nhãn/kiểu
cột hiện hành và cột bổ sung của chính sách nhập. Sheet nhập trống đứng đầu;
sheet hướng dẫn đứng sau. Dropdown dùng danh sách thật và named range;
cột chọn chưa cấu hình có cảnh báo và chỉ cho để trống. Không thêm lựa chọn
Đã về TK, không nhập bù hoặc thay đổi thứ tự cột trong tác vụ này.

Mẫu của bảng có chính sách chi tiết sản phẩm vẫn cần JSON như luồng nhập
hiện có; ví dụ nằm riêng ở hướng dẫn, không được nhập thành khách hàng.
Mã đơn/điện thoại/Zipcode được định dạng chữ; ngày/tiền định dạng theo kiểu.

## Kiểm chứng

- Red: test tải mẫu trả 404 trước khi có endpoint. Khi kiểm URLconf CRM,
  phát hiện thiếu route riêng và bổ sung trước bàn giao.
- `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest forms_builder/tests/test_import_template.py forms_builder/tests/test_nhap_xuat.py crm/tests/test_thu_muc.py -q --maxfail=2`: exit 0, không skip/lỗi.
- Sau bổ sung ca phân quyền xem/sửa: `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest forms_builder/tests/test_import_template.py -ra`: **5 passed**.
- Tải mẫu của cả ba bảng, điền hai bản ghi rồi prepare/confirm qua worker eager:
  mỗi bảng nhập đủ hai dòng, không lỗi. Database test riêng, không nhập vào local thật.
- Kiểm không có quyền, có quyền xem nhưng không được nhập (403), quyền sửa
  được tải (200), POST bị từ chối (405); người chỉ xem không có nút tải.
- Trình duyệt Codex tại localhost:8021: ba nút đúng bảng, bỏ nhãn Sửa,
  bấm Vận đơn DB phát sinh download. Kiểm desktop và 390×844; nút không tràn
  ngang, trả viewport về mặc định sau kiểm.
- Chưa kiểm tương tác dropdown trực tiếp trong Microsoft Excel; đã đọc lại
  cấu trúc workbook, named range, lựa chọn và định dạng bằng openpyxl.

Không migration, commit, push hoặc cập nhật VPS. Các thay đổi có sẵn về chọn
bảng nhận đơn được giữ nguyên, không thuộc diff chức năng này.
## Cập nhật 15.09.2026 — Sửa theo yêu cầu sau kiểm thử

Chủ dự án đã duyệt sửa các lỗi phát hiện và phản ánh cột trong file tải xuống
bị lệch. Phần này thay thế trạng thái chưa sửa ở các ghi nhận kiểm thử trước đó.

- Xem trước lấy giá trị theo đúng vị trí cột trong tệp; tương thích bản nháp cũ.
- Mẫu chỉ chứa cột nhận nhập, bỏ bốn cột phụ chỉ xuất/tính toán. Danh sách chọn
  lấy từ registry thực tế. Tiêu đề căn trái, xuống dòng, cao 54; cột rộng 20–42,
  ô nhập xuống dòng, căn trên; giữ định dạng chữ cho điện thoại/Zipcode/mã đơn.
  Không đổi thứ tự ColumnDef hay cấu hình cột riêng đã lưu trong trình duyệt.
- Xem trước báo dòng thiếu trường bắt buộc, sai giá trị chọn và mã đơn trùng.
  Mẫu trống bị từ chối; toàn bộ dòng lỗi thì nút xác nhận bị vô hiệu hóa.
- Vận đơn kiểm mã đơn trùng trong cùng bảng và cùng tệp, bỏ khoảng trắng hai
  đầu khi đối chiếu, phân biệt hoa thường. Dòng hợp lệ đầu tiên được nhận;
  không ghi đè/gộp/xóa đơn đã có. Worker kiểm lại dưới khóa bảng trước khi ghi,
  tránh hai lượt nhập đồng thời cùng tạo mã. Không đặt ràng buộc mới lên sửa ô.
- Trang kết quả phân biệt hoàn tất xử lý với nhập toàn bộ thành công.

Kiểm chứng mới: **30 passed in 14.98s**, không skip, bằng lệnh:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest forms_builder/tests/test_import_checks.py forms_builder/tests/test_import_template.py forms_builder/tests/test_nhap_xuat.py crm/tests/test_trang_chu.py -ra --maxfail=2
```

Có test hai worker đồng thời, trùng phát sinh sau preview, sai giá trị, tương
thích preview cũ, round-trip ba mẫu và quyền endpoint. Red trước sửa: 3 lỗi
đúng nguyên nhân, 1 đạt. Sau lần chạy xanh chỉ chỉnh câu hướng dẫn cho trường
hợp không còn dòng hợp lệ (kiểm lại bằng trình duyệt).

Trình duyệt tại 18031 dùng database riêng
`test_template_user_qa_20260915_fix1112`: tải mới cả ba mẫu rồi điền bản sao
bằng openpyxl; nhập mỗi bảng 3/3 đạt. DB hỗn hợp hiển thị 1 hợp lệ/2 lỗi trước
xác nhận, kết quả nhập 1/bỏ 2. Nhập lại 3 dòng: 0 hợp lệ/3 trùng, nút xác nhận
khóa. Tệp 10.000 dòng: preview 10.000 hợp lệ, kết quả 10.000/10.000, không lỗi.
Mẫu chưa điền báo lỗi không có dữ liệu. Tiêu đề và giá trị preview đã đối chiếu
trực tiếp (điện thoại/Zipcode giữ số 0 đầu). Không ghi dữ liệu thử vào DB dev.

Local 8021 dùng runserver tự nạp mã; worker đã khởi động lại sau khi kiểm tra
không có tác vụ đang chạy. Chưa commit/push/VPS. Chưa kiểm trực tiếp hiển thị
và thao tác dropdown trong Microsoft Excel; cấu trúc/định dạng workbook kiểm
bằng openpyxl. Nếu phản ánh “lệch” chỉ một vị trí cụ thể khác với các lỗi trên,
cần đối chiếu vị trí đó; không kết luận đã kiểm mọi cách hiển thị của Excel.
