/* notices.js */

let itemIndex = 0;
let editId    = null;

const CFG = () => window.NOTICES_CONFIG;


// ══════════════════════════════════════════════
// ОТКРЫТИЕ МОДАЛОК
// ══════════════════════════════════════════════

function openAddModal() {
  editId = null;
  document.getElementById('modalTitleText').textContent = 'Добавить извещение';
  document.getElementById('noticeForm').action = CFG().createUrl;
  clearForm();
  addItemRow(null);
  new bootstrap.Modal(document.getElementById('noticeModal')).show();
}

function openEditModal(pk) {
  editId = pk;
  document.getElementById('modalTitleText').textContent = 'Редактировать извещение';
  document.getElementById('noticeForm').action = CFG().editUrl.replace('0', pk);
  clearForm();

  fetch(CFG().getUrl.replace('0', pk))
    .then(r => r.json())
    .then(data => {
      document.getElementById('id_newspaper').value     = data.newspaper     || '';
      document.getElementById('id_issue_date').value    = data.issue_date    || '';
      document.getElementById('id_approval_date').value = data.approval_date || '';

      if (data.items && data.items.length) {
        data.items.forEach(it => addItemRow(it));
      } else {
        addItemRow(null);
      }
      new bootstrap.Modal(document.getElementById('noticeModal')).show();
    })
    .catch(err => alert('Ошибка загрузки: ' + err));
}

// ══════════════════════════════════════════════
// ОТКРЫТИЕ МОДАЛКИ РЕДАКТИРОВАНИЯ
// ══════════════════════════════════════════════

function openEditModal(pk) {
  editId = pk;
  document.getElementById('modalTitleText').textContent = 'Редактировать извещение';
  document.getElementById('noticeForm').action = CFG().editUrl.replace('0', pk);

  // Сначала очищаем — это сбросит itemIndex и management-поля
  clearForm();

  fetch(CFG().getUrl.replace('0', pk))
    .then(r => r.json())
    .then(data => {
      document.getElementById('id_newspaper').value     = data.newspaper     || '';
      document.getElementById('id_issue_date').value    = data.issue_date    || '';
      document.getElementById('id_approval_date').value = data.approval_date || '';

      if (data.items && data.items.length) {
        data.items.forEach(it => addItemRow(it));
      } else {
        addItemRow(null);
      }

      new bootstrap.Modal(document.getElementById('noticeModal')).show();
    })
    .catch(err => alert('Ошибка загрузки: ' + err));
}

// ══════════════════════════════════════════════
// ОЧИСТКА
// ══════════════════════════════════════════════

