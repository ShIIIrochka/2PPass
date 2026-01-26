const passwordsTableBody = document.querySelector('#passwords-table tbody');
const passwordsEmpty = document.querySelector('#passwords-empty');
const refreshButton = document.querySelector('#refresh-passwords');
const addPasswordBtn = document.querySelector('#add-password-btn');
const vaultName = document.querySelector('#vault-name');

const vaultId = window.vaultId;
if (!vaultId || vaultId === 0) {
    alert('Ошибка: не указан ID хранилища');
    window.location.href = '/vaults/';
}
const apiUrl = `/api/vaults/${vaultId}/passwords/`;

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

let canEdit = false;

function renderPasswords(data) {
    const vault = data.vault;
    const passwords = data.passwords || [];
    canEdit = data.can_edit || false;
    
    vaultName.textContent = vault.name || 'Хранилище';
    
    const actionsHeader = document.querySelector('#actions-header');
    if (actionsHeader) {
        actionsHeader.style.display = canEdit ? '' : 'none';
    }
    
    if (addPasswordBtn) {
        addPasswordBtn.style.display = canEdit ? '' : 'none';
    }
    
    passwordsTableBody.innerHTML = '';
    if (!passwords.length) {
        passwordsEmpty.classList.remove('hidden');
        return;
    }
    passwordsEmpty.classList.add('hidden');

    passwords.forEach((pwd) => {
        const row = document.createElement('tr');
        const tags = (pwd.tags || []).join(', ') || '-';
        const urlCell = pwd.url ? `<a href="${pwd.url}" target="_blank" rel="noopener">${pwd.url}</a>` : '-';
        
        const passwordCell = document.createElement('td');
        passwordCell.className = 'password-cell';
        
        const passwordDisplay = document.createElement('span');
        passwordDisplay.className = 'password-hidden';
        passwordDisplay.textContent = '••••••••';
        passwordDisplay.dataset.password = pwd.password;
        
        const showBtn = document.createElement('button');
        showBtn.className = 'btn btn-small';
        showBtn.textContent = 'Показать';
        showBtn.onclick = () => togglePassword(passwordDisplay, showBtn);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-small';
        copyBtn.textContent = 'Копировать';
        copyBtn.onclick = () => copyPassword(pwd.password, copyBtn);
        
        passwordCell.appendChild(passwordDisplay);
        passwordCell.appendChild(showBtn);
        passwordCell.appendChild(copyBtn);
        
        const notes = pwd.notes || '-';
        
        const titleCell = document.createElement('td');
        titleCell.setAttribute('data-label', 'Название');
        titleCell.textContent = pwd.title;
        
        const loginCell = document.createElement('td');
        loginCell.setAttribute('data-label', 'Логин');
        loginCell.textContent = pwd.login;
        
        passwordCell.setAttribute('data-label', 'Пароль');
        
        const urlCellEl = document.createElement('td');
        urlCellEl.setAttribute('data-label', 'URL');
        urlCellEl.innerHTML = urlCell;
        
        const tagsCell = document.createElement('td');
        tagsCell.setAttribute('data-label', 'Теги');
        tagsCell.textContent = tags;
        
        const notesCell = document.createElement('td');
        notesCell.setAttribute('data-label', 'Заметки');
        notesCell.textContent = notes;
        
        row.appendChild(titleCell);
        row.appendChild(loginCell);
        row.appendChild(passwordCell);
        row.appendChild(urlCellEl);
        row.appendChild(tagsCell);
        row.appendChild(notesCell);
        
        if (canEdit) {
            const actionsCell = document.createElement('td');
            actionsCell.className = 'table-actions';
            actionsCell.setAttribute('data-label', 'Действия');
            
            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-small';
            editBtn.textContent = 'Редактировать';
            editBtn.onclick = () => showEditPasswordModal(pwd);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-small btn-danger';
            deleteBtn.textContent = 'Удалить';
            deleteBtn.onclick = () => confirmDeletePassword(pwd.id, pwd.title);
            
            actionsCell.appendChild(editBtn);
            actionsCell.appendChild(deleteBtn);
            
            row.appendChild(actionsCell);
        }
        
        passwordsTableBody.appendChild(row);
    });
    
    const table = document.querySelector('#passwords-table');
    if (table) {
        const thead = table.querySelector('thead');
        if (thead) {
            const headers = Array.from(thead.querySelectorAll('th'));
            const rows = passwordsTableBody.querySelectorAll('tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    if (headers[index] && !cell.hasAttribute('data-label')) {
                        cell.setAttribute('data-label', headers[index].textContent.trim());
                    }
                });
            });
        }
    }
}

