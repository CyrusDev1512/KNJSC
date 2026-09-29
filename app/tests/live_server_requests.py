"""Máy chủ thử (`live_server`) phải xử lý xong mọi yêu cầu rồi pytest mới dọn bảng — TL-67.

Bài trình duyệt kết thúc ngay sau một thao tác làm trang gọi máy chủ (lưới tải lại dữ liệu, poll lịch
sử ô) thì luồng máy chủ thử còn đang truy vấn đúng lúc pytest-django dọn bảng bằng TRUNCATE. Hai bên
chờ khoá của nhau, Postgres huỷ lệnh dọn và bài báo lỗi lúc dọn — đỏ chập chờn ở CI #94, #96.

`LIVE_SERVER_REQUESTS` đếm yêu cầu máy chủ thử đang xử lý dở qua hai tín hiệu của Django; fixture tự
chạy `_live_server_idle_before_flush` ở `conftest.py` gốc chờ số đó về 0 rồi mới để pytest dọn bảng.
"""
import threading
import time

from django.core.handlers.wsgi import WSGIHandler
from django.core.signals import request_finished, request_started


class LiveServerRequests:
    """Đếm yêu cầu máy chủ thử đang xử lý dở.

    Chỉ tính yêu cầu đi qua `WSGIHandler`, tức máy chủ thử chạy ở luồng riêng. Yêu cầu của test client
    (`ClientHandler`) chạy ngay trong luồng bài kiểm nên xong trước khi bài xong, lại có khi không phát
    `request_finished` (phản hồi luồng không ai đọc hết) — tính vào thì bộ đếm treo ở số dương.
    """

    def __init__(self):
        self._condition = threading.Condition()
        self.in_flight = 0
        self.started_total = 0

    @staticmethod
    def _from_server(sender):
        return isinstance(sender, type) and issubclass(sender, WSGIHandler)

    def on_started(self, sender, **kwargs):
        if self._from_server(sender):
            with self._condition:
                self.in_flight += 1
                self.started_total += 1
                self._condition.notify_all()

    def on_finished(self, sender, **kwargs):
        if self._from_server(sender):
            with self._condition:
                self.in_flight = max(0, self.in_flight - 1)
                self._condition.notify_all()

    def wait_idle(self, quiet=0.2, timeout=5.0):
        """Chờ tới khi máy chủ không xử lý yêu cầu nào suốt `quiet` giây liền — khoảng đó để yêu cầu
        trình duyệt gửi trước khi đóng tab kịp tới máy chủ; quá `timeout` giây thì thôi, không treo.
        Trả True khi đã yên."""
        deadline = time.monotonic() + timeout
        with self._condition:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return self.in_flight == 0
                if self.in_flight:
                    self._condition.wait(remaining)
                    continue
                mark = self.started_total
                self._condition.wait(min(quiet, remaining))
                if not self.in_flight and self.started_total == mark:
                    return True


LIVE_SERVER_REQUESTS = LiveServerRequests()
request_started.connect(LIVE_SERVER_REQUESTS.on_started, weak=False)
request_finished.connect(LIVE_SERVER_REQUESTS.on_finished, weak=False)
