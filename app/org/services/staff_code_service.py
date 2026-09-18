"""Mã nhân sự theo quy ước công ty — ADR-037.

Quy tắc (sheet Quy ước-Định nghĩa 2.0): từ cuối của họ tên là TÊN, cộng chữ cái đầu
của từng từ đứng trước, viết hoa không dấu, viết liền — Lê Thưởng Thuận → THUANLT;
đã có thì người sau thêm số từ 2: THUANLT2, THUANLT3. Mã gán rồi thì cố định.

Tầng dịch vụ, không biết HTTP. `UserProfile.save()` gọi `suggest` khi mã rỗng nên mọi
hồ sơ luôn có mã; màn hình tạo tài khoản gọi `suggest` để điền sẵn.
"""
import re
import unicodedata

from django.contrib.auth import get_user_model

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError

#: Chữ hoa, số, bắt đầu bằng chữ, tối đa 20 ký tự — đúng độ dài cột `staff_code`.
CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{0,19}$")
MAX_LENGTH = 20
#: Họ tên hay tên đăng nhập không cho ra chữ nào thì lấy tiền tố này cộng số
FALLBACK_PREFIX = "NV"


def strip_accents(text):
    """Bỏ dấu tiếng Việt, đổi đ → d, viết hoa; chỉ giữ chữ, số và khoảng trắng."""
    text = unicodedata.normalize("NFD", str(text or "")).replace("đ", "d").replace("Đ", "D")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = unicodedata.normalize("NFC", text).upper()
    return re.sub(r"[^A-Z0-9 ]+", " ", text)


def normalise(code):
    """Chuỗi người gõ → dạng lưu: viết hoa, không dấu, không khoảng trắng."""
    return strip_accents(code).replace(" ", "")


def validate(code):
    if not CODE_PATTERN.match(code or ""):
        raise BusinessError(
            "Mã nhân sự chỉ gồm chữ không dấu và số, bắt đầu bằng chữ, tối đa 20 ký tự."
        )
    return code


def base_code(full_name):
    """Phần gốc theo quy tắc, chưa xét trùng. Họ tên không cho ra mã hợp lệ thì rỗng."""
    words = strip_accents(full_name).split()
    if not words:
        return ""
    code = (words[-1] + "".join(w[0] for w in words[:-1]))[:MAX_LENGTH]
    return code if CODE_PATTERN.match(code) else ""


def _taken(code, *, exclude_pk=None, exclude_user_pk=None):
    """Mã đã có người dùng, hoặc trùng tên đăng nhập người khác (tài khoản mới dùng mã
    làm tên đăng nhập nên hai sổ không được chéo nhau)."""
    from ..models import UserProfile

    profiles = UserProfile.objects.filter(staff_code=code)
    if exclude_pk is not None:
        profiles = profiles.exclude(pk=exclude_pk)
    if profiles.exists():
        return True
    users = get_user_model().objects.filter(username__iexact=code)
    if exclude_user_pk is not None:
        users = users.exclude(pk=exclude_user_pk)
    if exclude_pk is not None:
        users = users.exclude(profile__pk=exclude_pk)
    return users.exists()


def suggest(full_name, username="", *, exclude_pk=None, exclude_user_pk=None):
    """Mã gợi ý cho một người: gốc theo họ tên (không được thì theo tên đăng nhập),
    trùng thì thêm 2, 3… — chưa ghi gì."""
    base = base_code(full_name) or normalise(username)
    if not CODE_PATTERN.match(base):
        base = (FALLBACK_PREFIX + re.sub(r"[^A-Z0-9]", "", base))[:MAX_LENGTH]
    candidate, n = base, 1
    while _taken(candidate, exclude_pk=exclude_pk, exclude_user_pk=exclude_user_pk):
        n += 1
        suffix = str(n)
        candidate = base[:MAX_LENGTH - len(suffix)] + suffix
    return candidate


def assign(profile, code, *, actor=None, request=None):
    """Gán mã cho hồ sơ chưa có mã. Đã có mã khác thì từ chối — mã cố định (ADR-037)."""
    code = validate(normalise(code))
    if profile.staff_code and profile.staff_code != code:
        raise BusinessError("Mã nhân sự đã cố định, không đổi được.")
    if _taken(code, exclude_pk=profile.pk, exclude_user_pk=profile.user_id):
        raise BusinessError("Mã nhân sự này đã có người dùng.")
    if profile.staff_code == code:
        return profile
    profile.staff_code = code
    profile.save(update_fields=["staff_code", "updated_at"])
    record(
        AuditAction.UPDATE, actor=actor, target=profile,
        detail=f"Gán mã nhân sự {code}", request=request,
        actor_label="" if actor is not None else "gan_ma_nhan_su",
    )
    return profile
