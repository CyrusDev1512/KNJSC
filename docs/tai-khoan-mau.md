# Tài khoản mẫu để đăng nhập thử

Ghi chú nhanh cho máy phát triển. Toàn bộ tài khoản dưới đây do lệnh
`du_lieu_mau` tạo ra, **chỉ dùng trên máy cá nhân**, không phải tài khoản thật.

| | |
|---|---|
| Địa chỉ | `http://127.0.0.1:8020/` |
| Mật khẩu chung | `MatKhauTam-2026` |
| Trang quản trị Django | `http://127.0.0.1:8020/quan-tri/` — chỉ `quantri` vào được |

---

## Tài khoản quản trị

| Tên đăng nhập | Mật khẩu | Vai trò |
|---|---|---|
| `quantri` | `MatKhauTam-2026` | Admin — thấy và sửa được mọi bộ phận, vào được trang quản trị Django |

---

## Bộ phận Sale

| Tên đăng nhập | Mật khẩu | Cấp bậc | Team | Họ tên |
|---|---|---|---|---|
| `sale.manager` | `MatKhauTam-2026` | Manager | — | Lê Quốc Bảo |
| `sale.leader` | `MatKhauTam-2026` | Leader | Sale 1 (trưởng nhóm) | Trần Văn Dũng |
| `sale.leader2` | `MatKhauTam-2026` | Leader | Sale 2 (trưởng nhóm) | Phạm Quốc Anh |
| `sale.staff` | `MatKhauTam-2026` | Staff | Sale 1 | Nguyễn Thị Hà |
| `sale.staff2` | `MatKhauTam-2026` | Staff | Sale 2 | Lý Thu Hằng |
| `sale.moi` | `MatKhauTam-2026` | Staff | — | Nhân viên mới — **bị buộc đổi mật khẩu ngay lần đầu đăng nhập**, cố ý để thử luồng đó |

## Bộ phận Marketing

| Tên đăng nhập | Mật khẩu | Cấp bậc | Họ tên |
|---|---|---|---|
| `mkt.manager` | `MatKhauTam-2026` | Manager | Đỗ Thu Trang |
| `mkt.leader` | `MatKhauTam-2026` | Leader | Vũ Hoài Nam |
| `mkt.staff` | `MatKhauTam-2026` | Staff | Phạm Minh Anh |

## Bộ phận Vận đơn

| Tên đăng nhập | Mật khẩu | Cấp bậc | Họ tên |
|---|---|---|---|
| `vd.manager` | `MatKhauTam-2026` | Manager | Bùi Kim Chi |
| `vd.staff` | `MatKhauTam-2026` | Staff | Hoàng Văn Tú |

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

---

## Nếu chưa có tài khoản nào

Cơ sở dữ liệu không theo kho mã, máy mới dựng xong là trống. Chạy một trong
hai cách:

```
scripts\bat.cmd                       Windows — tự làm hết
sh scripts/bat.sh                     Mac, Linux — tự làm hết
```

hoặc chỉ nạp tài khoản khi container đã chạy:

```
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau
```

Chạy lại nhiều lần được, tài khoản đã có thì giữ nguyên. Muốn mật khẩu khác
thì thêm `--mat-khau <mật khẩu>` — chỉ áp cho tài khoản tạo mới trong lần chạy
đó, tài khoản đã có không đổi.

Đổi mật khẩu cho tài khoản của mình ở `http://127.0.0.1:8020/doi-mat-khau/`.

---

## Không được làm

- **Không chạy `du_lieu_mau` trên máy chủ thật.** Lệnh tự chặn khi `DEBUG` tắt,
  và cờ `--dong-y-chay-that` chỉ dành cho người biết chắc mình làm gì.
- Mật khẩu này nằm công khai trong mã nguồn. Tài khoản thật phải tạo qua màn
  hình Nhân sự với mật khẩu riêng.
