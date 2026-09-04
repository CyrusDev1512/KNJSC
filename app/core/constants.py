"""Các giá trị cố định của toàn hệ thống.

Khai báo ở một chỗ duy nhất, không viết rải rác (quy tắc 7).
"""
from django.db import models


class Rank(models.TextChoices):
    """Cấp bậc — quyết định phạm vi rộng bao nhiêu (ADR-003)."""

    STAFF = "staff", "Nhân viên"
    LEADER = "leader", "Trưởng nhóm"
    MANAGER = "manager", "Quản lý"
    ADMIN = "admin", "Quản trị viên"


# Thứ bậc để so sánh. Không dùng thứ tự chữ cái vì nó sai.
RANK_LEVEL = {
    Rank.STAFF: 10,
    Rank.LEADER: 20,
    Rank.MANAGER: 30,
    Rank.ADMIN: 40,
}


def rank_level(rank):
    """Trả về mức của một cấp bậc. Cấp bậc lạ coi như thấp nhất."""
    return RANK_LEVEL.get(rank, 0)


class Currency(models.TextChoices):
    """Loại tiền tệ dùng trong phase 1.

    Bán xuyên biên giới nên vừa có doanh số bằng USD vừa có chi phí bằng VND.
    Mỗi số tiền phải đi kèm loại tiền của nó, không quy đổi khi lưu.
    """

    VND = "VND", "Việt Nam đồng"
    USD = "USD", "Đô la Mỹ"
    # Hai thị trường còn lại — tệp vận đơn thật ghi "Giá tiền(CAD)" (Q41)
    CAD = "CAD", "Đô la Canada"
    PHP = "PHP", "Peso Philippines"


# Số chữ số thập phân theo tập quán từng loại tiền, dùng khi hiển thị
CURRENCY_DECIMALS = {Currency.VND: 0, Currency.USD: 2}
CURRENCY_SYMBOL = {Currency.VND: "₫", Currency.USD: "$"}


class AuditAction(models.TextChoices):
    """Các loại hành động được ghi vào nhật ký (BR-6)."""

    LOGIN = "login", "Đăng nhập"
    LOGIN_FAILED = "login_failed", "Đăng nhập thất bại"
    LOGOUT = "logout", "Đăng xuất"
    CREATE = "create", "Tạo"
    UPDATE = "update", "Sửa"
    DELETE = "delete", "Xoá"
    EXPORT = "export", "Xuất dữ liệu"
    IMPORT = "import", "Nhập dữ liệu"
    PERMISSION = "permission", "Đổi quyền"
    DENIED = "denied", "Từ chối truy cập"
    BACKUP = "backup", "Sao lưu"


# ══ NHẬP XUẤT TỆP VÀ TÁC VỤ NỀN — Giai đoạn 7 ══════════════════════
#
# Con số lấy từ docs/02 mục 10 (NFR-11 tới NFR-16) và docs/03 mục 6.3, 8, 9.
# Khai ở đây một chỗ; settings chỉ đọc lại, không viết cứng lần hai.

