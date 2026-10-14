"""Quét POST mọi đường của hai dịch vụ với Giám đốc và Kế toán — P0-2 (TL-91).

AC-3.7: gọi thẳng đường dẫn vẫn bị kiểm quyền. FR-3.5 (docstring `core.audit.record_denied`): mỗi lần từ chối có một
dòng Từ chối trong Nhật ký. AC-44.6: Giám đốc đọc toàn công ty nhưng không ghi nghiệp vụ. ADR-038: Kế toán xem và sửa
báo cáo, không làm gì khác.

Mỗi đường của hai bộ định tuyến (trừ `/quan-tri/`) nằm ở **đúng một** trong ba nhóm `BO_QUA`, `CHI_DOC`, `GHI`.
Đường mới mọc ra mà chưa xếp thì bài đỏ — endpoint ghi quên chặn không lọt qua lặng lẽ như với bài khói chỉ gọi GET.

Bốn vai bị cấm: Giám đốc không bộ phận, Giám đốc gắn Sale, Giám đốc gắn Vận đơn (ADR-044) và Staff Kế toán. Với mỗi
đường GHI và mỗi vai bị cấm: POST payload hợp lệ → 403, thêm đúng vai đó đúng một dòng Từ chối, cơ sở dữ liệu và
thư mục tệp không đổi. Mã khác 403 chỉ chấp nhận khi ghi lý do ở `Duong.ma`. Bài hiệu chuẩn gửi cùng payload bằng một
vai được phép và thấy cơ sở dữ liệu đổi: 403 ở trên là do cổng quyền, không phải do payload sai.
"""
import io
import uuid
from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import Client, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from core.constants import AuditAction, Rank
from core.models import AuditLog
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_bao_cao_ngay import _nop, bm_sale  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401

pytestmark = pytest.mark.django_db
# Bốn bài quét chạy khoảng 3 phút (mỗi đường một thế giới dữ liệu, mỗi vai một savepoint) nên mang dấu `cham`; CI vẫn chạy.
# Bài xếp loại đường thì nhanh, không mang dấu, để lệnh hằng ngày `-m "not cham"` vẫn bắt đường mới chưa xếp loại.

ERP, CRM = "knjsc.urls", "knjsc.urls_bangtinh"
#: Bốn vai không được ghi nghiệp vụ
CAM = ("ceo", "ceo_sale", "ceo_vd", "staff_kt")
CEO = ("ceo", "ceo_sale", "ceo_vd")


@dataclass(frozen=True)
class Duong:
    """Một đường cần gửi POST. Hàm nhận thế giới dữ liệu `w` và trả tham số đường dẫn hay payload."""

    kwargs: object = None
    payload: object = None
    json: bool = False
    #: Vai bị cấm ở đường này
    cam: tuple = CAM
    #: Mã khác 403 cho từng vai, kèm lý do: {vai: (mã, lý do)}
    ma: dict = field(default_factory=dict)
    #: Vai được phép dùng để hiệu chuẩn payload; None thì `khong_hieu_chuan` ghi lý do
    hc: str = "admin"
    khong_hieu_chuan: str = ""
    #: Tham số đường dẫn riêng cho lần hiệu chuẩn (đối tượng vai được phép đụng tới khác vai bị cấm)
    hc_kwargs: object = None
    #: Vai nhận 404 trên đối tượng chính nó THẤY được (không phải "không lộ có tồn tại"): vẫn phải có đúng một dòng Từ chối
    nhat_ky_404: tuple = ()


def _k(**gia_tri):
    return lambda w: {ten: (ham(w) if callable(ham) else ham) for ten, ham in gia_tri.items()}


#: Đường không gửi POST trong bài này, kèm lý do. Không phải chỗ giấu đường ghi.
BO_QUA = {
    (ERP, "dang_nhap"): "trang công khai, có bài riêng ở test_shared_login.py",
    (CRM, "dang_nhap"): "trang công khai, có bài riêng ở test_shared_login.py",
    (ERP, "dang_xuat"): "làm mất phiên của chính bài; có bài riêng ở test_account.py",
    (CRM, "dang_xuat"): "làm mất phiên của chính bài; có bài riêng ở test_account.py",
    (ERP, "doi_mat_khau"): "mọi vai đổi mật khẩu của chính mình (ADR-044), có bài riêng",
    (CRM, "doi_mat_khau"): "mọi vai đổi mật khẩu của chính mình (ADR-044), có bài riêng",
    (CRM, "bang_tinh"): "mẫu bị che bởi tong_quan: cùng đường /, reverse ra / rồi resolve về tong_quan",
}