function togglePassword(passwordDisplay, button) {
    if (passwordDisplay.classList.contains('password-hidden')) {
        passwordDisplay.textContent = passwordDisplay.dataset.password;
        passwordDisplay.classList.remove('password-hidden');
        passwordDisplay.classList.add('password-visible');
        button.textContent = 'Скрыть';
    } else {
        passwordDisplay.textContent = '••••••••';
        passwordDisplay.classList.remove('password-visible');
        passwordDisplay.classList.add('password-hidden');
        button.textContent = 'Показать';
    }
}

async function copyPassword(password, button) {
    try {
        await navigator.clipboard.writeText(password);
        button.textContent = 'Скопировано!';
        setTimeout(() => {
            button.textContent = 'Копировать';
        }, 2000);
    } catch (err) {
        const textarea = document.createElement('textarea');
        textarea.value = password;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            button.textContent = 'Скопировано!';
            setTimeout(() => {
                button.textContent = 'Копировать';
            }, 2000);
        } catch (err) {
            alert('Не удалось скопировать пароль');
        }
        document.body.removeChild(textarea);
    }
}

async function loadPasswords() {
    const response = await fetch(apiUrl, { credentials: 'include' });
    if (!response.ok) {
        const payload = await response.json();
        const error = payload.error || 'Ошибка загрузки паролей.';
        alert(error);
        if (response.status === 403 || response.status === 404) {
            window.location.href = '/vaults/';
        }
        return;
    }
    const payload = await response.json();
    renderPasswords(payload);
}

if (refreshButton) {
    refreshButton.addEventListener('click', loadPasswords);
}

async function updatePassword(passwordId, formData) {
    const data = {
        title: formData.get('title'),
        login: formData.get('login'),
        password: formData.get('password'),
        url: formData.get('url') || '',
        notes: formData.get('notes') || '',
        tags: (formData.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
    };
    
    const response = await fetch(`/api/vaults/${vaultId}/passwords/${passwordId}/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    });
    
    const payload = await response.json();
    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка обновления пароля.';
        alert(message);
        return;
    }
    
    alert(payload.message || 'Пароль успешно обновлен.');
    hideEditPasswordModal();
    await loadPasswords();
}

async function deletePassword(passwordId) {
    const response = await fetch(`/api/vaults/${vaultId}/passwords/${passwordId}/delete/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    });
    
    const payload = await response.json();
    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка удаления пароля.';
        alert(message);
        return;
    }
    
    alert('Пароль перемещён в корзину. Вы можете восстановить его позже.');
    await loadPasswords();
}

function confirmDeletePassword(passwordId, title) {
    if (confirm(`Вы уверены, что хотите удалить пароль "${title}"?\n\nПароль будет перемещён в корзину и может быть восстановлен.`)) {
        deletePassword(passwordId);
    }
}

function showEditPasswordModal(password) {
    const modal = document.querySelector('#edit-password-modal');
    if (!modal) {
        alert('Модальное окно редактирования не найдено.');
        return;
    }
    
    document.querySelector('#edit-password-id').value = password.id;
    document.querySelector('#edit-password-title').value = password.title || '';
    document.querySelector('#edit-password-login').value = password.login || '';
    document.querySelector('#edit-password-password').value = password.password || '';
    document.querySelector('#edit-password-url').value = password.url || '';
    document.querySelector('#edit-password-notes').value = password.notes || '';
    document.querySelector('#edit-password-tags').value = (password.tags || []).join(', ');
    
    modal.classList.add('is-open');
}

function hideEditPasswordModal() {
    const modal = document.querySelector('#edit-password-modal');
    if (modal) {
        modal.classList.remove('is-open');
        const form = document.querySelector('#edit-password-form');
        if (form) {
            form.reset();
        }
    }
}

function showAddPasswordModal() {
    const modal = document.querySelector('#add-password-modal');
    if (!modal) {
        alert('Модальное окно добавления не найдено.');
        return;
    }
    modal.classList.add('is-open');
}

function hideAddPasswordModal() {
    const modal = document.querySelector('#add-password-modal');
    if (modal) {
        modal.classList.remove('is-open');
        const form = document.querySelector('#add-password-form');
        if (form) {
            form.reset();
        }
    }
}

async function createPassword(formData) {
    const data = {
        title: formData.get('title'),
        login: formData.get('login'),
        password: formData.get('password'),
        url: formData.get('url') || '',
        notes: formData.get('notes') || '',
        tags: (formData.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
    };
    
    const response = await fetch(`/api/vaults/${vaultId}/passwords/create/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    });
    
    const payload = await response.json();
    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка добавления пароля.';
        alert(message);
        return;
    }
    
    alert(payload.message || 'Пароль успешно добавлен.');
    hideAddPasswordModal();
    await loadPasswords();
}

if (addPasswordBtn) {
    addPasswordBtn.addEventListener('click', showAddPasswordModal);
}

loadPasswords().catch(() => {
    alert('Ошибка загрузки паролей.');
});
