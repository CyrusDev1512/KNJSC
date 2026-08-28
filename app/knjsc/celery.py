"""Cấu hình tác vụ nền.

Tác vụ nền gọi cùng tầng dịch vụ với giao diện web — không viết logic hai lần.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "knjsc.settings.dev")

app = Celery("knjsc")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