#: Đường chỉ đọc: POST không được ghi gì, không nổ 500, 403 thì phải có dòng Từ chối.
CHI_DOC = {
    # ── KN ERP
    (ERP, "nhat_ky"): Duong(), (ERP, "ma_tran_quyen"): Duong(), (ERP, "tac_vu"): Duong(),
    (ERP, "tac_vu_xem"): Duong(_k(pk=lambda w: w.job.pk)),
    (ERP, "tac_vu_tien_do"): Duong(_k(pk=lambda w: w.job.pk)),
    (ERP, "tac_vu_tai"): Duong(_k(pk=lambda w: w.job.pk)),
    (ERP, "nhan_su"): Duong(), (ERP, "nhan_su_goi_y_ma"): Duong(), (ERP, "tong_quan"): Duong(),
    (ERP, "bang"): Duong(), (ERP, "bang_xem"): Duong(_k(code=lambda w: w.bang.code)),
    (ERP, "bang_mau_nhap"): Duong(_k(code=lambda w: w.bang.code)),
    (ERP, "bang_nhap_xem_truoc"): Duong(_k(code=lambda w: w.bang.code, pk=lambda w: w.nhap.pk)),
    (ERP, "bang_xuat"): Duong(_k(code=lambda w: w.bang.code)),
    (ERP, "bieu_mau"): Duong(),
    (ERP, "bao_cao_hoat_dong"): Duong(), (ERP, "bao_cao_hoat_dong_xuat"): Duong(),
    (ERP, "bao_cao_lich_su"): Duong(), (ERP, "bao_cao_da_bo"): Duong(),
    (ERP, "bao_cao_tong_hop"): Duong(), (ERP, "bao_cao_tong_hop_xuat"): Duong(),
    (ERP, "bao_cao_xem"): Duong(_k(pk=lambda w: w.bao_cao.pk)),
    # Sáu đường Lên đơn cũ của ERP chỉ chuyển tiếp sang KN CRM (ADR-023)
    (ERP, "len_don"): Duong(), (ERP, "kiem_khach"): Duong(), (ERP, "san_pham_moi"): Duong(),
    (ERP, "don_hang"): Duong(), (ERP, "don_xem"): Duong(_k(code=lambda w: w.don.code)),
    (ERP, "don_bo"): Duong(_k(code=lambda w: w.don.code)),
    (ERP, "bang_tin"): Duong(), (ERP, "bang_tin_xem"): Duong(_k(pk=lambda w: w.bai.pk)),
    (ERP, "tai_lieu"): Duong(), (ERP, "tai_lieu_tai"): Duong(_k(pk=lambda w: w.tai_lieu.pk)),
    (ERP, "cong_viec"): Duong(), (ERP, "cong_viec_xem"): Duong(_k(pk=lambda w: w.viec.pk)),
    (ERP, "van_hoa"): Duong(), (ERP, "van_hoa_thanh_vien"): Duong(_k(pk=lambda w: w.nd["staff_sale_1"].pk)),
    (ERP, "tai_nguyen"): Duong(),
    # ── KN CRM
    (CRM, "tong_quan"): Duong(), (CRM, "bang"): Duong(), (CRM, "bang_xem"): Duong(_k(code="van_don")),
    (CRM, "bang_mau_nhap"): Duong(_k(code="van_don")),
    (CRM, "bang_nhap_xem_truoc"): Duong(_k(code="van_don", pk=lambda w: w.nhap.pk)),
    (CRM, "nhat_ky"): Duong(), (CRM, "ma_tran_quyen"): Duong(), (CRM, "tac_vu"): Duong(),
    (CRM, "tac_vu_xem"): Duong(_k(pk=lambda w: w.job.pk)),
    (CRM, "tac_vu_tien_do"): Duong(_k(pk=lambda w: w.job.pk)),
    (CRM, "tac_vu_tai"): Duong(_k(pk=lambda w: w.job.pk)),
    (CRM, "deleted_tables"): Duong(),
    # Chứng từ thanh toán: cờ PAYMENT_DOCUMENTS_ENABLED tắt nên 404; khi bật có bài khoá riêng (P0-10)
    (CRM, "payment_library"): Duong(), (CRM, "payment_rows"): Duong(),
    (CRM, "payment_detail"): Duong(_k(pk=1)), (CRM, "payment_image"): Duong(_k(pk=1)),
    # Tóm tắt lên đơn chỉ tính, không ghi (CEO gắn Sale gọi được — ORD-05, chờ chốt)
    (CRM, "waybill_preview"): Duong(payload=lambda w: w.don_moi),
    (CRM, "don_xem"): Duong(_k(code=lambda w: w.don.code)), (CRM, "kiem_khach"): Duong(),
    (CRM, "crm_statistics"): Duong(), (CRM, "waybill_statistics"): Duong(),
    # KN OMS: bản demo dữ liệu giả, chỉ Admin, chỉ nhận GET (ADR-051) — POST là 405, không ghi gì
    (CRM, "kn_oms"): Duong(),
    (CRM, "master_data"): Duong(_k(code="van_don")), (CRM, "master_history"): Duong(_k(code="van_don")),
    (CRM, "master_scope"): Duong(_k(code="van_don"), lambda w: {"ids": [r.pk for r in w.dong]}, json=True),
    (CRM, "master_sync"): Duong(_k(code="van_don"), lambda w: {}, json=True),
    (CRM, "thu_muc"): Duong(),
    # Trang chọn bảng của Nhập tệp và Cấp quyền: POST xử lý như GET, chỉ liệt kê
    (CRM, "nhap_tep"): Duong(), (CRM, "cap_quyen"): Duong(),
    (CRM, "bang_tinh_mac_dinh"): Duong(), (CRM, "bang_tinh_xem"): Duong(_k(code="van_don")),
    (CRM, "bang_tinh_loc_cot"): Duong(_k(code="van_don", ma_cot="ghi_chu")),
    (CRM, "bang_tinh_xuat"): Duong(_k(code="van_don")),
    (CRM, "bang_tinh_moi_nhat"): Duong(_k(code="van_don")), (CRM, "master_filters"): Duong(_k(code="van_don")),
    # Sáu đường ghi ô của renderer HTMX cũ đã bỏ (ADR-021, 027): luôn 409 "Bộ lưới đã cập nhật", không ghi gì
    (CRM, "bang_tinh_o"): Duong(_k(code="van_don", pk=lambda w: w.dong[0].pk, ma_cot="ghi_chu")),
    (CRM, "bang_tinh_dong_moi"): Duong(_k(code="van_don")), (CRM, "bang_tinh_dinh_dang"): Duong(_k(code="van_don")),
    (CRM, "bang_tinh_luu_o"): Duong(_k(code="van_don")), (CRM, "bang_tinh_xoa_dong"): Duong(_k(code="van_don")),
    (CRM, "bang_tinh_khoi_phuc_dong"): Duong(_k(code="van_don")),
}

_KHONG_QUAN_LY = (404, "bảng đã xoá không nằm trong phạm vi xem của vai không quản lý: 404, không lộ bảng có tồn tại")
_KT_KHONG_THAY = {"staff_kt": (404, "Kế toán không thấy đối tượng của bộ phận khác: 404, không lộ đối tượng có tồn tại "
                                    "(cùng mẫu với _lay_bang, quy tắc 8)")}
_CO_TAT = (404, "cờ PAYMENT_DOCUMENTS_ENABLED tắt — tuyến 404 với mọi vai; khi bật có bài khoá ở P0-10")