function clearForm() {
  ['id_newspaper', 'id_issue_date', 'id_approval_date'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('itemsContainer').innerHTML = '';
  document.getElementById('formErrors').classList.add('d-none');
  document.getElementById('formErrors').innerHTML = '';
  itemIndex = 0;

  // Полностью удаляем все скрытые management-поля formset,
  // чтобы они пересоздались с нуля при syncManagement()
  const form = document.getElementById('noticeForm');
  ['TOTAL_FORMS', 'INITIAL_FORMS', 'MIN_NUM_FORMS', 'MAX_NUM_FORMS'].forEach(n => {
    const field = form.querySelector(`[name="items-${n}"]`);
    if (field) field.remove();
  });

  syncManagement();
}

// ══════════════════════════════════════════════
// ДОБАВИТЬ СТРОКУ ОБЪЕКТА
// ══════════════════════════════════════════════

function addItemRow(data) {
  const container = document.getElementById('itemsContainer');
  const idx       = itemIndex++;

  const itemId    = data?.id               ?? '';
  const address   = data?.address          ?? '';
  const fiasId    = data?.fias_id          ?? '';
  const region    = data?.region           ?? '';
  const city      = data?.city             ?? '';
  const street    = data?.street           ?? '';
  const house     = data?.house            ?? '';
  const cadastral = data?.cadastral_number ?? '';
  const customer  = data?.customer         ?? '';
  const contract  = data?.contract         ?? '';
  const order     = data?.order            ?? idx;

  const card       = document.createElement('div');
  card.className   = 'item-row card mb-2';
  card.dataset.idx = idx;

  card.innerHTML = `
    <div class="card-header d-flex justify-content-between align-items-center py-1 px-2"
         style="background:#f8f9fa; cursor:pointer"
         onclick="toggleItemRow(this)">
      <span class="item-row-title fw-semibold small text-muted">
        Объект ${idx + 1}
        <span class="item-row-preview ms-1 text-dark"></span>
      </span>
      <div class="d-flex gap-2 align-items-center">
        <i class="bi bi-chevron-down toggle-icon"></i>
        <button type="button"
                class="btn btn-outline-danger btn-sm py-0 px-1"
                onclick="removeItemRow(event, this)"
                title="Удалить объект">
          <i class="bi bi-trash"></i>
        </button>
      </div>
    </div>

    <div class="card-body item-row-body p-2">
      <input type="hidden" name="items-${idx}-id"      value="${itemId}">
      <input type="hidden" name="items-${idx}-order"   value="${order}"  class="order-field">
      <input type="hidden" name="items-${idx}-fias_id" value=""          class="fias-id-field">
      <input type="hidden" name="items-${idx}-region"  value=""          class="region-field">
      <input type="hidden" name="items-${idx}-city"    value=""          class="city-field">
      <input type="hidden" name="items-${idx}-street"  value=""          class="street-field">
      <input type="hidden" name="items-${idx}-house"   value=""          class="house-field">

      <div class="row g-2">
        <div class="col-12">
          <label class="form-label form-label-sm mb-1">
            <i class="bi bi-geo-alt me-1"></i>Адрес
          </label>
          <div style="position:relative">
            <input type="text"
                   name="items-${idx}-address"
                   class="form-control form-control-sm address-autocomplete"
                   placeholder="Начните вводить адрес..."
                   autocomplete="off">
            <div class="autocomplete-dropdown"></div>
          </div>
        </div>

        <div class="col-12 col-sm-6">
          <label class="form-label form-label-sm mb-1">Кадастровый номер</label>
          <input type="text"
                 name="items-${idx}-cadastral_number"
                 class="form-control form-control-sm cadastral-input"
                 placeholder="__:__:_______:______"
                 maxlength="23"
                 autocomplete="off">
        </div>

        <div class="col-12 col-sm-6">
          <label class="form-label form-label-sm mb-1">Заказчик</label>
          <input type="text"
                 name="items-${idx}-customer"
                 class="form-control form-control-sm customer-field"
                 placeholder="Наименование заказчика">
        </div>

        <div class="col-12 col-sm-6">
          <label class="form-label form-label-sm mb-1">Договор</label>
          <input type="text"
                 name="items-${idx}-contract"
                 class="form-control form-control-sm"
                 placeholder="Номер договора">
        </div>
      </div>
    </div>`;

  container.appendChild(card);

  // Безопасно устанавливаем значения через .value
  const body = card.querySelector('.item-row-body');
  body.querySelector(`[name="items-${idx}-address"]`).value          = address;
  body.querySelector(`[name="items-${idx}-cadastral_number"]`).value = cadastral;
  body.querySelector(`[name="items-${idx}-customer"]`).value         = customer;
  body.querySelector(`[name="items-${idx}-contract"]`).value         = contract;
  body.querySelector('.fias-id-field').value = fiasId;
  body.querySelector('.region-field').value  = region;
  body.querySelector('.city-field').value    = city;
  body.querySelector('.street-field').value  = street;
  body.querySelector('.house-field').value   = house;

  updateRowPreview(card);

  body.querySelectorAll('input[type="text"]').forEach(inp => {
    inp.addEventListener('input', () => updateRowPreview(card));
  });

  // ФИАС
  const addrInput = body.querySelector('.address-autocomplete');
  const dropdown  = body.querySelector('.autocomplete-dropdown');
  setupAutocomplete(addrInput, dropdown, card);

  // Маска кадастрового номера
  const cadastralInput = body.querySelector('.cadastral-input');
  if (cadastralInput) setupCadastralMask(cadastralInput);

  syncManagement();
}


// ══════════════════════════════════════════════
// ПРЕВЬЮ В ЗАГОЛОВКЕ КАРТОЧКИ
// ══════════════════════════════════════════════

function updateRowPreview(card) {
  const body      = card.querySelector('.item-row-body');
  const preview   = card.querySelector('.item-row-preview');
  const address   = body.querySelector('.address-autocomplete')?.value || '';
  const cadastral = body.querySelector('.cadastral-input')?.value      || '';
  const customer  = body.querySelector('.customer-field')?.value       || '';
  const parts     = [address, cadastral, customer].filter(Boolean);
  preview.textContent = parts.length ? ('— ' + parts.slice(0, 2).join(', ')) : '';
}


// ══════════════════════════════════════════════
// СВОРАЧИВАНИЕ КАРТОЧЕК
// ══════════════════════════════════════════════

function toggleItemRow(header) {
  const card   = header.closest('.item-row');
  const body   = card.querySelector('.item-row-body');
  const icon   = header.querySelector('.toggle-icon');
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : '';
  icon.className     = isOpen
    ? 'bi bi-chevron-right toggle-icon'
    : 'bi bi-chevron-down toggle-icon';
}

function collapseAll() {
  document.querySelectorAll('#itemsContainer .item-row').forEach(card => {
    card.querySelector('.item-row-body').style.display = 'none';
    card.querySelector('.toggle-icon').className = 'bi bi-chevron-right toggle-icon';
  });
}

function expandAll() {
  document.querySelectorAll('#itemsContainer .item-row').forEach(card => {
    card.querySelector('.item-row-body').style.display = '';
    card.querySelector('.toggle-icon').className = 'bi bi-chevron-down toggle-icon';
  });
}


// ══════════════════════════════════════════════
// УДАЛИТЬ СТРОКУ
// ══════════════════════════════════════════════

function removeItemRow(event, btn) {
  event.stopPropagation();
  btn.closest('.item-row').remove();
  renumberRows();
  syncManagement();
}

function renumberRows() {
  document.querySelectorAll('#itemsContainer .item-row').forEach((card, i) => {
    const title = card.querySelector('.item-row-title');
    // Обновляем только текстовый узел, не трогая .item-row-preview
    title.firstChild.textContent = `Объект ${i + 1} `;
  });
}


// ══════════════════════════════════════════════
// MANAGEMENT FORM
// ══════════════════════════════════════════════

function syncManagement() {
  const form = document.getElementById('noticeForm');

  // Значения по умолчанию: INITIAL_FORMS всегда 0,
  // чтобы Django не считал строки «уже существующими»
  const defaults = {
    'items-TOTAL_FORMS':   '0',
    'items-INITIAL_FORMS': '0',
    'items-MIN_NUM_FORMS': '0',
    'items-MAX_NUM_FORMS': '1000',
  };

  Object.entries(defaults).forEach(([name, def]) => {
    let field = form.querySelector(`[name="${name}"]`);
    if (!field) {
      field       = document.createElement('input');
      field.type  = 'hidden';
      field.name  = name;
      field.value = def;
      form.appendChild(field);
    }
  });

  // Обновляем только TOTAL_FORMS по реальному числу строк
  const rows = document.querySelectorAll('#itemsContainer .item-row');
  form.querySelector('[name="items-TOTAL_FORMS"]').value = rows.length;
}


// ══════════════════════════════════════════════
// МАСКА КАДАСТРОВОГО НОМЕРА __:__:_______:______
// ══════════════════════════════════════════════

function setupCadastralMask(input) {
  const SEGMENTS  = [2, 2, 7, 6];
  const SEP       = ':';
  const MAX_DIGITS = SEGMENTS.reduce((a, b) => a + b, 0); // 17

  function digitsOnly(str) {
    return str.replace(/\D/g, '');
  }

  function applyMask(digits) {
    let result = '';
    let pos    = 0;
    for (let s = 0; s < SEGMENTS.length; s++) {
      const chunk = digits.slice(pos, pos + SEGMENTS[s]);
      if (!chunk) break;
      if (s > 0) result += SEP;
      result += chunk;
      pos += SEGMENTS[s];
    }
    return result;
  }

  input.addEventListener('input', function () {
    // Запоминаем сколько цифр было до курсора
    const selStart    = input.selectionStart;
    const digitsBefore = digitsOnly(input.value.slice(0, selStart)).length;

    // Применяем маску
    const digits    = digitsOnly(input.value).slice(0, MAX_DIGITS);
    const formatted = applyMask(digits);
    input.value     = formatted;

    // Восстанавливаем позицию курсора
    let newPos = 0;
    let count  = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (formatted[i] !== SEP) count++;
      if (count === digitsBefore) { newPos = i + 1; break; }
      newPos = formatted.length;
    }
    input.setSelectionRange(newPos, newPos);
  });

  // Блокируем нецифровые символы
  input.addEventListener('keydown', function (e) {
    const passthrough = [
      'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight',
      'ArrowUp', 'ArrowDown', 'Tab', 'Home', 'End',
    ];
    if (passthrough.includes(e.key)) return;
    if (e.ctrlKey || e.metaKey) return;
    if (!/^\d$/.test(e.key)) e.preventDefault();
  });

  // Обрабатываем вставку из буфера
  input.addEventListener('paste', function (e) {
    e.preventDefault();
    const pasted  = (e.clipboardData || window.clipboardData).getData('text');
    const digits  = digitsOnly(input.value + pasted).slice(0, MAX_DIGITS);
    input.value   = applyMask(digits);
  });
}


