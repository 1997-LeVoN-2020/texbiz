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
  form.addEventListener('submit', (event) => {
    event.preventDefault();

    const name = form.querySelector('#name');
    const phone = form.querySelector('#phone');
    const object = form.querySelector('#object');
    const agree = form.querySelector('#agree');

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

    statusEl.textContent = 'Заявка отправлена. Мы свяжемся с вами в ближайшее время.';
    statusEl.classList.add('success');
    form.reset();
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

if (quizForm && quizResult) {
  quizForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const type = quizForm.querySelector('#quiz-type').value;
    const rooms = Number(quizForm.querySelector('#quiz-rooms').value);
    const modules = quizForm.querySelectorAll('input[type="checkbox"]:checked').length;

    if (!type || !rooms || modules === 0) {
      quizResult.innerHTML = '<h3>Недостаточно данных для расчета</h3><p>Выберите тип объекта, количество номеров и минимум один модуль.</p>';
      return;
    }

    const typeMultiplier = {
      hotel: 1.15,
      mini: 0.9,
      apart: 1.05,
      chain: 1.35,
    };

    const base = 120000;
    const roomsPart = rooms * 1700;
    const modulesPart = modules * 45000;
    const total = Math.round((base + roomsPart + modulesPart) * (typeMultiplier[type] || 1));

    const start = Math.round(total * 0.85);
    const end = Math.round(total * 1.2);
    const startFormatted = start.toLocaleString('ru-RU');
    const endFormatted = end.toLocaleString('ru-RU');
    const launchDays = rooms <= 40 ? '5-9 дней' : rooms <= 120 ? '8-14 дней' : '14-25 дней';

    quizResult.innerHTML = `<h3>Ориентировочный бюджет: ${startFormatted} - ${endFormatted} руб.</h3><p>Предварительный срок запуска: ${launchDays}. Точный расчет подготовим после экспресс-аудита объекта и проверки интеграций.</p><a class="btn btn-primary" href="#contacts">Получить точную смету</a>`;
  });
}
