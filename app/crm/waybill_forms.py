"""Ô nhập của Lên đơn KN CRM; nghiệp vụ vẫn do orders xử lý."""
from django import forms
from core.constants import Currency
from orders.constants import Market, PaymentMethod
from core.constants import Rank
from core.permissions import has_rank


class SellerChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.username} — {obj.profile.full_name}'


class WaybillOrderForm(forms.Form):
    customer_name = forms.CharField(label="Tên khách", max_length=200)
    phone = forms.CharField(label="Số điện thoại", max_length=40)
    market = forms.ChoiceField(label="Quốc gia", choices=Market.choices)
    state = forms.CharField(label="Bang", max_length=120, required=False)
    city = forms.CharField(label="Thành phố", max_length=120, required=False)
    zipcode = forms.CharField(label="Zipcode", max_length=20, required=False)
    address_line = forms.CharField(label="Chi tiết số nhà, đường", max_length=300, required=False)
    currency = forms.ChoiceField(label="Loại tiền", choices=Currency.choices, initial=Currency.USD)
    payment_method = forms.ChoiceField(label="PTTT lên đơn", choices=PaymentMethod.choices)
    note = forms.CharField(label="Ghi chú", max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        actor = kwargs.pop('actor', None)
        self.actor = actor
        super().__init__(*args, **kwargs)
        if actor and has_rank(actor, Rank.ADMIN):
            from orders.services.assignment_service import candidates
            self.fields['seller'] = SellerChoice(label='Sale đứng đơn', queryset=candidates('care').filter(
                profile__department__code='sale',profile__department__is_active=True,
                profile__department__deleted_at__isnull=True))
        for field in self.fields.values():
            field.widget.attrs["class"] = "o-nhap"

    def clean(self):
        cleaned = super().clean()
        if self.data.get('seller') and 'seller' not in self.fields:
            raise forms.ValidationError('Chỉ Admin được chọn Sale đứng đơn.')
        return cleaned
