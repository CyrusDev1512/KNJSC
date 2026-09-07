"""Tác vụ nền của Văn hoá — chạy nền không có nghĩa là chạy âm thầm: thành
công hay thất bại đều để lại dấu vết (nhật ký, và thư cho người vận hành khi
hỏng)."""
from celery import shared_task


@shared_task(name="culture.thuong_sao_thang")
def thuong_sao_thang():
    """Ngày 1 hằng tháng (và mỗi lần máy bật, qua entrypoint): thưởng sao cho
    top 3 doanh số tháng trước — FR-12.4. Chạy lại không nhân đôi."""
    from core.alerts import bao_nguoi_van_hanh
    from core.audit import record
    from core.constants import AuditAction
    from core.exceptions import BusinessError

    from .services import leaderboard_service

    ky = leaderboard_service.previous_period()
    try:
        return leaderboard_service.award_monthly_stars(ky)
    except BusinessError as loi:
        record(AuditAction.CREATE, target=("star_award", ky), detail=f"Thưởng sao {ky} thất bại: {loi}")
        bao_nguoi_van_hanh("Thưởng sao tháng thất bại", f"Kỳ {ky}: {loi}")
        return 0
