"""Ô nhập của Lên đơn KN CRM; nghiệp vụ vẫn do orders xử lý."""
from django import forms
from django.urls import reverse
from core.constants import Currency
from orders.constants import Market, PaymentMethod


class WaybillOrderForm(forms.Form):
    customer_name = forms.CharField(label="Tên khách", max_length=200)
    phone = forms.CharField(label="Số điện thoại", max_length=40)
    facebook = forms.CharField(label="Facebook", max_length=200, required=False)
    email = forms.EmailField(label="Email", required=False)
    sub_unit = forms.CharField(label="Đơn vị phụ", max_length=120, required=False)
    market = forms.ChoiceField(label="Quốc gia", choices=[("", "— Chọn quốc gia —"), *Market.choices])
    state = forms.CharField(label="Bang", max_length=120, required=False)
    city = forms.CharField(label="Thành phố", max_length=120, required=False)
    zipcode = forms.CharField(label="Zipcode", max_length=20, required=False)
    address_line = forms.CharField(label="Chi tiết số nhà, đường", max_length=300, required=False)
    currency = forms.ChoiceField(label="Loại tiền", choices=[("", "— Chọn loại tiền —"), *Currency.choices])
    payment_method = forms.ChoiceField(label="PTTT lên đơn", choices=[("", "— Chọn PTTT —"), *PaymentMethod.choices])
    note = forms.CharField(label="Ghi chú", max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        self.fields["phone"].widget.attrs.update({
            "hx-get": reverse("kiem_khach"),
            "hx-trigger": "change, keyup changed delay:600ms",
            "hx-target": "#nhac-khach", "hx-swap": "outerHTML",
        })
        for field in self.fields.values():
            field.widget.attrs["class"] = "o-nhap"

    def clean(self):
        cleaned = super().clean()
        if self.data.get('seller'):
            raise forms.ValidationError('Người đứng đơn do hệ thống lấy từ tài khoản đang đăng nhập.')
        return cleaned
