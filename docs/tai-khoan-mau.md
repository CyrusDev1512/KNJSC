# Tài khoản mẫu để đăng nhập thử

Ghi chú nhanh cho máy phát triển. Toàn bộ tài khoản dưới đây do lệnh
`du_lieu_mau` tạo ra, **chỉ dùng trên máy cá nhân**, không phải tài khoản thật.

| | |
|---|---|
| Địa chỉ | `http://127.0.0.1:8020/` |
| Mật khẩu chung | `matkhaucuatoi` |
| Trang quản trị Django | `http://127.0.0.1:8020/quan-tri/` — chỉ `quantri` vào được |

---

## Tài khoản quản trị

| Tên đăng nhập | Mật khẩu | Vai trò |
|---|---|---|
| `quantri` | `matkhaucuatoi` | Admin — thấy và sửa được mọi bộ phận, vào được trang quản trị Django |

---

## Bộ phận Sale

| Tên đăng nhập | Mật khẩu | Cấp bậc | Team | Họ tên |
|---|---|---|---|---|
| `sale.manager` | `matkhaucuatoi` | Manager | — | Lê Quốc Bảo |
| `sale.leader` | `matkhaucuatoi` | Leader | Sale 1 (trưởng nhóm) | Trần Văn Dũng |
| `sale.leader2` | `matkhaucuatoi` | Leader | Sale 2 (trưởng nhóm) | Phạm Quốc Anh |
| `sale.staff` | `matkhaucuatoi` | Staff | Sale 1 | Nguyễn Thị Hà |
| `sale.staff2` | `matkhaucuatoi` | Staff | Sale 2 | Lý Thu Hằng |
| `sale.moi` | `matkhaucuatoi` | Staff | — | Nhân viên mới — **bị buộc đổi mật khẩu ngay lần đầu đăng nhập**, cố ý để thử luồng đó |

## Bộ phận Marketing

| Tên đăng nhập | Mật khẩu | Cấp bậc | Họ tên |
|---|---|---|---|
| `mkt.manager` | `matkhaucuatoi` | Manager | Đỗ Thu Trang |
| `mkt.leader` | `matkhaucuatoi` | Leader | Vũ Hoài Nam |
| `mkt.staff` | `matkhaucuatoi` | Staff | Phạm Minh Anh |

## Bộ phận Vận đơn

| Tên đăng nhập | Mật khẩu | Cấp bậc | Họ tên |
|---|---|---|---|
| `vd.manager` | `matkhaucuatoi` | Manager | Bùi Kim Chi |
| `vd.staff` | `matkhaucuatoi` | Staff | Hoàng Văn Tú |

---

## Mỗi cấp bậc thấy gì

| Cấp bậc | Phạm vi dữ liệu |
|---|---|
| Staff | Chỉ bản ghi do chính mình tạo |
| Leader | Toàn bộ team mình phụ trách |
| Manager | Toàn bộ bộ phận |
| Admin | Mọi bộ phận, cộng trang quản trị Django |

Muốn thử phân quyền thì đăng nhập `sale.staff` và `sale.staff2`: hai người
khác team, không thấy báo cáo của nhau. `sale.leader` thấy cả `sale.staff`
nhưng không thấy `sale.staff2`.

Nhóm **Nội bộ** (Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên — ADR-017)
mọi cấp bậc đều vào; Manager trở lên mới ghim bài, tải tài liệu, thêm mục,
thêm tài nguyên. Ghi nhận văn hoá đi từ trên xuống (Q75): `sale.leader` ghi
nhận được `sale.staff`, `mkt.manager` ghi nhận được `mkt.leader` và `mkt.staff`,
`quantri` ghi nhận được mọi người; `sale.staff` không có ô ghi nhận. Dữ liệu mẫu đặt **ngày sinh** cho vài tài khoản để Bảng tin
có thiệp ngay: `sale.staff` đúng ngày chạy lệnh (thiệp hiện hôm đó),
`sale.staff2` 20.11, `sale.leader` 08.03, `mkt.staff` 14.07, `mkt.manager`
25.12, `vd.staff` 02.05. Sửa ngày sinh ở Nhân sự → Sửa hồ sơ.

---

## Nếu chưa có tài khoản nào

Cơ sở dữ liệu không theo kho mã, máy mới dựng xong là trống. Chạy một trong
hai cách:

```
KN JSC.bat                          Windows — thư mục gốc, nháy đúp; máy sạch thì tự nạp tài khoản
scripts\cap-nhat-local.bat          Windows — làm hết cho chắc: dựng lại, migrate, nạp
./scripts/cap-nhat-local.sh         Mac, Linux — tự làm hết
```

hoặc chỉ nạp tài khoản khi container đã chạy:

```
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau
```

Chạy lại không tạo trùng, nhưng **đặt lại mật khẩu và mở khoá tài khoản mẫu đã có**.
Thêm `--mat-khau <mật khẩu>` để chọn mật khẩu cho cả tài khoản mẫu mới lẫn đã có.
Lệnh này còn nạp dữ liệu mẫu; không dùng chỉ để đồng bộ mật khẩu khi mở ứng dụng.

## Mật khẩu giữa hai máy và khi mở KN JSC

Mật khẩu đăng nhập được băm trong PostgreSQL, lưu trong Docker volume `db_data`,
không nằm trong localStorage và không được push lên GitHub. KNERP và KN CRM trên
cùng máy dùng chung database; hai máy chạy Docker riêng có database riêng.

Sau khi cập nhật nhánh có thay đổi này, mở `KN JSC.bat` như bình thường: launcher
kéo code của nhánh đang đứng, khởi động hệ thống rồi gọi `cap_nhat_mat_khau_mau`.
Lệnh đổi 12 tài khoản mẫu đã có sang mật khẩu chung ở trên **một lần trên mỗi
database**, đánh dấu riêng từng tài khoản trong audit. Máy mới nhận mật khẩu này
khi tạo dữ liệu mẫu. Không tạo tài khoản còn thiếu hoặc nạp đơn/báo cáo bằng bước
cập nhật mật khẩu; không đổi quyền hoặc cờ buộc đổi mật khẩu của tài khoản.

Các lần mở sau không đặt lại mật khẩu người dùng đã đổi và không làm mất phiên
đăng nhập lần nữa. Lần cập nhật đầu làm phiên cũ hết hiệu lực; đăng nhập lại bằng
mật khẩu mới. `sale.moi` vẫn phải đổi mật khẩu ở lần đăng nhập đầu tiên.
Khi `DEBUG` tắt, bước tự cập nhật này bỏ qua.

Máy khác phải kéo được code mới của đúng nhánh; push riêng lẻ chưa đổi database
máy đó. Nếu launcher báo không kéo được mã mới, cần xử lý lỗi Git rồi mở lại.
Muốn chỉ chạy bước cập nhật một lần khi container đã sẵn sàng:

```powershell
docker compose -f deploy/docker-compose.yml exec web python manage.py cap_nhat_mat_khau_mau
```

Đổi mật khẩu cho tài khoản của mình ở `http://127.0.0.1:8020/doi-mat-khau/`.

---

## Không được làm

- **Không chạy `du_lieu_mau` trên máy chủ thật.** Lệnh tự chặn khi `DEBUG` tắt,
  và cờ `--dong-y-chay-that` chỉ dành cho người biết chắc mình làm gì.
- Mật khẩu này nằm công khai trong mã nguồn. Tài khoản thật phải tạo qua màn
  hình Nhân sự với mật khẩu riêng.