#: Đường ghi: vai bị cấm POST payload hợp lệ thì 403 có nhật ký, không đổi gì.
GHI = {
    # ── Nhân sự, bộ phận: chỉ Admin; Giám đốc đặt lại mật khẩu, xoá tài khoản cấp dưới (ADR-044) nên ở đây
    #    nhắm hồ sơ một Admin khác — chiều được phép nằm ở bài DUOC
    (ERP, "nhan_su_moi"): Duong(payload=lambda w: {
        "full_name": "Người Quét Post", "staff_code": "QUETPOST", "username": "quetpost", "rank": Rank.STAFF,
        "department": w.bp["sale"].pk, "team": "", "password": "Mat-khau-quet-post-1"}),
    (ERP, "nhan_su_sua"): Duong(_k(pk=lambda w: w.nd["staff_sale_1"].profile.pk), lambda w: {
        "full_name": "Đổi Tên Quét", "staff_code": w.nd["staff_sale_1"].profile.staff_code, "rank": Rank.STAFF,
        "department": w.bp["sale"].pk, "team": w.nd["staff_sale_1"].profile.team_id or "", "birthday": ""}),
    (ERP, "nhan_su_dat_lai_mat_khau"): Duong(_k(pk=lambda w: w.admin2.profile.pk), lambda w: {
        "new_password1": "Mat-khau-moi-quet-1", "new_password2": "Mat-khau-moi-quet-1"}),
    (ERP, "nhan_su_xoa"): Duong(_k(pk=lambda w: w.admin2.profile.pk), lambda w: {"confirm": "yes"}),
    (ERP, "nhan_su_doi_trang_thai"): Duong(_k(pk=lambda w: w.nd["staff_sale_1"].profile.pk)),
    (ERP, "bo_phan"): Duong(payload=lambda w: {"tao_bo_phan": "1", "bp-name": "Bộ phận quét", "bp-code": "bp-quet",
                                               "bp-is_active": "on"}),
    # ── Bảng dữ liệu, biểu mẫu (KN ERP)
    (ERP, "bang_moi"): Duong(payload=lambda w: {"name": "Bảng quét", "code": "bang_quet", "description": ""},
                             hc="manager_sale"),
    (ERP, "bang_cot"): Duong(_k(code=lambda w: w.bang.code), lambda w: w.cot_moi),
    (ERP, "bang_nhap"): Duong(_k(code=lambda w: w.bang.code), lambda w: {"tep": w.tep_nhap()}),
    (ERP, "bang_nhap_xac_nhan"): Duong(_k(code=lambda w: w.bang.code, pk=lambda w: w.nhap.pk)),
    (ERP, "bang_xoa_cot"): Duong(_k(code=lambda w: w.bang.code, pk=lambda w: w.cot_bo.pk)),
    (ERP, "bang_them_lua_chon"): Duong(_k(code=lambda w: w.bang.code, ma_cot="kenh"),
                                       lambda w: {"nhan_moi": "Kênh quét"}),
    (ERP, "bang_cap_quyen"): Duong(_k(code=lambda w: w.bang.code), lambda w: {
        "user": w.nd["staff_vd"].pk, "team": "", "action": "view"}),
    (ERP, "bang_thu_quyen"): Duong(_k(code=lambda w: w.bang.code, pk=lambda w: w.quyen_bang.pk)),
    (ERP, "bieu_mau_moi"): Duong(payload=lambda w: {"name": "Biểu mẫu quét", "code": "bm_quet",
                                                    "description": "", "table": w.bang.pk}, hc="manager_sale"),
    (ERP, "truong_moi"): Duong(payload=lambda w: {"name": "Trường quét", "code": "truong_quet",
                                                  "field_type": "text", "meaning": "", "hint": "",
                                                  "default_value": ""}, hc="manager_sale"),
    (ERP, "bieu_mau_dien"): Duong(_k(code=lambda w: w.bm.code), lambda w: w.dien_bm,
                                  cam=CEO, hc="staff_sale_1"),
    (ERP, "bieu_mau_sua"): Duong(_k(code=lambda w: w.bm.code), lambda w: {
        "field": w.truong_them.pk, "column": w.cot_bo.pk, "required": ""}),
    (ERP, "bieu_mau_bo_truong"): Duong(_k(code=lambda w: w.bm.code, pk=lambda w: w.bm_truong.pk)),
    (ERP, "bieu_mau_cap_quyen"): Duong(_k(code=lambda w: w.bm.code), lambda w: {
        "user": w.nd["staff_vd"].pk, "team": "", "action": "fill"}),
    (ERP, "bieu_mau_thu_quyen"): Duong(_k(code=lambda w: w.bm.code, pk=lambda w: w.quyen_bm.pk)),
    # ── Báo cáo ngày (ADR-038, 041, 042)
    # Kế toán gửi biểu mẫu của Sale: ngoài phạm vi, 403 có nhật ký. Trang của Kế toán khi không gửi biểu mẫu nào nằm ở
    # bài test_ke_toan_khong_co_muc_nop_bao_cao
    (ERP, "bao_cao_ngay"): Duong(payload=lambda w: {**w.dien_bm, "bieu_mau": w.bm.code}, hc="staff_sale_1"),
    (ERP, "bao_cao_khoi_phuc"): Duong(_k(pk=lambda w: w.bao_cao_bo.pk)),
    (ERP, "bao_cao_tong_hop_nguong"): Duong(payload=lambda w: {
        "nguon": w.bang_mkt.code, "next": "/bao-cao/tong-hop/", "tot_cpo": "300.000", "kem_cpo": "800.000"}),
    # Kế toán sửa được báo cáo (AC-4.8) — chiều được phép ở bài DUOC
    (ERP, "bao_cao_sua"): Duong(_k(pk=lambda w: w.bao_cao.pk), lambda w: w.sua_bao_cao, cam=CEO,
                                ma={v: (404, "AC-50.4: Giám đốc xem được báo cáo nhưng không sửa — daily_service.can_amend "
                                             "sai thì 404") for v in CEO}, nhat_ky_404=CEO),
    (ERP, "bao_cao_bo"): Duong(_k(pk=lambda w: w.bao_cao.pk)),
    # ── Nội bộ (ADR-017): Giám đốc và Kế toán đăng bài, thích, bình luận, giao việc cho mình (bài DUOC); ở đây là
    #    đụng tới bài, bình luận, việc của người khác
    **{(ERP, ten): Duong(cam=(), hc=None, khong_hieu_chuan="mọi vai được làm (ADR-017, ADR-044) — chiều được phép "
                                                          "kiểm ở bài DUOC")
       for ten in ("bang_tin_dang", "bang_tin_thich", "bang_tin_binh_luan", "cong_viec_moi")},
    (ERP, "bang_tin_binh_luan_go"): Duong(_k(pk=lambda w: w.binh_luan.pk)),
    (ERP, "bang_tin_ghim"): Duong(_k(pk=lambda w: w.bai.pk), lambda w: {"ghim": "1"}),
    (ERP, "bang_tin_go"): Duong(_k(pk=lambda w: w.bai.pk)),
    (ERP, "tai_lieu_tai_len"): Duong(payload=lambda w: {
        "category": w.muc_tai_lieu.pk, "title": "Tài liệu quét", "description": "",
        "link": "https://example.com/quet"}, hc="manager_sale"),
    (ERP, "tai_lieu_muc_moi"): Duong(payload=lambda w: {"name": "Mục quét", "department": w.bp["sale"].pk},
                                     hc="manager_sale"),
    (ERP, "tai_lieu_go"): Duong(_k(pk=lambda w: w.tai_lieu.pk), ma=_KT_KHONG_THAY),
    (ERP, "cong_viec_sua"): Duong(_k(pk=lambda w: w.viec.pk), lambda w: {
        "title": "Việc đổi tên", "description": "", "assignee": w.nd["staff_sale_1"].pk, "priority": "vua",
        "due_date": ""}, hc="staff_sale_1", ma=_KT_KHONG_THAY),
    (ERP, "cong_viec_trang_thai"): Duong(_k(pk=lambda w: w.viec.pk), lambda w: {"trang_thai": "dang_lam"},
                                         hc="staff_sale_1", ma=_KT_KHONG_THAY),
    (ERP, "cong_viec_go"): Duong(_k(pk=lambda w: w.viec.pk), hc="staff_sale_1", ma=_KT_KHONG_THAY),
    (ERP, "van_hoa_ghi_nhan"): Duong(payload=lambda w: {
        "receiver": w.nd["staff_sale_1"].pk, "value": w.gia_tri_van_hoa, "message": "Làm tốt"}),
    (ERP, "tai_nguyen_moi"): Duong(payload=lambda w: {
        "category": w.muc_tai_nguyen.pk, "name": "Tài nguyên quét", "status": "trong", "holder": "",
        "department": "", "link": "", "note": ""}),
    (ERP, "tai_nguyen_muc_moi"): Duong(payload=lambda w: {"name": "Mục tài nguyên quét"}),
    (ERP, "tai_nguyen_sua"): Duong(_k(pk=lambda w: w.tai_nguyen.pk), lambda w: {
        "category": w.muc_tai_nguyen.pk, "name": "Tài nguyên đổi tên", "status": "trong", "holder": "",
        "department": "", "link": "", "note": ""}),
    (ERP, "tai_nguyen_go"): Duong(_k(pk=lambda w: w.tai_nguyen.pk)),
    # ── KN CRM: các view dùng chung với ERP, trên bảng vận đơn (KN CRM chỉ phục vụ bảng vận đơn, ADR-040)
    (CRM, "bang_moi"): Duong(payload=lambda w: {"name": "Bảng quét CRM", "code": "bang_quet_crm", "description": ""},
                             hc="manager_vd"),
    (CRM, "bang_cot"): Duong(_k(code="van_don"), lambda w: {**w.cot_moi, "code": "cot_quet_crm"}),
    (CRM, "bang_xoa_cot"): Duong(_k(code="van_don", pk=lambda w: w.cot_bo_vd.pk)),
    (CRM, "bang_nhap"): Duong(_k(code="van_don"), lambda w: {"tep": w.tep_nhap()},
                              hc=None, khong_hieu_chuan="cùng view bang_nhap của ERP, đã hiệu chuẩn ở ERP"),
    (CRM, "bang_nhap_xac_nhan"): Duong(_k(code="van_don", pk=lambda w: w.nhap.pk), hc=None,
                                       khong_hieu_chuan="tác vụ nhập thuộc bảng ERP; view đã hiệu chuẩn ở ERP"),
    (CRM, "bang_cap_quyen"): Duong(_k(code="van_don"), lambda w: {
        "user": w.nd["staff_mkt"].pk, "team": "", "action": "view"}),
    (CRM, "bang_thu_quyen"): Duong(_k(code="van_don", pk=lambda w: w.quyen_vd.pk)),
    # Giám đốc và Kế toán thấy bảng vận đơn nhưng không quản lý: 403 có nhật ký (P0-2)
    (CRM, "delete_table"): Duong(_k(code="van_don"), lambda w: {"name": w.van_don.name}, hc=None,
                                 khong_hieu_chuan="bảng vận đơn có protect_table: không ai xoá được, kể cả Admin"),
    (CRM, "restore_table"): Duong(_k(code=lambda w: w.bang_da_xoa.code), ma={v: _KHONG_QUAN_LY for v in CAM}),
    (CRM, "payment_create"): Duong(ma={v: _CO_TAT for v in CAM}, hc=None, khong_hieu_chuan=_CO_TAT[1]),
    (CRM, "payment_update"): Duong(_k(pk=1), ma={v: _CO_TAT for v in CAM}, hc=None, khong_hieu_chuan=_CO_TAT[1]),
    # Bỏ đơn chỉ Admin (ADR-049): view báo lỗi rồi quay về thư mục — 302 kèm dòng Từ chối, không 403
    (CRM, "don_bo"): Duong(_k(code=lambda w: w.don.code), ma={
        **{v: (302, "AC-6.13: từ chối có nhật ký rồi chuyển về thư mục kèm lời báo") for v in CEO}, **_KT_KHONG_THAY}),
    (CRM, "san_pham_moi"): Duong(payload=lambda w: {"nhan_moi": "Sản phẩm quét"}, hc="leader_sale_1"),
    (CRM, "master_save"): Duong(_k(code="van_don"), lambda w: {"operation": str(uuid.uuid4()), "cells": [
        {"id": w.dong[0].pk, "column": "ghi_chu", "old": w.dong[0].data.get("ghi_chu"), "value": "Quét POST"}]},
        json=True),
    (CRM, "master_clear_details"): Duong(_k(code="van_don"), lambda w: {"operation": str(uuid.uuid4()), "cells": [
        {"id": w.dong[0].pk, "column": "gia_tien", "old": w.dong[0].data.get("gia_tien")}]}, json=True),
    (CRM, "waybill_assignment"): Duong(payload=lambda w: {
        "versions": {str(w.dong[0].pk): 0}, "changes": {"delivery": w.nd["staff_vd"].pk}}, json=True,
        hc="manager_vd"),
    (CRM, "waybill_create"): Duong(payload=lambda w: w.don_moi, hc="staff_sale_1"),
    (CRM, "waybill_detail"): Duong(_k(pk=lambda w: w.dong[0].pk), lambda w: w.chi_tiet),
    (CRM, "thu_muc_moi"): Duong(payload=lambda w: {"bo_phan": w.bp["vd"].pk, "name": "Thư mục mới quét"}),
    (CRM, "thu_muc_sua"): Duong(_k(pk=lambda w: w.thu_muc.pk), lambda w: {"name": "Thư mục đổi tên"},
                                ma=_KT_KHONG_THAY),
    (CRM, "thu_muc_xoa"): Duong(_k(pk=lambda w: w.thu_muc.pk), ma=_KT_KHONG_THAY),
    (CRM, "bang_tinh_chuyen_thu_muc"): Duong(_k(code="van_don"), lambda w: {"folder": w.thu_muc.pk}),
    (CRM, "bang_tinh_them_cot"): Duong(_k(code="van_don"), lambda w: {"so": "1"}),
    (CRM, "bang_tinh_xoa_cot"): Duong(_k(code="van_don"), lambda w: {"cot": w.cot_bo_vd.code}),
    (CRM, "bang_tinh_an_cot"): Duong(_k(code="van_don"), lambda w: {"cot": "ghi_chu", "an": "1"}),
}

