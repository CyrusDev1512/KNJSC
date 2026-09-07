"""Tác vụ nền của Văn hoá — chạy nền không có nghĩa là chạy âm thầm: mỗi lần
đều ghi nhật ký qua tầng dịch vụ."""
from celery import shared_task


@shared_task(name="culture.thuong_sao_thang")
def thuong_sao_thang():
    """Ngày 1 hằng tháng: thưởng sao cho top 3 doanh số tháng trước — FR-12.4."""
    from .services import leaderboard_service

    return leaderboard_service.award_monthly_stars(leaderboard_service.previous_period())
