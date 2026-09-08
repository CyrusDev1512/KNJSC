"""Tác vụ nền của Bảng tin — cùng hàm với lệnh `thiep_sinh_nhat`, với
`entrypoint.sh` lúc máy bật và với `du_lieu_mau`, không viết logic hai lần."""
from celery import shared_task


@shared_task(name="feed.thiep_sinh_nhat")
def thiep_sinh_nhat():
    """06:00 hằng ngày: đăng thiệp cho người có sinh nhật hôm nay, bù cả những
    ngày máy tắt — FR-10.4."""
    from .services import post_service

    return post_service.catch_up_birthday_posts()