#: Ghi mà Giám đốc hay Kế toán **được** làm (ADR-044, ADR-038, ADR-017) — chặn quá tay cũng là lỗi.
DUOC = {
    ("ceo", ERP, "nhan_su_dat_lai_mat_khau"): Duong(_k(pk=lambda w: w.nd["staff_sale_1"].profile.pk), lambda w: {
        "new_password1": "Mat-khau-moi-quet-1", "new_password2": "Mat-khau-moi-quet-1"}),
    ("ceo", ERP, "nhan_su_xoa"): Duong(_k(pk=lambda w: w.nd["staff_sale_1b"].profile.pk), lambda w: {"confirm": "yes"}),
    ("ceo", ERP, "bang_tin_dang"): Duong(payload=lambda w: {"body": "Giám đốc chào cả nhà"}),
    ("ceo", ERP, "bang_tin_thich"): Duong(_k(pk=lambda w: w.bai.pk)),
    ("ceo", ERP, "bang_tin_binh_luan"): Duong(_k(pk=lambda w: w.bai.pk), lambda w: {"body": "Hay lắm"}),
    # Việc thuộc bộ phận của người làm: Giám đốc không bộ phận thì tầng dịch vụ báo "phải thuộc một bộ phận"
    ("ceo_sale", ERP, "cong_viec_moi"): Duong(payload=lambda w: {
        "title": "Việc của Giám đốc", "description": "", "assignee": w.vai["ceo_sale"].pk, "priority": "vua",
        "due_date": ""}),
    ("staff_kt", ERP, "bao_cao_sua"): Duong(_k(pk=lambda w: w.bao_cao.pk), lambda w: w.sua_bao_cao),
    ("staff_kt", ERP, "bang_tin_dang"): Duong(payload=lambda w: {"body": "Kế toán chào cả nhà"}),
    ("staff_kt", ERP, "cong_viec_moi"): Duong(payload=lambda w: {
        "title": "Việc của Kế toán", "description": "", "assignee": w.nd["staff_kt"].pk, "priority": "vua",
        "due_date": ""}),
}


