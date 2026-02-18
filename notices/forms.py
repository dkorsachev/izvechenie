from django import forms
from django.forms import inlineformset_factory
from .models import Notice, NoticeItem


class NoticeForm(forms.ModelForm):
    class Meta:
        model  = Notice
        fields = ['newspaper', 'issue_date', 'approval_date']
        widgets = {
            'newspaper': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Название газеты',
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
            'approval_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Все поля необязательны
        for field in self.fields.values():
            field.required = False
        # Дополнительно явно для newspaper — на случай если что-то переопределяет
        self.fields['newspaper'].required = False

class NoticeItemForm(forms.ModelForm):
    class Meta:
        model  = NoticeItem
        fields = [
            'address', 'fias_id', 'region', 'city', 'street', 'house',
            'cadastral_number', 'customer', 'contract', 'order',
        ]
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control form-control-sm address-autocomplete',
                'placeholder': 'Начните вводить адрес...',
                'autocomplete': 'off',
            }),
            'fias_id': forms.HiddenInput(),
            'region':  forms.HiddenInput(),
            'city':    forms.HiddenInput(),
            'street':  forms.HiddenInput(),
            'house':   forms.HiddenInput(),
            'order':   forms.HiddenInput(),
            'cadastral_number': forms.TextInput(attrs={
                'class': 'form-control form-control-sm cadastral-input',
                # placeholder отражает маску
                'placeholder': '__:__:_______:______',
                'maxlength': '23',
                'autocomplete': 'off',
            }),
            'customer': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Наименование заказчика',
            }),
            'contract': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Номер договора',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Все поля необязательны
        for field in self.fields.values():
            field.required = False


NoticeItemFormSet = inlineformset_factory(
    Notice, NoticeItem,
    form=NoticeItemForm,
    extra=0,
    can_delete=True,
    min_num=0,           # убираем обязательность минимум одной строки
    validate_min=False,
)


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Поиск по всем полям...',
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date',
        })
    )
    date_field = forms.ChoiceField(
        required=False,
        choices=[
            ('issue_date',    'Дата выпуска'),
            ('approval_date', 'Дата согласования'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )