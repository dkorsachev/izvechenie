from django.contrib import admin
from .models import Notice, NoticeItem


class NoticeItemInline(admin.TabularInline):
    model  = NoticeItem
    extra  = 1
    fields = [
        'order', 'address', 'cadastral_number',
        'customer', 'contract', 'fias_id',
    ]


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'newspaper', 'issue_date', 'approval_date', 'created_at']
    list_filter   = ['issue_date', 'approval_date']
    search_fields = ['newspaper']
    inlines       = [NoticeItemInline]


@admin.register(NoticeItem)
class NoticeItemAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'notice', 'address', 'cadastral_number', 'customer', 'contract']
    search_fields = ['address', 'cadastral_number', 'customer', 'contract']
    list_filter   = ['notice']