# ══ HẠ TẦNG ══════════════════════════════════════════════════════

def _thu_thap(resolver, tien_to=""):
    """(tên, mẫu đường dẫn) của mọi URLPattern ngoài /quan-tri/ — kể cả mẫu quên đặt tên (tên None)."""
    for mau in resolver.url_patterns:
        if isinstance(mau, URLResolver):
            yield from _thu_thap(mau, tien_to + str(mau.pattern))
        elif isinstance(mau, URLPattern) and not (tien_to + str(mau.pattern)).startswith("quan-tri/"):
            yield mau.name, tien_to + str(mau.pattern)


CAC_MAU = {conf: list(_thu_thap(get_resolver(conf))) for conf in (ERP, CRM)}
CAC_DUONG = sorted({(conf, ten) for conf, mau in CAC_MAU.items() for ten, _ in mau if ten})


def _anh_chup():
    """Toàn bộ dữ liệu của các app dự án (trừ nhật ký) và tài khoản (trừ giờ đăng nhập), cộng tệp trong STORAGE_DIR."""
    kq = {}
    for nhan in settings.LOCAL_APPS:
        for mo_hinh in apps.get_app_config(nhan).get_models():
            if mo_hinh is not AuditLog:
                kq[mo_hinh._meta.label] = list(mo_hinh._base_manager.order_by("pk").values())
    kq["auth.User"] = [{k: v for k, v in u.items() if k != "last_login"}
                       for u in get_user_model()._base_manager.order_by("pk").values()]
    kq["tep"] = sorted(str(p) for p in settings.STORAGE_DIR.rglob("*") if p.is_file())
    return kq


