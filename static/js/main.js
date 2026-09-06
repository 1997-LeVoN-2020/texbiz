/* ТЕХБИЗ — main.js. Без библиотек.
   Меню на узких экранах и отправка формы без перезагрузки.
   Без JavaScript всё работает обычным POST. */
(function () {
  'use strict';

  // --- Меню -----------------------------------------------------------------

  var header = document.querySelector('[data-header]');
  var toggle = document.querySelector('[data-menu-toggle]');
  var nav = document.querySelector('[data-nav]');

  function closeMenu() {
    if (!header) return;
    header.classList.remove('is-open');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
  }

  if (header && toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = header.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) closeMenu();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeMenu();
    });
    document.addEventListener('click', function (event) {
      if (!header.contains(event.target)) closeMenu();
    });
  }

  // --- Форма заявки --------------------------------------------------------

  var PHONE_HINT = 'Не удалось отправить заявку. Позвоните нам: +7 938 511-13-31.';

  function setFieldError(form, name, message) {
    var input = form.querySelector('[name="' + name + '"]');
    if (!input) return;
    var field = input.closest('.field, .consent');
    if (!field) return;
    field.classList.add('is-invalid');
    if (field.classList.contains('consent')) return;
    var error = field.querySelector('.field-error');
    if (!error) {
      error = document.createElement('p');
      error.className = 'field-error';
      field.appendChild(error);
    }
    error.textContent = message;
  }

  function clearErrors(form) {
    form.querySelectorAll('.is-invalid').forEach(function (el) { el.classList.remove('is-invalid'); });
    form.querySelectorAll('.field-error').forEach(function (el) { el.remove(); });
  }

  function validate(form) {
    var ok = true;
    var name = form.querySelector('[name="name"]');
    var phone = form.querySelector('[name="phone"]');
    var consent = form.querySelector('[name="consent"]');

    if (name && name.value.trim().length < 2) {
      setFieldError(form, 'name', 'Напишите имя.');
      ok = false;
    }
    if (phone) {
      var digits = phone.value.replace(/\D/g, '');
      if (digits.length < 10 || digits.length > 15) {
        setFieldError(form, 'phone', 'Проверьте номер телефона.');
        ok = false;
      }
    }
    if (consent && !consent.checked) {
      setFieldError(form, 'consent', '');
      ok = false;
    }
    return ok;
  }

  document.querySelectorAll('[data-lead-form]').forEach(function (form) {
    var status = form.querySelector('[data-form-status]');
    var button = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', function (event) {
      if (!window.fetch || !window.FormData) return; // обычная отправка
      event.preventDefault();
      clearErrors(form);
      status.className = 'form-status';
      status.textContent = '';

      if (!validate(form)) {
        status.textContent = 'Заполните обязательные поля и подтвердите согласие.';
        status.classList.add('is-error');
        return;
      }

      button.disabled = true;
      status.textContent = 'Отправляем…';

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch', 'Accept': 'application/json' },
        credentials: 'same-origin'
      })
        .then(function (response) {
          return response.json().then(function (data) { return { status: response.status, data: data }; });
        })
        .then(function (result) {
          var data = result.data || {};
          if (data.ok && data.redirect) {
            window.location.assign(data.redirect);
            return;
          }
          if (data.errors) {
            Object.keys(data.errors).forEach(function (key) { setFieldError(form, key, data.errors[key]); });
            status.textContent = 'Проверьте выделенные поля.';
          } else {
            status.textContent = data.error || PHONE_HINT;
          }
          status.classList.add('is-error');
          button.disabled = false;
        })
        .catch(function () {
          status.textContent = PHONE_HINT;
          status.classList.add('is-error');
          button.disabled = false;
        });
    });
  });
})();
