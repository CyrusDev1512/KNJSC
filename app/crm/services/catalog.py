"""Bảng mà KN CRM phục vụ — ADR-040 (24.09.2026): **chỉ bảng vận đơn**.

Sale và Marketing nhập-xuất đều bên KN ERP (biểu mẫu báo cáo ngày, Báo cáo
tổng hợp, Bảng dữ liệu); KN CRM chỉ còn Bảng tính của Vận đơn. Mọi cửa của
KN CRM — trang chủ, thư mục, lưới, JSON của lưới, nhập tệp, cấp quyền, bảng
đã xoá — lọc qua đây (quy tắc 7). **Dữ liệu các bảng khác không đổi**: chúng
chỉ không hiện và không mở được ở dịch vụ 8021; KN ERP đọc ghi như cũ, trang
Thống kê của CRM vẫn đọc số liệu từ cả hai bên.
"""
from orders.constants import waybill_condition


def chi_van_don(queryset, prefix=""):
    """Thu hẹp một queryset bảng (hoặc dòng, với prefix="table__") về bảng vận đơn."""
    return queryset.filter(waybill_condition(prefix))
