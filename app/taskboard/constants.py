"""Hằng của module Công việc — khai một chỗ (quy tắc 7), ADR-015."""
from django.db import models


class TaskStatus(models.TextChoices):
    MOI = "moi", "Mới"
    DANG_LAM = "dang_lam", "Đang làm"
    XONG = "xong", "Xong"
    HUY = "huy", "Huỷ"


class TaskPriority(models.TextChoices):
    THAP = "thap", "Thấp"
    VUA = "vua", "Vừa"
    CAO = "cao", "Cao"


#: Chuyển trạng thái hợp lệ — FR-11.2. Xong quay lại Đang làm được; Huỷ mở lại thành Mới
STATUS_TRANSITIONS = {
    TaskStatus.MOI: (TaskStatus.DANG_LAM, TaskStatus.HUY),
    TaskStatus.DANG_LAM: (TaskStatus.XONG, TaskStatus.HUY, TaskStatus.MOI),
    TaskStatus.XONG: (TaskStatus.DANG_LAM,),
    TaskStatus.HUY: (TaskStatus.MOI,),
}

#: Trạng thái còn mở — dùng để tính quá hạn
OPEN_STATUSES = (TaskStatus.MOI, TaskStatus.DANG_LAM)

#: Lớp chip có sẵn trong main.css
STATUS_CHIP = {
    TaskStatus.MOI: "chip-nhat",
    TaskStatus.DANG_LAM: "chip-nhan",
    TaskStatus.XONG: "chip-tot",
    TaskStatus.HUY: "chip-xau",
}
PRIORITY_CHIP = {
    TaskPriority.THAP: "chip-nhat",
    TaskPriority.VUA: "chip-cho",
    TaskPriority.CAO: "chip-xau",
}

TITLE_MAX = 200

#: Nhãn tiếng Việt khi ghi nhật ký sửa việc
TASK_FIELD_LABELS = {
    "title": "Tiêu đề", "description": "Mô tả", "assignee": "Người làm",
    "priority": "Ưu tiên", "due_date": "Hạn",
}
