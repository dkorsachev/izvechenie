import re
import requests
from datetime import date, timedelta
from io import BytesIO

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from .models import Notice, NoticeItem
from .forms import NoticeForm, NoticeItemFormSet, SearchForm


# ──────────────────────────────────────────────
# Подсветка поиска
# ──────────────────────────────────────────────
def highlight(text, query):
    if not query or not text:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark>{m.group(0)}</mark>', str(text))


# ──────────────────────────────────────────────
# Список
# ──────────────────────────────────────────────
def notice_list(request):
    form  = SearchForm(request.GET or None)
    qs    = Notice.objects.prefetch_related('items').all()
    query = ''

    if form.is_valid():
        query      = form.cleaned_data.get('q', '')
        date_from  = form.cleaned_data.get('date_from')
        date_to    = form.cleaned_data.get('date_to')
        date_field = form.cleaned_data.get('date_field') or 'issue_date'

        if query:
            qs = qs.filter(
                Q(newspaper__icontains=query) |
                Q(items__address__icontains=query) |
                Q(items__cadastral_number__icontains=query) |
                Q(items__customer__icontains=query) |
                Q(items__contract__icontains=query)
            ).distinct()

        if date_from:
            qs = qs.filter(**{f'{date_field}__gte': date_from})
        if date_to:
            qs = qs.filter(**{f'{date_field}__lte': date_to})

    notices = []
    for n in qs:
        items_hl = []
        for it in n.items.all():
            items_hl.append({
                'address':          highlight(it.address, query),
                'cadastral_number': highlight(it.cadastral_number, query),
                'customer':         highlight(it.customer, query),
                'contract':         highlight(it.contract, query),
            })
        notices.append({
            'obj':             n,
            'newspaper':       highlight(n.newspaper, query),
            'items':           items_hl,
            'approval_status': n.approval_status,
        })

    return render(request, 'notices/list.html', {
        'notices':     notices,
        'search_form': form,
        'query':       query,
    })


# ──────────────────────────────────────────────
# Создание
# ──────────────────────────────────────────────
def notice_create(request):
    if request.method == 'POST':
        form    = NoticeForm(request.POST)
        formset = NoticeItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            notice          = form.save()
            formset.instance = notice
            formset.save()
            messages.success(request, 'Извещение добавлено.')
            return redirect('notice_list')
        errors = {**form.errors}
        for i, fe in enumerate(formset.errors):
            if fe:
                errors[f'Строка {i+1}'] = list(fe.values())
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    return redirect('notice_list')


