const state = {
  product: 'Сумка кожаная',
  productPrice: 4900,
  productColor: '#C8AA8A',
  productShape: 'bag',
  material: 'Натуральная кожа',
  materialExtra: 500,
  color: '#C8AA8A',
  colorName: 'Bleached Sand',
  engraving: '',
  engravingLine2: '',
  engravingFont: 'serif',
  engravingPlacement: 'По центру',
  fitting: 'Золото',
  extras: [],
  extrasTotal: 0,
};

function goStep(n) {
  document.querySelectorAll('.step-section').forEach(s => s.classList.remove('active'));
  document.getElementById('step' + n).classList.add('active');
  document.querySelectorAll('.sn-item').forEach((item, i) => {
    item.classList.remove('active', 'done');
    if (i + 1 < n) item.classList.add('done');
    if (i + 1 === n) item.classList.add('active');
  });
  updatePreview();
}

function selectProd(el, name, price, color, shape) {
  document.querySelectorAll('.prod-opt').forEach(e => e.classList.remove('sel'));
  el.classList.add('sel');
  state.product = name;
  state.productPrice = price;
  state.productColor = color;
  state.productShape = shape;
  document.getElementById('sumProd').textContent = name;
  updatePrice();
  updatePreview();
}

function selectMat(el, name, extra) {
  document.querySelectorAll('.mat-opt').forEach(e => e.classList.remove('sel'));
  el.classList.add('sel');
  state.material = name;
  state.materialExtra = extra === 'Базовая' ? 0 : parseInt(String(extra).replace('+', ''), 10) || 0;
  document.getElementById('sumMat').textContent = name;
  document.getElementById('priceMat').textContent = extra === 'Базовая' ? '—' : extra + ' сом';
  updatePrice();
}

function selectColor(el, name, hex) {
  document.querySelectorAll('.color-grid .color-option').forEach(e => e.classList.remove('sel'));
  el.classList.add('sel');
  state.color = hex;
  state.colorName = name;
  document.getElementById('colorName').textContent = name;
  document.getElementById('sumColor').textContent = name;
  updatePreview();
}

function selectFitting(el, name) {
  el.parentElement.querySelectorAll('.color-option').forEach(e => e.classList.remove('sel'));
  el.classList.add('sel');
  state.fitting = name;
}

function selectFont(el, font, name) {
  document.querySelectorAll('.fp').forEach(e => e.classList.remove('sel'));
  el.classList.add('sel');
  state.engravingFont = font;
  updatePreview();
}

function setEngravingPlacement(el) {
  state.engravingPlacement = el.value;
  updatePreview();
}

function updateEngraving() {
  const val = document.getElementById('engravingText').value;
  state.engraving = val;
  document.getElementById('charCount').textContent = val.length;
  document.getElementById('sumEng').textContent = val || '—';
  const engFee = state.engraving || state.engravingLine2;
  document.getElementById('priceEng').textContent = engFee ? '+400 сом' : '—';
  updatePreview();
  updatePrice();
}

function updateEngravingLine2(el) {
  state.engravingLine2 = el.value;
  const engFee = state.engraving || state.engravingLine2;
  document.getElementById('priceEng').textContent = engFee ? '+400 сом' : '—';
  document.getElementById('sumEng').textContent =
    [state.engraving, state.engravingLine2].filter(Boolean).join(' / ') || '—';
  updatePreview();
  updatePrice();
}

function toggleExtra(el, name, price) {
  el.classList.toggle('sel');
  if (el.classList.contains('sel')) {
    state.extras.push({ name, price });
  } else {
    state.extras = state.extras.filter(e => e.name !== name);
  }
  state.extrasTotal = state.extras.reduce((s, e) => s + e.price, 0);
  document.getElementById('sumExtras').textContent = state.extras.length
    ? state.extras.map(e => e.name).join(', ')
    : '—';
  document.getElementById('priceExtras').textContent = state.extrasTotal ? '+' + state.extrasTotal + ' сом' : '—';
  updatePrice();
}

function updatePrice() {
  const base = state.productPrice;
  const mat = state.materialExtra;
  const eng = state.engraving || state.engravingLine2 ? 400 : 0;
  const ext = state.extrasTotal;
  const total = base + mat + eng + ext;
  document.getElementById('priceBase').textContent = base.toLocaleString('ru') + ' сом';
  const elMat = document.getElementById('priceMat');
  if (elMat) elMat.textContent = mat ? '+' + mat + ' сом' : '—';
  const elEng = document.getElementById('priceEng');
  if (elEng) elEng.textContent = eng ? '+400 сом' : '—';
  const elEx = document.getElementById('priceExtras');
  if (elEx) elEx.textContent = ext ? '+' + ext + ' сом' : '—';
  document.getElementById('priceTotal').textContent = total.toLocaleString('ru') + ' сом';
}

function getShapeStyle(shape, color) {
  const styles = {
    bag: `width:80px;height:72px;border-radius:8px 8px 12px 12px;`,
    wallet: `width:88px;height:56px;border-radius:6px;`,
    bracelet: `width:72px;height:72px;border-radius:50%;border:14px solid ${color};background:transparent!important;box-shadow:0 4px 16px rgba(0,0,0,.25);`,
    belt: `width:96px;height:36px;border-radius:4px;`,
    keychain: `width:48px;height:72px;border-radius:24px 24px 8px 8px;`,
    cover: `width:72px;height:88px;border-radius:6px 12px 12px 6px;`,
  };
  return styles[shape] || `width:80px;height:80px;border-radius:8px;`;
}

