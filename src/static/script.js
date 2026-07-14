// URL of the Python (Flask/Passenger) form handler. The Python app is
// deployed at the domain root (same directory as the static site), so
// this is just the Flask route path — update it if that ever changes.
const MAIL_ENDPOINT = '/send';

const menuBtn = document.querySelector('.menu-btn');
const mainNav = document.querySelector('#main-nav');

if (menuBtn && mainNav) {
  menuBtn.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('is-open');
    menuBtn.setAttribute('aria-expanded', String(isOpen));
  });

  mainNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mainNav.classList.remove('is-open');
      menuBtn.setAttribute('aria-expanded', 'false');
    });
  });
}

const navDropdowns = document.querySelectorAll('.nav-item.has-dropdown');

function closeNavDropdowns() {
  navDropdowns.forEach((item) => {
    item.classList.remove('is-open');
    item.querySelector('.nav-dropdown-toggle')?.setAttribute('aria-expanded', 'false');
  });
}

navDropdowns.forEach((item) => {
  const toggle = item.querySelector('.nav-dropdown-toggle');
  if (!toggle) return;

  toggle.addEventListener('click', (event) => {
    event.stopPropagation();
    const isOpen = item.classList.contains('is-open');
    closeNavDropdowns();
    if (!isOpen) {
      item.classList.add('is-open');
      toggle.setAttribute('aria-expanded', 'true');
    }
  });
});

document.addEventListener('click', closeNavDropdowns);

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeNavDropdowns();
  }
});

const revealItems = document.querySelectorAll('.reveal');

revealItems.forEach((item, index) => {
  item.style.setProperty('--reveal-order', String(index % 8));
});

if ('IntersectionObserver' in window && revealItems.length) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('is-visible'));
}

const hero = document.querySelector('.hero');

if (hero && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
  hero.addEventListener('mousemove', (event) => {
    const rect = hero.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 12;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 10;
    hero.style.setProperty('transform', `translate3d(${x * -0.25}px, ${y * -0.2}px, 0)`);
  });

  hero.addEventListener('mouseleave', () => {
    hero.style.setProperty('transform', 'translate3d(0, 0, 0)');
  });
}

const form = document.querySelector('#lead-form');
const statusEl = document.querySelector('#form-status');

function isValidPhone(value) {
  const digits = value.replace(/\D/g, '');
  return digits.length >= 10;
}

if (form && statusEl) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const name = form.querySelector('#name');
    const phone = form.querySelector('#phone');
    const object = form.querySelector('#object');
    const agree = form.querySelector('#agree');
    const submitBtn = form.querySelector('button[type="submit"]');

    statusEl.className = 'form-status';

    if (!name.value.trim() || !phone.value.trim() || !object.value || !agree.checked) {
      statusEl.textContent = 'Заполните обязательные поля и подтвердите согласие.';
      statusEl.classList.add('error');
      return;
    }

    if (!isValidPhone(phone.value)) {
      statusEl.textContent = 'Проверьте формат телефона.';
      statusEl.classList.add('error');
      return;
    }

    submitBtn.disabled = true;
    statusEl.textContent = 'Отправляем заявку...';

    try {
      const response = await fetch(MAIL_ENDPOINT, {
        method: 'POST',
        body: new FormData(form),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.error || 'send_failed');
      }

      statusEl.textContent = 'Заявка отправлена. Мы свяжемся с вами в ближайшее время.';
      statusEl.classList.add('success');
      form.reset();
    } catch (error) {
      statusEl.textContent = 'Не удалось отправить заявку. Позвоните нам напрямую по указанному телефону.';
      statusEl.classList.add('error');
    } finally {
      submitBtn.disabled = false;
    }
  });
}

const segmentTabs = document.querySelectorAll('.segment-tab');
const segmentPanels = document.querySelectorAll('.segment-panel');

if (segmentTabs.length && segmentPanels.length) {
  segmentTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.segmentTarget;

      segmentTabs.forEach((item) => {
        item.classList.remove('is-active');
        item.setAttribute('aria-selected', 'false');
      });

      segmentPanels.forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.segmentPanel === target);
      });

      tab.classList.add('is-active');
      tab.setAttribute('aria-selected', 'true');
    });
  });
}

const quizForm = document.querySelector('#quiz-form');
const quizResult = document.querySelector('#quiz-result');

// Relative setup effort per module -- 1C and the booking engine are full
// systems to configure, support is mostly ongoing (cheaper to onboard),
// so a flat per-checkbox price didn't reflect real scope differences.
const MODULE_PRICES = {
  '1c': 75000,
  kkt: 60000,
  srv: 155000,
  lock: 90000,
  ops: 15000,
  ota: 15000,
  booking: 100000,
};

if (quizForm && quizResult) {
  quizForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const type = quizForm.querySelector('#quiz-type').value;
    const roomsInput = quizForm.querySelector('#quiz-rooms');
    const rooms = Number(roomsInput.value);
    const roomsMin = Number(roomsInput.min);
    const roomsMax = Number(roomsInput.max);
    const checkedModules = Array.from(quizForm.querySelectorAll('input[type="checkbox"]:checked'));

    if (!type || !rooms || checkedModules.length === 0) {
      quizResult.innerHTML = '<h3>Недостаточно данных для расчета</h3><p>Выберите тип объекта, количество номеров и минимум один модуль.</p>';
      return;
    }

    if (rooms < roomsMin || rooms > roomsMax) {
      quizResult.innerHTML = `<h3>Проверьте количество номеров</h3><p>Введите значение от ${roomsMin} до ${roomsMax}.</p>`;
      return;
    }

    const typeMultiplier = {
      hotel: 1.15,
      mini: 0.9,
      apart: 1.05,
      chain: 1.35,
    };

    const moduleLines = checkedModules.map((checkbox) => ({
      label: checkbox.closest('label').textContent.trim(),
      price: MODULE_PRICES[checkbox.value] || 45000,
    }));
    const modulesPart = moduleLines.reduce((sum, line) => sum + line.price, 0);

    const base = 120000;
    const roomsPart = rooms * 1700;
    const multiplier = typeMultiplier[type] || 1;
    const total = Math.round((base + roomsPart + modulesPart) * multiplier);

    const start = Math.round(total * 0.85);
    const end = Math.round(total * 1.2);
    const startFormatted = start.toLocaleString('ru-RU');
    const endFormatted = end.toLocaleString('ru-RU');
    const launchDays = rooms <= 40 ? '5-9 дней' : rooms <= 120 ? '8-14 дней' : '14-25 дней';

    const breakdown = moduleLines
      .map((line) => `<li><span>${line.label}</span><span>≈ ${line.price.toLocaleString('ru-RU')} руб.</span></li>`)
      .join('');

    quizResult.innerHTML = `<h3>Ориентировочный бюджет: ${startFormatted} - ${endFormatted} руб.</h3><p>Предварительный срок запуска: ${launchDays}. Точный расчет подготовим после экспресс-аудита объекта и проверки интеграций.</p><p class="quiz-breakdown-label">Из чего складывается смета:</p><ul class="quiz-breakdown">${breakdown}</ul><a class="btn btn-primary" href="#contacts">Получить точную смету</a>`;
  });
}
