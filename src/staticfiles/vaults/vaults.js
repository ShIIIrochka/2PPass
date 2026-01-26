const vaultsTableBody = document.querySelector('#vaults-table tbody');
const vaultsEmpty = document.querySelector('#vaults-empty');
const refreshButton = document.querySelector('#refresh-vaults');
const createForm = document.querySelector('#create-vault-form');
const formMessage = document.querySelector('#vault-form-message');
const usersSelect = document.querySelector('#vault-users');
const groupsSelect = document.querySelector('#vault-groups');
const createGroupBtn = document.querySelector('#create-group-btn');
const createGroupModal = document.querySelector('#create-group-modal');
const createGroupForm = document.querySelector('#create-group-form');
const createGroupCancel = document.querySelector('#create-group-cancel');
const groupFormMessage = document.querySelector('#group-form-message');

const apiUrl = '/api/vaults/';
const createUrl = '/api/vaults/create/';
const usersUrl = '/api/vaults/users/';
const groupsUrl = '/api/users/groups/';

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

function addTableLabels(table) {
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const headers = Array.from(thead.querySelectorAll('th'));
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, index) => {
            if (headers[index] && !cell.hasAttribute('data-label')) {
                cell.setAttribute('data-label', headers[index].textContent.trim());
            }
        });
    });
}

function renderVaults(vaults) {
    vaultsTableBody.innerHTML = '';
    if (!vaults.length) {
        vaultsEmpty.classList.remove('hidden');
        return;
    }
    vaultsEmpty.classList.add('hidden');

    vaults.forEach((vault) => {
        const row = document.createElement('tr');
        const tags = (vault.tags || []).join(', ') || '-';
        const accessName = {
            'admin': 'Администратор',
            'edit': 'Редактирование',
            'view': 'Просмотр',
        }[vault.access_level] || vault.access_level;

        const nameCell = document.createElement('td');
        nameCell.className = 'clickable-vault';
        nameCell.setAttribute('data-label', 'Название');
        nameCell.onclick = () => window.location.href = `/vaults/${vault.id}/`;
        nameCell.textContent = vault.name;
        
        const descCell = document.createElement('td');
        descCell.setAttribute('data-label', 'Описание');
        descCell.textContent = vault.description || '-';
        
        const tagsCell = document.createElement('td');
        tagsCell.setAttribute('data-label', 'Теги');
        tagsCell.textContent = tags;
        
        const creatorCell = document.createElement('td');
        creatorCell.setAttribute('data-label', 'Создатель');
        creatorCell.textContent = vault.created_by;
        
        const accessCell = document.createElement('td');
        accessCell.setAttribute('data-label', 'Уровень доступа');
        accessCell.textContent = accessName;
        
        const usersCell = document.createElement('td');
        usersCell.setAttribute('data-label', 'Пользователей');
        usersCell.textContent = vault.users_count;
        
        row.appendChild(nameCell);
        row.appendChild(descCell);
        row.appendChild(tagsCell);
        row.appendChild(creatorCell);
        row.appendChild(accessCell);
        row.appendChild(usersCell);
        vaultsTableBody.appendChild(row);
    });
    
    const table = document.querySelector('#vaults-table');
    if (table) {
        addTableLabels(table);
    }
}

async function loadVaults() {
    const response = await fetch(apiUrl, { credentials: 'include' });
    if (!response.ok) {
        formMessage.textContent = 'Ошибка загрузки хранилищ.';
        formMessage.classList.add('is-error');
        return;
    }
    const payload = await response.json();
    renderVaults(payload.vaults || []);
}

async function loadUsers() {
    if (!usersSelect) return;
    
    const response = await fetch(usersUrl, { credentials: 'include' });
    if (!response.ok) {
        return;
    }
    const payload = await response.json();
    const users = payload.users || [];

    usersSelect.innerHTML = '';
    users.forEach((user) => {
        const option = document.createElement('option');
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
        option.value = user.id;
        option.textContent = fullName ? `${fullName} (${user.email})` : user.email;
        usersSelect.appendChild(option);
    });
}

