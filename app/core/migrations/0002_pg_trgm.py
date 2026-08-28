"""Bật phần mở rộng pg_trgm để tìm kiếm bằng __icontains có chỉ mục.

Tách thành tệp riêng để chạy trước mọi chỉ mục GIN dùng `gin_trgm_ops`.
Đảo ngược được: gỡ phần mở rộng.
"""
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("core", "0001_initial")]

    operations = [TrigramExtension()]
