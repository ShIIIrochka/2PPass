document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const passwordChangeForm = document.getElementById('passwordChangeForm');
    const profileForm = document.getElementById('profileForm');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (passwordChangeForm) {
        passwordChangeForm.addEventListener('submit', handlePasswordChange);
    }

    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }

    function showMessage(elementId, message, isError = false) {
        const messageEl = document.getElementById(elementId);
        if (!messageEl) return;
        messageEl.textContent = message;
        messageEl.className = 'form-message' + (isError ? ' is-error' : ' is-success');
        messageEl.classList.remove('hidden');
    }

    function hideMessage(elementId) {
        const messageEl = document.getElementById(elementId);
        if (messageEl) {
            messageEl.classList.add('hidden');
        }
    }

    async function handleLogin(e) {
        e.preventDefault();
        hideMessage('loginMessage');

        const formData = new FormData(loginForm);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const response = await fetch('/api/users/login/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                if (data.password_changed === false) {
                    window.location.href = '/password-change/';
                } else {
                    window.location.href = '/users/';
                }
            } else {
                const errorMsg = data.error || data.non_field_errors?.[0] || 'Ошибка входа';
                showMessage('loginMessage', errorMsg, true);
            }
        } catch (error) {
            showMessage('loginMessage', 'Ошибка соединения', true);
        }
    }

    async function handlePasswordChange(e) {
        e.preventDefault();
        hideMessage('passwordMessage');

        const formData = new FormData(passwordChangeForm);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const response = await fetch('/api/users/password-change/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('passwordMessage', 'Пароль успешно изменен', false);
                const profileSection = document.getElementById('profileSection');
                if (profileSection) {
                    profileSection.classList.remove('hidden');
                }
                passwordChangeForm.style.display = 'none';
            } else {
                const errorMsg = data.error || data.old_password?.[0] || data.new_password_confirm?.[0] || 'Ошибка смены пароля';
                showMessage('passwordMessage', errorMsg, true);
            }
        } catch (error) {
            showMessage('passwordMessage', 'Ошибка соединения', true);
        }
    }

    async function handleProfileUpdate(e) {
        e.preventDefault();
        hideMessage('profileMessage');

        const formData = new FormData(profileForm);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const response = await fetch('/api/users/profile/', {
                method: 'PATCH',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('profileMessage', 'Профиль сохранен', false);
                setTimeout(() => {
                    window.location.href = '/users/';
                }, 1000);
            } else {
                const errorMsg = data.error || 'Ошибка сохранения профиля';
                showMessage('profileMessage', errorMsg, true);
            }
        } catch (error) {
            showMessage('profileMessage', 'Ошибка соединения', true);
        }
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            try {
                await fetch('/api/users/logout/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                });
                window.location.href = '/login/';
            } catch (error) {
                window.location.href = '/login/';
            }
        });
    }
});
