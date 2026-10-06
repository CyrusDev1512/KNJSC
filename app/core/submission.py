"""Chạy một việc ghi đúng một lần cho mỗi lần nộp form — AC-4.12, AC-6.11.

Dùng ở tầng dịch vụ (`daily_service.submit_current`, `order_service.create_order_once`), không ở view (quy tắc 2).
"""
import uuid

from django.db import IntegrityError, transaction

from .exceptions import BusinessError
from .models import SubmissionReceipt


def new_key():
    """Mã lần nộp cho một lần mở form."""
    return str(uuid.uuid4())


def parse_key(raw):
    """Mã hợp lệ thì trả UUID, không có hay hỏng thì None — form mở từ trước bản sửa vẫn nộp được như cũ."""
    try:
        return uuid.UUID(str(raw or "").strip())
    except ValueError:
        return None


def run_once(actor, key, kind, create, load):
    """Gọi `create()` một lần cho mỗi (người, mã). Trả `(đối tượng, mới_tạo)`.

    Lần gửi lặp trả `(load(id đã ghi), False)`. Hai yêu cầu cùng lúc: yêu cầu sau chờ ở ràng buộc duy nhất tới khi
    yêu cầu trước commit rồi đọc lại biên nhận. `create()` lỗi thì cả biên nhận lẫn dữ liệu cùng quay lui — sửa rồi nộp
    lại với cùng mã vẫn được.
    """
    key = parse_key(key)
    if key is None:
        return create(), True
    with transaction.atomic():
        try:
            with transaction.atomic():
                receipt = SubmissionReceipt.objects.create(actor=actor, key=key, kind=kind)
        except IntegrityError:
            cu = SubmissionReceipt.objects.filter(actor=actor, key=key).first()
            if cu is None or cu.kind != kind or cu.object_id is None:
                raise BusinessError("Lần nộp này đã được xử lý. Tải lại trang rồi làm lại.") from None
            return load(cu.object_id), False
        obj = create()
        receipt.object_id = obj.pk
        receipt.save(update_fields=["object_id"])
        return obj, True
