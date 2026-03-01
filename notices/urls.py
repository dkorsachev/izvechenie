from django.urls import path
from . import views

urlpatterns = [
    path('',               views.notice_list,         name='notice_list'),
    path('create/',        views.notice_create,        name='notice_create'),
    path('<int:pk>/get/',  views.notice_get,           name='notice_get'),
    path('<int:pk>/edit/', views.notice_edit,          name='notice_edit'),
    path('<int:pk>/delete/', views.notice_delete,      name='notice_delete'),
    path('<int:pk>/export/', views.notice_export_word, name='notice_export'),
    path('fias/suggest/',  views.fias_suggest,         name='fias_suggest'),
    path('import/',       views.notice_import, name='notice_import'),
    path('import/template/', views.notice_import_template, name='notice_import_template'),
]