// ══════════════════════════════════════════════
// ФИАС АВТОДОПОЛНЕНИЕ
// ══════════════════════════════════════════════

function setupAutocomplete(input, dropdown, card) {
  let timer = null;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 3) { hideDropdown(dropdown); return; }

    timer = setTimeout(() => {
      fetch(CFG().fiasUrl + '?q=' + encodeURIComponent(q))
        .then(r => r.json())
        .then(data => renderDropdown(data.suggestions || [], dropdown, input, card))
        .catch(() => hideDropdown(dropdown));
    }, 300);
  });

  document.addEventListener('click', e => {
    if (!card.contains(e.target)) hideDropdown(dropdown);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { hideDropdown(dropdown); return; }

    const items  = dropdown.querySelectorAll('.autocomplete-item');
    if (!items.length) return;

    const active = dropdown.querySelector('.autocomplete-item.active');
    let idx      = [...items].indexOf(active);

    if (e.key === 'ArrowDown') { e.preventDefault(); idx = (idx + 1) % items.length; }
    if (e.key === 'ArrowUp')   { e.preventDefault(); idx = (idx - 1 + items.length) % items.length; }

    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (active) active.classList.remove('active');
      items[idx].classList.add('active');
      items[idx].scrollIntoView({ block: 'nearest' });
    }

    if (e.key === 'Enter') {
      const a = dropdown.querySelector('.autocomplete-item.active');
      if (a) { e.preventDefault(); a.click(); }
    }
  });
}

