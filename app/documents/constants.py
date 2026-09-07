"""Hằng của module Tài liệu — khai một chỗ (quy tắc 7), ADR-015."""
from core.constants import LINK_SCHEMES, FileKind  # noqa: F401 — LINK_SCHEMES dùng chung với resources

#: Thư mục con trong STORAGE_DIR. Cố ý nằm ngoài `uploads/` và `exports/`,
#: hai chỗ bị `core.don_tep_xuat_qua_han` dọn sau 24 giờ (FR-9.5)
DOCUMENT_SUBDIR = "tai-lieu"

#: Loại tệp thư viện nhận — FR-9.2. Luồng nhập bảng vẫn chỉ Excel và CSV
DOCUMENT_FILE_KINDS = (
    FileKind.PDF, FileKind.DOCX, FileKind.XLSX, FileKind.CSV, FileKind.JPG, FileKind.PNG,
)

TITLE_MAX = 200
DESCRIPTION_MAX = 500
CATEGORY_NAME_MAX = 120
FILE_NAME_MAX = 200

