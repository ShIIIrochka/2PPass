/* -*- coding: utf-8 -*- */

/*
 Скрипт для копирования пароля в админке.
 - Ищет элементы с классом `pw-copy-btn` и атрибутом `data-url`.
 - По клику делает POST на указанный URL (использует CSRF из cookie),
   получает JSON { password: "..." } и пытается записать пароль в буфер обмена.
 - Тексты статуса на русском, поведение минимальное и предсказуемое.
*/

/* global document, window, fetch, navigator, console */

(function () {
  'use strict';

  if (window._pw_copy_loaded) {
    return;
  }
  window._pw_copy_loaded = true;

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop()) : '';
  }

  function findStatusElement(btn) {
    // ожидаем рядом <span class="pw-copy-status">, иначе создаём
    var next = btn.nextElementSibling;
    if (next && next.classList && next.classList.contains('pw-copy-status')) {
      return next;
    }
    var span = document.createElement('span');
    span.className = 'pw-copy-status';
    span.style.marginLeft = '8px';
    span.style.color = '#444';
    btn.parentNode.insertBefore(span, btn.nextSibling);
    return span;
  }

  function setTransientStatus(el, text, ms) {
    if (!el) return;
    el.textContent = text || '';
    if (ms) {
      setTimeout(function () {
        el.textContent = '';
      }, ms);
    }
  }

  // Делегируем клики на документе — поддерживает динамическое добавление кнопок
  document.addEventListener('click', function (evt) {
    try {
      var target = evt.target;
      // closest может отсутствовать в очень старых браузерах, но для админки Django это нормально
      var btn = (typeof target.closest === 'function') ? target.closest('.pw-copy-btn') : null;
      if (!btn) return;

      evt.preventDefault();

      var url = btn.getAttribute('data-url');
      if (!url) {
        return;
      }

      var statusEl = findStatusElement(btn);
      btn.disabled = true;
      setTransientStatus(statusEl, 'Запрос...');

      fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Accept': 'application/json'
        }
      })
        .then(function (resp) {
          // Ожидаем валидный JSON. Если backend вернёт ошибку, обработаем в catch.
          return resp.json();
        })
        .then(function (data) {
          if (data && data.password) {
            var pw = data.password;
            if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
              navigator.clipboard.writeText(pw).then(function () {
                setTransientStatus(statusEl, 'Скопировано', 2000);
              }, function () {
                // fallback
                console.log('Password:', pw);
                setTransientStatus(statusEl, 'Копирование не удалось — проверьте консоль', 3000);
              });
            } else {
              // Clipboard API отсутствует — выводим в консоль как последний вариант
              console.log('Password:', pw);
              setTransientStatus(statusEl, 'Буфер недоступен — проверьте консоль', 3000);
            }
          } else {
            setTransientStatus(statusEl, (data && data.error) ? data.error : 'Нет пароля', 2500);
          }
        })
        .catch(function () {
          setTransientStatus(statusEl, 'Ошибка', 2500);
        })
        .finally(function () {
          btn.disabled = false;
        });
    } catch (e) {
      // На уровне UI — просто логируем, чтобы не ломать страницу.
      try { console.error(e); } catch (ignore) {}
    }
  }, false);
})();