def _khac(truoc, sau):
    return sorted(k for k in truoc if truoc[k] != sau.get(k))


def _cau_hinh(conf):
    """Mỗi dịch vụ một cấu hình như khi chạy thật (knjsc/settings/bangtinh.py)."""
    if conf == CRM:
        return override_settings(ROOT_URLCONF=CRM, GRID_ONLY_TABLES=set(), BANGTINH_URL="")
    return override_settings(ROOT_URLCONF=ERP, GRID_ONLY_TABLES={"van_don"})


def _gui(w, vai, conf, ten, d, *, hieu_chuan=False):
    """Đăng nhập bằng một client mới rồi POST; trả (phản hồi, số dòng Từ chối của vai tăng thêm, phần dữ liệu đổi)."""
    nguoi = w.vai[vai]
    client = Client()
    client.force_login(nguoi)
    ham_k = (d.hc_kwargs if hieu_chuan and d.hc_kwargs else d.kwargs)
    with _cau_hinh(conf):
        url = reverse(ten, kwargs=ham_k(w) if ham_k else None, urlconf=conf)
        payload = d.payload(w) if d.payload else {}
        tu_choi = AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi)
        dem, truoc = tu_choi.count(), _anh_chup()
        if d.json:
            r = client.post(url, payload, content_type="application/json")
        else:
            r = client.post(url, payload)
        if getattr(r, "streaming", False):
            b"".join(r.streaming_content)
        return r, tu_choi.count() - dem, _khac(truoc, _anh_chup())


def _tung_vai(cac_vai, viec):
    """Chạy `viec(vai)` cho từng vai trong một savepoint riêng, gom mọi lỗi rồi báo một lần."""
    loi = []
    for vai in cac_vai:
        sid = transaction.savepoint()
        try:
            loi += viec(vai)
        finally:
            transaction.savepoint_rollback(sid)
    assert not loi, "\n".join(loi)


# ══ THẾ GIỚI DỮ LIỆU ═════════════════════════════════════════════