# ──────────────────────────────────────────────
# Получение данных для редактирования (AJAX)
# ──────────────────────────────────────────────
@require_GET
def notice_get(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    items  = list(notice.items.values(
        'id', 'address', 'fias_id', 'region', 'city',
        'street', 'house', 'cadastral_number', 'customer', 'contract', 'order'
    ))
    return JsonResponse({
        'id':            notice.pk,
        'newspaper':     notice.newspaper,
        'issue_date':    notice.issue_date.isoformat()    if notice.issue_date    else '',
        'approval_date': notice.approval_date.isoformat() if notice.approval_date else '',
        'items':         items,
    })


# ──────────────────────────────────────────────
# Редактирование
# ──────────────────────────────────────────────
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    if request.method == 'POST':
        form    = NoticeForm(request.POST, instance=notice)
        formset = NoticeItemFormSet(request.POST, instance=notice)

        if form.is_valid() and formset.is_valid():
            form.save()
            # Удаляем все старые items и сохраняем только новые из формы
            notice.items.all().delete()
            instances = formset.save(commit=False)
            for obj in instances:
                obj.notice = notice
                obj.save()
            # Удалённые через can_delete тоже обрабатываем
            for obj in formset.deleted_objects:
                if obj.pk:
                    obj.delete()
            messages.success(request, 'Извещение обновлено.')
            return redirect('notice_list')

        errors = {**form.errors}
        for i, fe in enumerate(formset.errors):
            if fe:
                errors[f'Строка {i + 1}'] = list(fe.values())
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    return redirect('notice_list')


# ──────────────────────────────────────────────
# Удаление
# ──────────────────────────────────────────────
@require_POST
def notice_delete(request, pk):
    get_object_or_404(Notice, pk=pk).delete()
    messages.success(request, 'Извещение удалено.')
    return redirect('notice_list')


# ──────────────────────────────────────────────
# ФИАС (DaData)
# ──────────────────────────────────────────────
def fias_suggest(request):
    q = request.GET.get('q', '')
    if not q:
        return JsonResponse({'suggestions': []})
    token = getattr(settings, 'DADATA_TOKEN', '')
    if not token or token == 'ВАШ_ТОКЕН_DADATA':
        return JsonResponse({'suggestions': [
            {'value': q + ' (укажите DADATA_TOKEN)', 'fias_id': '',
             'region': '', 'city': '', 'street': '', 'house': ''}
        ]})
    try:
        resp = requests.post(
            settings.FIAS_API_URL,
            json={'query': q, 'count': 10},
            headers={'Authorization': f'Token {token}',
                     'Content-Type': 'application/json'},
            timeout=3
        )
        resp.raise_for_status()
        out = []
        for s in resp.json().get('suggestions', []):
            d = s.get('data', {})
            out.append({
                'value':   s.get('value', ''),
                'fias_id': d.get('fias_id', '') or d.get('house_fias_id', ''),
                'region':  d.get('region_with_type', ''),
                'city':    d.get('city_with_type', '') or d.get('settlement_with_type', ''),
                'street':  d.get('street_with_type', ''),
                'house':   d.get('house', ''),
            })
        return JsonResponse({'suggestions': out})
    except Exception as e:
        return JsonResponse({'suggestions': [], 'error': str(e)})


# ──────────────────────────────────────────────
# Экспорт Word
# ──────────────────────────────────────────────
RED  = (0xC0, 0x00, 0x00)
GREY = (0x80, 0x80, 0x80)

_MONTHS_RU = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']


def _fmt_date(d):
    return f'{d.day:02d} {_MONTHS_RU[d.month]} {d.year}'

def _fmt_date_short(d):
    return d.strftime('%d.%m.%Y')

def _run(para, text, bold=False, italic=False, underline=False,
         color=None, size=12, name='Times New Roman'):
    r = para.add_run(text)
    r.font.name  = name
    r.font.size  = Pt(size)
    r.bold       = bold
    r.italic     = italic
    r.underline  = underline
    if color:
        r.font.color.rgb = RGBColor(*color)
    try:
        r._element.rPr.rFonts.set(qn('w:cs'), name)
        r._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    except Exception:
        pass
    return r

def _para(doc, first_indent=None, left_indent=None,
          align=WD_ALIGN_PARAGRAPH.JUSTIFY,
          space_before=0, space_after=0, line_spacing=14):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.alignment    = align
    fmt.space_before = Pt(space_before)
    fmt.space_after  = Pt(space_after)
    fmt.line_spacing = Pt(line_spacing)
    if first_indent is not None:
        fmt.first_line_indent = Cm(first_indent)
    if left_indent is not None:
        fmt.left_indent = Cm(left_indent)
    return p


def notice_export_word(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    items  = list(notice.items.all())

    doc = Document()

    # ── Страница ──────────────────────────────
    sec                = doc.sections[0]
    sec.page_width     = Mm(210)
    sec.page_height    = Mm(297)
    sec.left_margin    = Cm(3.0)
    sec.right_margin   = Cm(1.5)
    sec.top_margin     = Cm(2.0)
    sec.bottom_margin  = Cm(2.0)

    # Убираем колонтитулы
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False
    for hf in (sec.header, sec.footer):
        for p in hf.paragraphs:
            p.clear()

    # ── Базовый стиль ─────────────────────────
    ns            = doc.styles['Normal']
    ns.font.name  = 'Times New Roman'
    ns.font.size  = Pt(12)
    ns.font.bold  = False
    ns.font.color.rgb = RGBColor(0, 0, 0)

    # ── Вспомогательные функции ───────────────

    BLACK = RGBColor(0, 0, 0)

    def run(para, text, bold=False, underline=False,
            size=12, name='Times New Roman'):
        """Добавляет run: шрифт всегда чёрный, не курсив."""
        r = para.add_run(text)
        r.font.name      = name
        r.font.size      = Pt(size)
        r.bold           = bold
        r.italic         = False
        r.underline      = underline
        r.font.color.rgb = BLACK
        # Кириллический и восточноазиатский шрифт тоже Times New Roman
        try:
            rPr = r._element.get_or_add_rPr()
            rFonts = rPr.get_or_add_rFonts()
            rFonts.set(qn('w:cs'),      name)
            rFonts.set(qn('w:eastAsia'), name)
        except Exception:
            pass
        return r

    def para(align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             first_indent=None, left_indent=None,
             space_before=0, space_after=0, line_spacing=14):
        p   = doc.add_paragraph()
        fmt = p.paragraph_format
        fmt.alignment    = align
        fmt.space_before = Pt(space_before)
        fmt.space_after  = Pt(space_after)
        fmt.line_spacing = Pt(line_spacing)
        if first_indent is not None:
            fmt.first_line_indent = Cm(first_indent)
        if left_indent is not None:
            fmt.left_indent = Cm(left_indent)
        return p

    def fmt_date_long(d):
        """12 мая 2025"""
        months = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f'{d.day} {months[d.month]} {d.year}'

    def fmt_date_short(d):
        """12.05.2025"""
        return d.strftime('%d.%m.%Y')

    PLACEHOLDER = '__.__.____'
    PLACEHOLDER_LONG = '__ ________ ____'

    # ══════════════════════════════════════════
    # ЗАГОЛОВОК
    # ══════════════════════════════════════════
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    run(p,
        'ИЗВЕЩЕНИЕ О ПРОВЕДЕНИИ СОБРАНИЯ О СОГЛАСОВАНИИ\n'
        'МЕСТОПОЛОЖЕНИЯ ГРАНИЦ ЗЕМЕЛЬНЫХ УЧАСТКОВ',
        bold=False)

    # ══════════════════════════════════════════
    # ВВОДНЫЙ АБЗАЦ
    # ══════════════════════════════════════════
    p = para(first_indent=1.25, space_before=6)
    run(p, 'Филиалом Публично-правовой компании «')
    run(p, 'Роскадастр', underline=True)
    run(p,
        '» по Луганской Народной Республике, юридический адрес: '
        '291011, РФ, ЛНР, г. Луганск, ул. Шелкового, д. 1д, e-mail: ')
    run(p, 'filial1@81.kadastr.ru', underline=True)
    run(p,
        ', ОКПО 74750952, ОГРН 1227700700633, ИНН/КПП 7708410783/940343001, '
        'контактный телефон (0-22) 50 12 90, в лице заместителя директора '
        'филиала – главного технолога публично-правовой компании «')
    run(p, 'Роскадастр', underline=True)
    run(p,
        '» по Луганской Народной Республике ')
    run(p, 'Прядкина Гавриила Викторовича', underline=True)
    run(p,
        ' (доверенность от 09.01.2025) выполняются кадастровые работы '
        'в отношении земельных участков, расположенных по адресу '
        '(местонахождение):')

    # ══════════════════════════════════════════
    # СПИСОК ОБЪЕКТОВ (без договора)
    # ══════════════════════════════════════════
    for i, it in enumerate(items, 1):
        p = para(left_indent=1.25, first_indent=0,
                 space_before=2, space_after=2)
        parts = []
        if it.address:
            parts.append(it.address)
        if it.cadastral_number:
            parts.append(f'кадастровый номер {it.cadastral_number}')
        if it.customer:
            parts.append(f'заказчик: {it.customer}')
        line = ', '.join(parts) + (';' if parts else '')
        run(p, f'{i}.\t{line}')

    # ══════════════════════════════════════════
    # ДАТА СОБРАНИЯ  ← Дата согласования
    # ══════════════════════════════════════════
    p = para(first_indent=1.25, space_before=6)
    run(p,
        'Собрание по поводу согласования местоположения границ состоится '
        'по адресу: РФ, ЛНР, г. Луганск, ул. Оборонная, д. 101Б ')
    approval_str = (fmt_date_short(notice.approval_date)
                    if notice.approval_date else PLACEHOLDER)
    run(p, approval_str)
    run(p, ' в 10 часов 00 минут.')

    # ══════════════════════════════════════════
    # ОЗНАКОМЛЕНИЕ
    # ══════════════════════════════════════════
    p = para(first_indent=1.25, space_before=6)
    run(p,
        'С проектами межевых планов можно ознакомиться по адресу: '
        'г. Луганск, ул. Оборонная, д. 101Б.')

    # ══════════════════════════════════════════
    # СРОКИ ВОЗРАЖЕНИЙ  ← «с» = Дата выпуска, «по» = Дата согласования
    # ══════════════════════════════════════════
    p = para(first_indent=1.25, space_before=6)
    run(p,
        'Требования о проведении согласования местоположения границ земельных '
        'участков на местности и обоснованные возражения о местоположении '
        'границ после ознакомления с проектами межевых планов принимаются с ')
    # «с» — дата выпуска
    issue_str = (fmt_date_long(notice.issue_date)
                 if notice.issue_date else PLACEHOLDER_LONG)
    run(p, issue_str)
    run(p, ' по ')
    # «по» — дата согласования
    approval_long = (fmt_date_long(notice.approval_date)
                     if notice.approval_date else PLACEHOLDER_LONG)
    run(p, approval_long)
    run(p,
        ' по адресу: г. Луганск, ул. Оборонная, д. 101Б.')

    # ══════════════════════════════════════════
    # ДОКУМЕНТЫ
    # ══════════════════════════════════════════
    p = para(first_indent=1.25, space_before=6)
    run(p,
        'При проведении согласования местоположения границ при себе иметь '
        'документ, удостоверяющий личность, а также документы о правах на '
        'земельный участок (часть 12 статьи 39, часть 2 статьи 40 Федерального '
        'закона от 24 июля 2007 г. № 221-ФЗ «О кадастровой деятельности»).')

    # ══════════════════════════════════════════
    # СОХРАНЕНИЕ
    # ══════════════════════════════════════════
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    fname = f'izveshenie_{notice.pk}.docx'
    resp  = HttpResponse(
        buf.read(),
        content_type=(
            'application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document'
        )
    )
    resp['Content-Disposition'] = (
        f'attachment; filename="{fname}"; '
        f"filename*=UTF-8''{fname}"
    )
    return resp