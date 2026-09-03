"""Kiểm thử tệp chuyển đổi cấu trúc.

`CLAUDE.md` mục *Định nghĩa hoàn thành* điều 3 đòi **tệp chuyển đổi cấu trúc
chạy xuôi và ngược đều được**. Trước tệp này, quy tắc đó không có gì bắt buộc —
tôi kiểm bằng tay mỗi lần, và đã một lần chạy nhầm lên cơ sở dữ liệu phát triển
làm mất dữ liệu mẫu.

Ba thứ tệp này bắt:

1. Model và tệp chuyển đổi lệch nhau — ai đó sửa model mà quên sinh tệp
2. Tệp không đảo ngược được — thường là `RunSQL` thiếu `reverse_sql`
3. Hai nhánh lá trong cùng một app — gộp nhánh sinh xung đột

**Chạy chậm** vì phải dựng lại cơ sở dữ liệu nhiều lần, nên đánh dấu `cham`.
Bỏ qua khi cần vòng lặp nhanh bằng `pytest -m "not cham"`.
"""
from io import StringIO

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader

#: App có tệp chuyển đổi của chính dự án. Không đụng tới app của Django.
CAC_APP = ["core", "org", "forms_builder", "reports", "orders", "crm"]


@pytest.mark.django_db
def test_model_va_tep_chuyen_doi_khong_lech():
    """CLAUDE.md quy tắc 4 — Sửa model mà quên sinh tệp chuyển đổi thì đỏ

    Chạy dưới cấu hình kiểm thử, vì app `core.tests` chỉ tồn tại ở đó. Chạy
    dưới cấu hình dev sẽ cho kết quả khác và bỏ sót model thử phạm vi.
    """
    ra = StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=ra, stderr=ra)
    except SystemExit as thoat:
        pytest.fail(
            "Model và tệp chuyển đổi đã lệch nhau. Chạy `makemigrations` rồi "
            f"commit tệp sinh ra.\n{ra.getvalue()}"
        )
    assert "No changes detected" in ra.getvalue() or ra.getvalue().strip() == ""


@pytest.mark.django_db
def test_khong_co_hai_nhanh_la_trong_mot_app():
    """CLAUDE.md quy tắc 5 — Mỗi app chỉ có một nhánh lá, không gộp xung đột"""
    loader = MigrationLoader(connection)
    theo_app = {}
    for ten_app, ten_tep in loader.graph.leaf_nodes():
        theo_app.setdefault(ten_app, []).append(ten_tep)

    nhieu_la = {a: ds for a, ds in theo_app.items() if len(ds) > 1}
    assert not nhieu_la, (
        f"App có nhiều hơn một nhánh lá, phải gộp lại: {nhieu_la}"
    )


@pytest.mark.django_db
def test_moi_app_deu_co_tep_chuyen_doi():
    """Quy tắc 4 — App có model thì phải có tệp chuyển đổi, không để trống"""
    loader = MigrationLoader(connection)
    thieu = []
    for ten in CAC_APP:
        cau_hinh = apps.get_app_config(ten)
        if list(cau_hinh.get_models()) and ten not in loader.migrated_apps:
            thieu.append(ten)
    assert not thieu, f"App có model nhưng chưa có tệp chuyển đổi: {thieu}"


@pytest.mark.cham
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("ten_app", CAC_APP)
def test_chay_nguoc_roi_chay_xuoi_lai_duoc(ten_app):
    """CLAUDE.md Định nghĩa hoàn thành điều 3 — Chạy xuôi và ngược đều được

    Chỗ hay gãy nhất là `RunSQL` thiếu `reverse_sql`, và phần mở rộng
    PostgreSQL như `pg_trgm`. Bỏ `reverse_sql` của `core/0002_pg_trgm.py` là
    bài này phải đỏ.

    Chỉ chạy trên cơ sở dữ liệu **kiểm thử** — pytest-django dựng riêng
    `test_knjsc_db`, không đụng tới dữ liệu phát triển.
    """
    im = StringIO()
    try:
        call_command("migrate", ten_app, "zero", verbosity=0, stdout=im, stderr=im)
    except Exception as loi:
        pytest.fail(
            f"App {ten_app} không chạy ngược được: {loi}\n"
            "Thường là RunSQL thiếu reverse_sql, hoặc RunPython thiếu hàm đảo."
        )
    finally:
        # Dựng lại dù bài đỗ hay hỏng, để bài sau không chạy trên lược đồ trống
        call_command("migrate", ten_app, verbosity=0, stdout=im, stderr=im)

    # Sau khi chạy lại, bảng phải có mặt trở lại
    cau_hinh = apps.get_app_config(ten_app)
    with connection.cursor() as con:
        for model in cau_hinh.get_models():
            bang = model._meta.db_table
            con.execute("SELECT to_regclass(%s)", [bang])
            assert con.fetchone()[0] is not None, (
                f"Chạy xuôi lại rồi mà bảng {bang} vẫn chưa có"
            )