function renderDropdown(suggestions, dropdown, input, card) {
  dropdown.innerHTML = '';
  if (!suggestions.length) { hideDropdown(dropdown); return; }

  suggestions.forEach(s => {
    const item       = document.createElement('div');
    item.className   = 'autocomplete-item';
    item.textContent = s.value;

    item.addEventListener('mousedown', e => e.preventDefault());
    item.addEventListener('click', () => {
      input.value = s.value;
      card.querySelector('.fias-id-field').value = s.fias_id || '';
      card.querySelector('.region-field').value  = s.region  || '';
      card.querySelector('.city-field').value    = s.city    || '';
      card.querySelector('.street-field').value  = s.street  || '';
      card.querySelector('.house-field').value   = s.house   || '';
      hideDropdown(dropdown);
      updateRowPreview(card);
    });
    dropdown.appendChild(item);
  });

  dropdown.style.display = 'block';
}

function hideDropdown(dropdown) {
  dropdown.style.display = 'none';
  dropdown.innerHTML     = '';
}


// ══════════════════════════════════════════════
// САБМИТ
// ══════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('noticeForm');
  if (!form) return;

  form.addEventListener('submit', e => {
    e.preventDefault();
    fetch(form.action, {
      method:  'POST',
      body:    new FormData(form),
      headers: { 'X-CSRFToken': CFG().csrfToken },
    })
    .then(r => {
      if (r.redirected || r.ok) window.location.reload();
      else return r.json().then(showErrors);
    })
    .catch(() => window.location.reload());
  });
});

function showErrors(err) {
  const div  = document.getElementById('formErrors');
  const msgs = [];
  Object.entries(err.errors || {}).forEach(([k, v]) => {
    const lines = Array.isArray(v) ? v.flat() : [v];
    msgs.push(`<b>${k}:</b> ${lines.join(', ')}`);
  });
  div.innerHTML = msgs.join('<br>') || 'Проверьте форму';
  div.classList.remove('d-none');
  div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}


// ══════════════════════════════════════════════
// УДАЛЕНИЕ
// ══════════════════════════════════════════════

function confirmDelete(pk) {
  document.getElementById('deleteForm').action =
    CFG().deleteUrl.replace('0', pk);
  new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

  // ── Импорт из Excel ───────────────────────────────────────────────────────

function doImport() {
  const fileInput = document.getElementById('importFile');
  const resultDiv = document.getElementById('importResult');
  const btn       = document.getElementById('importBtn');
  const spinner   = document.getElementById('importSpinner');

  if (!fileInput.files.length) {
    alert('Выберите файл Excel');
    return;
  }

  const formData = new FormData();
  formData.append('excel_file', fileInput.files[0]);

  // Показываем спиннер, блокируем кнопку
  btn.disabled = true;
  spinner.classList.remove('d-none');
  resultDiv.classList.add('d-none');

  fetch(window.NOTICES_CONFIG.importUrl, {
    method: 'POST',
    headers: { 'X-CSRFToken': window.NOTICES_CONFIG.csrfToken },
    body: formData,
  })
    .then(r => r.json())
    .then(data => {
      resultDiv.classList.remove('d-none');
      if (data.success) {
        resultDiv.className = 'alert alert-success mb-3';
        resultDiv.innerHTML =
          `<i class="bi bi-check-circle me-1"></i>${data.message}` +
          `<br><small class="text-muted">Страница обновится через секунду…</small>`;
        setTimeout(() => location.reload(), 1500);
      } else {
        resultDiv.className = 'alert alert-danger mb-3';
        resultDiv.innerHTML =
          `<i class="bi bi-x-circle me-1"></i>${data.error}`;
      }
    })
    .catch(err => {
      resultDiv.classList.remove('d-none');
      resultDiv.className = 'alert alert-danger mb-3';
      resultDiv.innerHTML = `<i class="bi bi-x-circle me-1"></i>Ошибка: ${err}`;
    })
    .finally(() => {
      btn.disabled = false;
      spinner.classList.add('d-none');
    });
}