@pytest.fixture
def w(settings, departments, nguoi_dung, make_user, bm_sale, bang_mkt, mkt_source):  # noqa: F811
    """Một đối tượng thật cho mỗi tham số đường dẫn, của người khác vai đang thử."""
    from culture.models import CoreValue
    from documents.services import document_service
    from feed.services import post_service
    from forms_builder.meaning import FieldType
    from forms_builder.models import ColumnDef, FieldDef, GrantAction, TableDef
    from forms_builder.services import folder_service, form_service, grant_service, import_service
    from openpyxl import Workbook
    from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
    from orders.models import Product
    from orders.services import dispatch_service, order_service
    from reports.services import daily_service
    from resources.services import resource_service
    from taskboard.services import task_service

    settings.GRID_ONLY_TABLES = set()
    admin, nd = nguoi_dung["admin"], nguoi_dung
    w = SimpleNamespace(nd=nd, bp=departments, bang=bm_sale.table, bm=bm_sale, bang_mkt=bang_mkt)
    w.admin2 = make_user("quan_tri_2", Rank.ADMIN)
    w.vai = {**nd, "ceo_sale": make_user("ceo_sale", Rank.CEO, departments["sale"]),
             "ceo_vd": make_user("ceo_vd", Rank.CEO, departments["vd"]), "admin2": w.admin2}

    # Bảng vận đơn, hai đơn của hai nhân viên Sale
    dispatch_service.ensure_waybill_table(actor=admin)
    w.van_don = TableDef.objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    sp = [Product.objects.create(code=f"quet-{i}", name=f"Sản phẩm quét {i}") for i in range(2)]
    w.don = order_service.create_order(phone="0900000001", customer_name="Khách quét",
                                       lines=[{"product": sp[0].code, "quantity": 1, "unit_price": "10.00"}],
                                       actor=nd["staff_sale_1"])
    don_2 = order_service.create_order(phone="0900000002", customer_name="Khách quét 2",
                                       lines=[{"product": sp[1].code, "quantity": 1, "unit_price": "10.00"}],
                                       actor=nd["staff_sale_2"])
    w.dong = [w.don.record, don_2.record]
    for r in w.dong:
        r.refresh_from_db()
    w.don_moi = {"phone": "0900000009", "customer_name": "Khách mới quét", "market": "us", "currency": "USD",
                 "payment_method": "zelle", "product": [sp[0].code], "quantity": ["1"], "unit_price": ["10.00"],
                 "ma_lan_nop": str(uuid.uuid4())}
    w.chi_tiet = {"product": [sp[1].code], "quantity": ["2"], "unit": [""], "unit_price": ["10.00"],
                  "paid_amount": ["0.00"], "version": w.dong[0].updated_at.isoformat()}
    w.cot_bo_vd = ColumnDef.objects.create(table=w.van_don, name="Cột phụ quét", code="cot_phu_quet",
                                           field_type=FieldType.TEXT, order=900)
    w.quyen_vd = grant_service.grant(table=w.van_don, user=nd["staff_mkt"], action=GrantAction.VIEW, actor=admin)
    w.thu_muc = folder_service.create_folder(name="Thư mục quét", department=departments["vd"], actor=admin)
    w.bang_da_xoa = TableDef.all_objects.create(name="Bảng đã xoá", code="bang_da_xoa_quet",
                                                department=departments["vd"], created_by=admin)
    TableDef.all_objects.filter(pk=w.bang_da_xoa.pk).update(deleted_at=w.van_don.created_at)

    # Bảng Sale và biểu mẫu báo cáo của nó (bm_sale)
    w.cot_bo = ColumnDef.objects.create(table=w.bang, name="Ghi chú quét", code="ghi_chu_quet",
                                        field_type=FieldType.TEXT, order=50)
    ColumnDef.objects.create(table=w.bang, name="Kênh", code="kenh", field_type=FieldType.CHOICE, order=51,
                             options=["Facebook"])
    w.cot_moi = {"name": "Cột quét", "code": "cot_quet", "field_type": "text", "meaning": "", "order": "60",
                 "options": "", "highlight": "", "alert_op": "", "alert_value": "", "compute_op": "",
                 "compute_left": "", "compute_right": "", "compute_decimals": "0"}
    w.quyen_bang = grant_service.grant(table=w.bang, user=nd["staff_mkt"], action=GrantAction.VIEW,
                                       actor=nd["manager_sale"])
    w.quyen_bm = grant_service.grant(form=w.bm, user=nd["staff_mkt"], action=GrantAction.FILL,
                                     actor=nd["manager_sale"])
    w.bm_truong = w.bm.fields.select_related("field").get(field__code="so_don")
    w.truong_them = FieldDef.objects.create(name="Ghi chú quét", code="ghi_chu_quet", field_type=FieldType.TEXT,
                                            department=departments["sale"])
    w.dien_bm = {"ngay": date.today().isoformat(), "so_mess": "10", "so_don": "2", "doanh_so": "100",
                 "ma_lan_nop": str(uuid.uuid4())}

    def tep_nhap():
        so = Workbook()
        so.active.append(["Ngày", "Số Mess", "Số đơn", "Doanh số"])
        so.active.append([date.today().isoformat(), 5, 1, 50])
        dem = io.BytesIO()
        so.save(dem)
        return SimpleUploadedFile("nhap.xlsx", dem.getvalue(),
                                  content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    w.tep_nhap = tep_nhap
    w.nhap = import_service.prepare(w.bang, tep_nhap(), actor=admin)

    # Báo cáo ngày của staff_sale_1: một bản đang có, một bản đã bỏ
    w.bao_cao = _nop(w.bm, nd["staff_sale_1"])
    w.bao_cao_bo = _nop(w.bm, nd["staff_sale_1"], so_mess="9")
    daily_service.withdraw(w.bao_cao_bo, actor=nd["staff_sale_1"])
    sua = {"version": w.bao_cao.record.updated_at.isoformat(), "so_mess": "250", "so_don": "50", "doanh_so": "5000000"}
    w.sua_bao_cao = sua

    # Nội bộ: mọi thứ của người khác (staff_sale_1, manager_sale)
    w.bai = post_service.create_post(body="Bài của nhân viên Sale", actor=nd["staff_sale_1"])
    w.binh_luan = post_service.add_comment(w.bai, body="Bình luận của Sale", actor=nd["staff_sale_1"])
    w.viec = task_service.create_task(title="Việc của Sale", assignee=nd["staff_sale_1"], actor=nd["staff_sale_1"])
    w.muc_tai_lieu = document_service.create_category(name="Mục Sale", department=departments["sale"],
                                                      actor=nd["manager_sale"])
    w.tai_lieu = document_service.upload_document(title="Tài liệu Sale", category=w.muc_tai_lieu,
                                                  link="https://example.com/sale", actor=nd["manager_sale"])
    w.muc_tai_nguyen = resource_service.create_category(name="Mục máy", actor=nd["manager_sale"])
    w.tai_nguyen = resource_service.create_resource(category=w.muc_tai_nguyen, name="Máy quét",
                                                    actor=nd["manager_sale"])
    w.gia_tri_van_hoa = CoreValue.values[0]

    from core.constants import JobKind, JobStatus
    from core.models import BackgroundJob
    w.job = BackgroundJob.objects.create(kind=JobKind.values[0], status=JobStatus.DONE, created_by=admin,
                                         title="Tác vụ quét")
    return w


# ══ BÀI KIỂM ═════════════════════════════════════════════════════

def test_moi_duong_dan_deu_da_xep_loai():
    """AC-3.7 — Mọi đường của KN ERP và KN CRM (trừ /quan-tri/) nằm đúng một trong ba nhóm Bỏ qua, Chỉ đọc, Ghi; đường
    mới chưa xếp loại thì đỏ để không ai quên kiểm quyền cho nó (P0-2)"""
    nhom = [set(BO_QUA), set(CHI_DOC), set(GHI)]
    chua = [d for d in CAC_DUONG if not any(d in n for n in nhom)]
    assert not chua, "Đường chưa xếp loại — thêm vào BO_QUA, CHI_DOC hay GHI kèm lý do:\n" + "\n".join(map(str, chua))
    trung = [d for d in CAC_DUONG if sum(d in n for n in nhom) > 1]
    assert not trung, f"Đường nằm ở hơn một nhóm: {trung}"
    thua = sorted(set().union(*nhom) - set(CAC_DUONG))
    assert not thua, f"Đường không còn trong bộ định tuyến, gỡ khỏi bảng: {thua}"
    assert len(CAC_DUONG) >= 150
    # Bài POST dựa vào reverse(tên): mẫu quên name= hay hai mẫu trùng tên sẽ lọt khỏi bảng xếp loại
    khong_ten = [(conf, duong) for conf, mau in CAC_MAU.items() for ten, duong in mau if not ten]
    assert not khong_ten, f"Đường thiếu name= — đặt tên rồi xếp loại: {khong_ten}"
    trung_ten = [(conf, ten) for conf, mau in CAC_MAU.items() for ten in {t for t, _ in mau}
                 if [t for t, _ in mau].count(ten) > 1 and (conf, ten) not in BO_QUA]
    assert not trung_ten, f"Hai mẫu cùng tên trong một dịch vụ: {trung_ten}"
    assert all(len(ly_do) > 10 for ly_do in BO_QUA.values())
    # Mã khác 403 phải có lý do, và đường không hiệu chuẩn cũng vậy
    for d in GHI.values():
        assert all(len(ly_do) > 10 for _, ly_do in d.ma.values())
        assert d.hc or len(d.khong_hieu_chuan) > 10


@pytest.mark.cham
@pytest.mark.parametrize("conf,ten", sorted(k for k, d in GHI.items() if d.cam), ids=lambda x: str(x))
def test_vai_bi_cam_post_khong_ghi_va_tu_choi_co_nhat_ky(w, conf, ten):
    """AC-3.7 — Giám đốc (không bộ phận, gắn Sale, gắn Vận đơn) và Staff Kế toán POST thẳng một đường ghi nghiệp vụ với
    payload hợp lệ: bị từ chối 403 và có thêm đúng một dòng Từ chối của vai đó (FR-3.5, AC-44.6, ADR-038); cơ sở dữ liệu
    và thư mục tệp không đổi; mã khác 403 chỉ ở chỗ đã ghi lý do (P0-2, TL-91)"""
    d = GHI[(conf, ten)]

    def viec(vai):
        r, them, doi = _gui(w, vai, conf, ten, d)
        mong, _ = d.ma.get(vai, (403, ""))
        loi = []
        if r.status_code != mong:
            loi.append(f"{vai}: mã {r.status_code}, mong {mong}")
        if doi:
            loi.append(f"{vai}: dữ liệu đổi ở {doi}")
        if (mong in (302, 403) or vai in d.nhat_ky_404) and them != 1:
            loi.append(f"{vai}: bị từ chối ({r.status_code}) mà có {them} dòng Từ chối, mong đúng 1")
        return loi

    _tung_vai(d.cam, viec)


@pytest.mark.cham
@pytest.mark.parametrize("conf,ten", sorted(CHI_DOC), ids=lambda x: str(x))
def test_post_duong_chi_doc_khong_doi_db_va_403_co_nhat_ky(w, conf, ten):
    """AC-3.7 — POST vào đường chỉ đọc bằng Giám đốc hay Kế toán: không lỗi 500, không đổi cơ sở dữ liệu hay tệp; trả
    403 thì phải có đúng một dòng Từ chối của vai đó (FR-3.5, P0-2)"""
    d = CHI_DOC[(conf, ten)]

    def viec(vai):
        r, them, doi = _gui(w, vai, conf, ten, d)
        loi = []
        if r.status_code >= 500:
            loi.append(f"{vai}: lỗi {r.status_code}")
        if doi:
            loi.append(f"{vai}: dữ liệu đổi ở {doi}")
        if r.status_code == 403 and them != 1:
            loi.append(f"{vai}: 403 mà có {them} dòng Từ chối, mong đúng 1")
        return loi

    _tung_vai(CAM, viec)


@pytest.mark.cham
@pytest.mark.parametrize("conf,ten", sorted(k for k, d in GHI.items() if d.hc), ids=lambda x: str(x))
def test_payload_mau_hop_le_voi_vai_doi_chung(w, conf, ten):
    """AC-3.7 — Cùng payload gửi bằng vai được phép thì ghi được (200/204/302 và cơ sở dữ liệu đổi): lần bị từ chối
    ở bài trên là do cổng quyền, không phải do payload hay tham số đường dẫn sai (P0-2)"""
    d = GHI[(conf, ten)]

    def viec(vai):
        r, _, doi = _gui(w, vai, conf, ten, d, hieu_chuan=True)
        loi = []
        if r.status_code not in (200, 204, 302):
            ctx = getattr(r, "context", None) or {}
            loi.append(f"{vai}: mã {r.status_code} — {ctx.get('error', '') if ctx else ''} "
                       f"{getattr(ctx.get('form'), 'errors', '') if ctx else ''}")
        if not doi:
            loi.append(f"{vai}: không ghi được gì — payload chưa hợp lệ ({r.status_code})")
        return loi

    _tung_vai([d.hc], viec)


@pytest.mark.cham
@pytest.mark.parametrize("vai,conf,ten", sorted(DUOC), ids=lambda x: str(x))
def test_ceo_va_ke_toan_van_ghi_duoc_viec_duoc_phep(w, vai, conf, ten):
    """AC-44.6 — Giám đốc vẫn đặt lại mật khẩu, xoá tài khoản cấp dưới (ADR-044), đăng bài, thích, bình luận và giao
    việc cho chính mình; Kế toán vẫn sửa báo cáo (AC-4.8), đăng bài, giao việc cho mình — chặn POST không được chặn
    quá tay (P0-2)"""
    d = DUOC[(vai, conf, ten)]
    r, them, doi = _gui(w, vai, conf, ten, d)
    assert r.status_code in (200, 204, 302), r.content.decode()[:300]
    assert doi and them == 0


CAU_KHONG_BIEU_MAU = "Bộ phận của bạn chưa có biểu mẫu báo cáo ngày — liên hệ quản lý"


def test_ke_toan_khong_co_muc_nop_bao_cao(w):
    """AC-4.1 — Bộ phận chưa có biểu mẫu báo cáo ngày (Kế toán) thì không thấy mục "Nộp báo cáo ngày" trên menu lẫn nút
    Nộp báo cáo ở Lịch sử; gõ thẳng /bao-cao/ (GET hay POST không chọn biểu mẫu) thấy câu báo, mã 200, không ghi gì.
    Manager Sale có biểu mẫu vẫn thấy mục; Manager tạo biểu mẫu cho Kế toán thì mục tự hiện lại (chủ dự án 13–14.10)"""
    from core.navigation import visible_navigation
    from forms_builder.models import FormDef
    from reports.services import daily_service

    def co_muc(nguoi):
        return "bao_cao_ngay" in {m["code"] for nhom in visible_navigation(nguoi) for m in nhom["items"]}

    kt, sale = w.nd["staff_kt"], w.nd["manager_sale"]
    assert not co_muc(kt) and co_muc(sale) and not co_muc(w.nd["ceo"])
    client = Client()
    client.force_login(kt)
    with _cau_hinh(ERP):
        assert 'href="/bao-cao/"' not in client.get("/bao-cao/lich-su/").content.decode()
        truoc = _anh_chup()
        for r in (client.get("/bao-cao/"), client.post("/bao-cao/", {"so_mess": "1"})):
            assert r.status_code == 200 and CAU_KHONG_BIEU_MAU in r.content.decode()
        assert not _khac(truoc, _anh_chup())
    FormDef.objects.create(table=w.bang, department=w.bp["kt"], code="bc_ke_toan", name="Báo cáo Kế toán")
    assert co_muc(kt) and daily_service.can_submit_reports(kt)