function updatePreview() {
  const shape = document.getElementById('previewShape');
  const engraving = document.getElementById('previewEngraving');
  const shapeStyle = getShapeStyle(state.productShape, state.color);
  if (state.productShape === 'bracelet') {
    shape.style.cssText = shapeStyle;
    shape.style.borderColor = state.color;
    shape.style.background = 'transparent';
  } else {
    shape.style.cssText =
      shapeStyle + `background:${state.color};box-shadow:0 8px 24px rgba(0,0,0,.3);`;
  }
  let engText = state.engraving || '';
  if (state.engravingLine2) engText += '\n' + state.engravingLine2;
  engraving.textContent = engText;
  engraving.style.fontFamily = state.engravingFont;
  engraving.style.whiteSpace = 'pre';
  const place = state.engravingPlacement || 'По центру';
  if (place === 'По центру') {
    engraving.style.textAlign = 'center';
    engraving.style.alignSelf = 'center';
  } else if (place === 'Снизу справа') {
    engraving.style.textAlign = 'right';
    engraving.style.alignSelf = 'flex-end';
  } else if (place === 'Снизу слева') {
    engraving.style.textAlign = 'left';
    engraving.style.alignSelf = 'flex-start';
  } else {
    engraving.style.textAlign = 'center';
    engraving.style.alignSelf = 'center';
  }
}

function getCsrfToken() {
  const field = document.querySelector('#csrfForm input[name=csrfmiddlewaretoken]');
  if (field && field.value) return field.value;
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

async function addToCart() {
  const modal = document.getElementById('modalBg');
  const errEl = document.getElementById('modalError');
  const titleEl = document.getElementById('modalTitle');
  const textEl = document.getElementById('modalText');
  const cartBtn = document.getElementById('modalGoToCart');
  const setModalState = (ok, message) => {
    if (titleEl) titleEl.textContent = ok ? 'Добавлено в корзину!' : 'Не удалось добавить в корзину';
    if (textEl) {
      textEl.textContent = ok
        ? 'Ваш персональный аксессуар добавлен в корзину. Оформите заказ, и наш мастер приступит к работе.'
        : (message || 'Повторите попытку. Если проблема повторяется, обновите страницу.');
    }
    if (cartBtn) cartBtn.style.display = ok ? 'inline-block' : 'none';
  };
  setModalState(true, '');
  if (errEl) {
    errEl.style.display = 'none';
    errEl.textContent = '';
  }
  const url = window.PERSONALIZATION_ADD_URL;
  if (!url) {
    setModalState(false, 'Сервер не настроен');
    if (errEl) {
      errEl.textContent = 'Сервер не настроен';
      errEl.style.display = 'block';
    }
    modal.classList.add('show');
    return;
  }
  const payload = {
    productShape: state.productShape,
    product: state.product,
    productPrice: state.productPrice,
    material: state.material,
    color: state.color,
    colorName: state.colorName,
    fitting: state.fitting,
    engraving: state.engraving,
    engravingLine2: state.engravingLine2,
    engravingFont: state.engravingFont,
    engravingPlacement: state.engravingPlacement,
    extras: state.extras.map(e => ({ name: e.name, price: e.price })),
  };
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(payload),
      credentials: 'same-origin',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      let msg = 'Не удалось добавить в корзину';
      if (errEl) {
        const map = {
          invalid_json: 'Некорректные данные',
          invalid_shape: 'Некорректный тип изделия',
          invalid_material: 'Некорректный материал',
          invalid_extra: 'Некорректная опция',
          invalid_payload: 'Некорректный запрос',
          invalid_extras: 'Некорректные опции',
          no_active_category: 'Нет активной категории для сохранения персонального товара.',
          builder_product_missing:
            'Сервис временно недоступен. Выполните миграции БД (python manage.py migrate) и перезапустите сайт.',
        };
        msg = map[data.error];
        if (!msg && res.status === 403) {
          msg = 'Ошибка защиты (CSRF). Обновите страницу и попробуйте снова.';
        }
        errEl.textContent = msg || 'Не удалось добавить в корзину';
        errEl.style.display = 'block';
      }
      setModalState(false, msg);
      modal.classList.add('show');
      return;
    }
    const cartLink = document.getElementById('headerCartLink');
    if (cartLink && data.cart_count != null) {
      let badge = cartLink.querySelector('.badge-count');
      if (!badge && data.cart_count > 0) {
        badge = document.createElement('span');
        badge.className = 'badge-count';
        cartLink.appendChild(badge);
      }
      if (badge) {
        badge.textContent = String(data.cart_count);
        badge.style.display = data.cart_count > 0 ? '' : 'none';
      }
    }
    if (window.CART_DETAIL_URL) {
      const verify = await fetch(window.CART_DETAIL_URL, { credentials: 'same-origin' });
      const html = await verify.text();
      if (html.includes('cart-empty')) {
        const msg = 'Сервер ответил успешно, но корзина осталась пустой. Обновите страницу и попробуйте снова.';
        if (errEl) {
          errEl.textContent = msg;
          errEl.style.display = 'block';
        }
        setModalState(false, msg);
        modal.classList.add('show');
        return;
      }
    }
    setModalState(true, '');
    modal.classList.add('show');
  } catch (e) {
    setModalState(false, 'Нет соединения с сервером');
    if (errEl) {
      errEl.textContent = 'Нет соединения с сервером';
      errEl.style.display = 'block';
    }
    modal.classList.add('show');
  }
}

updatePreview();
updatePrice();
