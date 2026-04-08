import re
import requests
import openpyxl
from collections import OrderedDict
from datetime import date, timedelta, datetime
from io import BytesIO

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django import forms
from django.forms import formset_factory, inlineformset_factory

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import Notice, NoticeItem


# ──────────────────────────────────────────────
# Формы
# ──────────────────────────────────────────────
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['newspaper', 'issue_date', 'approval_date']
        widgets = {
            'newspaper': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название газеты'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_issue_date'
            }),
            'approval_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_approval_date'
            }),
        }
        labels = {
            'newspaper': 'Газета',
            'issue_date': 'Дата выпуска',
            'approval_date': 'Дата согласования',
        }

class NoticeItemForm(forms.ModelForm):
    class Meta:
        model = NoticeItem
        fields = ['address', 'fias_id', 'region', 'city', 'street', 'house', 
                  'cadastral_number', 'customer', 'contract', 'order']
        widgets = {
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Введите адрес'
            }),
            'cadastral_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кадастровый номер'
            }),
            'customer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заказчик'
            }),
            'contract': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Номер договора'
            }),
            'region': forms.HiddenInput(),
            'city': forms.HiddenInput(),
            'street': forms.HiddenInput(),
            'house': forms.HiddenInput(),
            'fias_id': forms.HiddenInput(),
            'order': forms.HiddenInput(),
        }

NoticeItemFormSet = inlineformset_factory(
    Notice, NoticeItem,
    form=NoticeItemForm,
    extra=1,
    can_delete=True
)

class SearchForm(forms.Form):
    q          = forms.CharField(required=False, label='Поиск')
    date_from  = forms.DateField(required=False, label='Дата с', 
                                 widget=forms.DateInput(attrs={'type': 'date'}))
    date_to    = forms.DateField(required=False, label='Дата по',
                                 widget=forms.DateInput(attrs={'type': 'date'}))
    date_field = forms.ChoiceField(
        required=False,
        choices=[('issue_date', 'Дата выпуска'), ('approval_date', 'Дата согласования')],
        label='Поле даты'
    )