"""Ô nhập của Lên đơn KN CRM; nghiệp vụ vẫn do orders xử lý."""
from django import forms
from django.urls import reverse
from orders.constants import Market, ACTIVE_PAYMENT_CHOICES
from orders.services import currency_service


class WaybillOrderForm(forms.Form):
    customer_name = forms.CharField(label="Tên khách", max_length=200)
    phone = forms.CharField(label="Số điện thoại", max_length=40)
    facebook = forms.CharField(label="Facebook", max_length=200, required=False)
    email = forms.EmailField(label="Email", required=False)
    market = forms.ChoiceField(label="Quốc gia", choices=[("", "— Chọn quốc gia —"), *Market.choices])
    state = forms.CharField(label="Bang", max_length=120, required=False)
    city = forms.CharField(label="Thành phố", max_length=120, required=False)
    zipcode = forms.CharField(label="Zipcode", max_length=20, required=False)
    address_line = forms.CharField(label="Chi tiết số nhà, đường", max_length=300, required=False)
    currency = forms.CharField(label="Loại tiền", required=False,
        widget=forms.TextInput(attrs={'readonly': True, 'placeholder': 'Tự theo quốc gia'}))
    payment_method = forms.ChoiceField(label="PTTT lên đơn", choices=[("", "— Chọn PTTT —"), *ACTIVE_PAYMENT_CHOICES])
    note = forms.CharField(label="Ghi chú", max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        # Lời nhắc khách phải tính lại khi **một trong hai** ô đổi: gõ nhầm số thì
        # tên khách lạ hiện ra ngay, còn sửa tên của số đã có thì hiện cảnh báo sắp
        # đổi tên trong danh bạ. Mỗi ô gửi kèm ô kia, nếu không server chỉ thấy một nửa.
        nhac = {
            "hx-get": reverse("kiem_khach"),
            "hx-trigger": "change, keyup changed delay:600ms",
            "hx-target": "#nhac-khach", "hx-swap": "outerHTML",
        }
        self.fields["phone"].widget.attrs.update(
            {**nhac, "hx-include": "[name=customer_name]"})
        self.fields["customer_name"].widget.attrs.update(
            {**nhac, "hx-include": "[name=phone]"})
        for field in self.fields.values():
            field.widget.attrs["class"] = "o-nhap"

    def clean(self):
        cleaned = super().clean()
        if self.data.get('seller'):
            raise forms.ValidationError('Người đứng đơn do hệ thống lấy từ tài khoản đang đăng nhập.')
        if cleaned.get('market'):
            cleaned['currency'] = currency_service.for_market(cleaned['market'])
        return cleaned