async function loadGroups() {
    if (!groupsSelect) return;
    const response = await fetch(groupsUrl, { credentials: 'include' });
    if (!response.ok) {
        return;
    }
    const payload = await response.json();
    const groups = payload.groups || [];

    groupsSelect.innerHTML = '';
    groups.forEach((group) => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        groupsSelect.appendChild(option);
    });
}

function showCreateGroupModal() {
    if (!createGroupModal) return;
    if (groupFormMessage) {
        groupFormMessage.textContent = '';
        groupFormMessage.classList.remove('is-error', 'is-success');
    }
    if (createGroupForm) {
        createGroupForm.reset();
    }
    createGroupModal.classList.add('is-open');
}

function hideCreateGroupModal() {
    if (!createGroupModal) return;
    createGroupModal.classList.remove('is-open');
}

async function createGroup(formData) {
    const name = (formData.get('name') || '').trim();
    if (!name) {
        if (groupFormMessage) {
            groupFormMessage.textContent = 'Введите название группы.';
            groupFormMessage.classList.add('is-error');
            groupFormMessage.classList.remove('is-success');
        }
        return;
    }

    const response = await fetch(groupsUrl, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ name }),
    });

    let payload = {};
    try {
        payload = await response.json();
    } catch (_e) {
        payload = {};
    }

    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка создания группы.';
        if (groupFormMessage) {
            groupFormMessage.textContent = message;
            groupFormMessage.classList.add('is-error');
            groupFormMessage.classList.remove('is-success');
        }
        return;
    }

    if (groupFormMessage) {
        groupFormMessage.textContent = payload.message || 'Группа создана.';
        groupFormMessage.classList.remove('is-error');
        groupFormMessage.classList.add('is-success');
    }

    await loadGroups();

    if (groupsSelect && payload.id != null) {
        const createdOption = groupsSelect.querySelector(`option[value="${payload.id}"]`);
        if (createdOption) {
            createdOption.selected = true;
        }
    }

    hideCreateGroupModal();
}

async function createVault(formData) {
    const data = {
        name: formData.get('name'),
        description: formData.get('description') || '',
        tags: (formData.get('tags') || '').split(',').map(tag => tag.trim()).filter(Boolean),
        access_level: formData.get('access_level'),
        users: formData.getAll('users').map(id => parseInt(id)),
        groups: formData.getAll('groups').map(id => parseInt(id)),
    };

    const response = await fetch(createUrl, {
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
        const message = payload.error || payload.detail || 'Ошибка создания хранилища.';
        formMessage.textContent = message;
        formMessage.classList.add('is-error');
        formMessage.classList.remove('is-success');
        return;
    }

    formMessage.classList.remove('is-error');
    formMessage.classList.add('is-success');
    formMessage.textContent = payload.message || 'Хранилище создано.';
    createForm.reset();
    await loadVaults();
}

if (refreshButton) {
    refreshButton.addEventListener('click', loadVaults);
}

if (createForm) {
    createForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        formMessage.textContent = '';
        formMessage.classList.remove('is-error', 'is-success');
        const data = new FormData(createForm);
        await createVault(data);
    });
}

if (createGroupBtn) {
    createGroupBtn.addEventListener('click', showCreateGroupModal);
}

if (createGroupCancel) {
    createGroupCancel.addEventListener('click', hideCreateGroupModal);
}

if (createGroupForm) {
    createGroupForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        await createGroup(new FormData(createGroupForm));
    });
}

if (createGroupModal) {
    createGroupModal.addEventListener('click', (e) => {
        if (e.target === createGroupModal || e.target.classList.contains('modal-overlay')) {
            hideCreateGroupModal();
        }
    });
}

const canCreate = window.canCreateVault === true;

if (canCreate && createForm) {
    loadUsers();
    loadGroups();
}

loadVaults().catch(() => {
    if (formMessage) {
        formMessage.textContent = 'Ошибка загрузки хранилищ.';
        formMessage.classList.add('is-error');
    }
});
