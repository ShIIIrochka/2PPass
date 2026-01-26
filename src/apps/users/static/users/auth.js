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

    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(`${name}=`)) {
                return decodeURIComponent(trimmed.substring(name.length + 1));
            }
        }
        return '';
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

        const email = loginForm.querySelector('[name=email]').value;
        const password = loginForm.querySelector('[name=password]').value;
        const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : getCookie('csrftoken');

        const requestData = {
            email: email,
            password: password,
        };

        console.log('Sending login request:', { email, password: '***' });
        console.log('Request data:', JSON.stringify(requestData));

        try {
            const response = await fetch('/api/users/login/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrfToken && { 'X-CSRFToken': csrfToken }),
                },
                body: JSON.stringify(requestData),
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));

            const data = await response.json();
            console.log('Response data:', data);

            if (response.ok) {
                if (data.password_changed === false) {
                    window.location.href = '/login/password-change/';
                } else {
                    window.location.href = '/vaults/';
                }
            } else {
                const errorMsg = data.detail || data.error || data.non_field_errors?.[0] || 'Ошибка входа';
                console.error('Login error:', errorMsg, data);
                showMessage('loginMessage', errorMsg, true);
            }
        } catch (error) {
            console.error('Login request error:', error);
            showMessage('loginMessage', 'Ошибка соединения: ' + error.message, true);
        }
    }

    async function handlePasswordChange(e) {
        e.preventDefault();
        hideMessage('passwordMessage');

        const formData = new FormData(passwordChangeForm);
        const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : getCookie('csrftoken');

        if (!csrfToken) {
            showMessage('passwordMessage', 'Ошибка: CSRF token не найден. Перезагрузите страницу.', true);
            return;
        }

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
                
                setTimeout(() => {
                    window.location.href = '/vaults/';
                }, 2000);
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