UPLOAD_MAX_BYTES = 10 * 1024 * 1024     # NFR-11 — 10 MB mỗi tệp tải lên
IMPORT_MAX_ROWS = 5_000                  # NFR-13 — trần cứng mỗi lần nhập
IMPORT_PERF_ROWS = 2_000                 # NFR-3  — mốc đo: 2.000 dòng dưới 60 giây
IMPORT_PERF_SECONDS = 60
EXPORT_SYNC_MAX_ROWS = 2_000             # trên mức này thì xuất chạy nền
EXPORT_FILE_TTL_HOURS = 24               # NFR-16 — tệp xuất giữ 24 giờ
BACKUP_KEEP = 30                         # NFR-15 — giữ tối đa 30 bản sao lưu
JOB_STALE_MINUTES = 15                   # chờ quá lâu nghĩa là worker không chạy
IMPORT_ERROR_LIST_MAX = 200              # số dòng lỗi lưu chi tiết vào tác vụ
HEADER_SCAN_ROWS = 10                    # dò hàng tiêu đề trong bấy nhiêu hàng đầu
GRID_PAGE_SIZE = 100                     # Bảng tính vận đơn — dòng mỗi trang
GRID_FROZEN_COLUMNS = 4
GRID_FILTER_OPTIONS_MAX = 200            # số giá trị tối đa trong hộp lọc một cột
GRID_FROZEN_COLUMNS_GENERIC = 1          # bảng thường: cố định một cột đầu — ADR-010
GRID_FROZEN_WIDTH_DEFAULT = 160          # ... rộng bấy nhiêu px
GRID_SPARE_ROWS = 5                      # dòng trống cuối lưới để gõ bản ghi mới
GRID_FORMAT_CELLS_MAX = 500              # số ô tối đa định dạng trong một lần
GRID_MIN_COLUMNS = 26                    # lưới luôn có chữ cột tới Z, thiếu thì thêm cột trống — ADR-011
GRID_FILLER_COLUMNS = 2                  # ... và ít nhất hai cột trống sau cột cuối
GRID_ROW_NUMBER_WIDTH = 46               # cột số dòng bên trái (px)
GRID_SPARE_ROWS_MAX = 2000               # "+100 dòng" không vượt quá bấy nhiêu dòng trống
GRID_PASTE_CELLS_MAX = 2000              # số ô tối đa lưu trong một lần dán / kéo điền / hoàn tác
PERF_TABLE_ROWS = 50_000                 # AC-7.1 — 50.000 bản ghi tải trang đầu
PERF_PAGE_SECONDS = 2                    # ... dưới 2 giây


class FileKind(models.TextChoices):
    """Loại tệp được phép tải lên — NFR-12. Kiểm bằng đầu tệp, không tin đuôi (S7)."""

    XLSX = "xlsx", "Excel"
    CSV = "csv", "CSV"
    JPG = "jpg", "Ảnh JPG"
    PNG = "png", "Ảnh PNG"


#: Chữ ký đầu tệp. CSV không có chữ ký — nhận khi đọc được dạng chữ và không
#: chứa byte 0 (xem `core.excel.sniff_kind`).
FILE_MAGIC = {
    FileKind.XLSX: (b"PK\x03\x04",),
    FileKind.JPG: (b"\xff\xd8\xff",),
    FileKind.PNG: (b"\x89PNG\r\n\x1a\n",),
}

#: Đuôi tệp ứng với mỗi loại, để đối chiếu đuôi khai báo với loại thật.
FILE_EXTENSIONS = {
    FileKind.XLSX: (".xlsx",),
    FileKind.CSV: (".csv",),
    FileKind.JPG: (".jpg", ".jpeg"),
    FileKind.PNG: (".png",),
}

#: Loại tệp nhận được ở luồng nhập dữ liệu vào bảng
IMPORT_FILE_KINDS = (FileKind.XLSX, FileKind.CSV)


class JobKind(models.TextChoices):
    """Loại tác vụ nền."""

    IMPORT = "import", "Nhập tệp"
    EXPORT = "export", "Xuất tệp"
    BACKUP = "backup", "Sao lưu"
    CLEANUP = "cleanup", "Dọn dẹp"


class JobStatus(models.TextChoices):
    """Vòng đời một tác vụ nền.

    DRAFT là bước xem trước của luồng nhập — người dùng chưa xác nhận nên chưa
    có gì được ghi. STALE nghĩa là chờ quá lâu mà không ai nhận: worker chết,
    và hệ thống phải nói ra chứ không im lặng (kien-truc.md).
    """

    DRAFT = "draft", "Chờ xác nhận"
    PENDING = "pending", "Chờ xử lý"
    RUNNING = "running", "Đang chạy"
    DONE = "done", "Xong"
    FAILED = "failed", "Thất bại"
    STALE = "stale", "Kẹt — worker không chạy"


#: Trạng thái đã kết thúc — trang tiến độ ngừng hỏi lại khi gặp một trong số này
JOB_FINISHED = (JobStatus.DONE, JobStatus.FAILED, JobStatus.STALE)
