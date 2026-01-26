const usersTableBody = document.querySelector('#users-table tbody');
const emptyState = document.querySelector('#users-empty');
const refreshButton = document.querySelector('#refresh-users');
const form = document.querySelector('#create-user-form');
const formMessage = document.querySelector('#form-message');

const apiUrl = '/api/users/';
const vaultsApiUrl = '/api/vaults/';
const rolesApiUrl = '/api/roles/';

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

let allVaults = [];
let customRoles = [];

async function loadVaults() {
    try {
        const response = await fetch(vaultsApiUrl, { credentials: 'include' });
        if (!response.ok) return;
        const payload = await response.json();
        allVaults = payload.vaults || [];
    } catch (err) {
        console.error('Ошибка загрузки хранилищ:', err);
    }
}

async function loadCustomRoles() {
    try {
        const response = await fetch(rolesApiUrl, { credentials: 'include' });
        if (!response.ok) return;
        const payload = await response.json();
        customRoles = payload.custom_roles || [];
    } catch (err) {
        console.error('Ошибка загрузки ролей:', err);
    }
}

function buildRoleChoiceOptions(selectEl) {
    if (!selectEl) return;
    selectEl.innerHTML = '';

    const systemGroup = document.createElement('optgroup');
    systemGroup.label = 'Системные роли';

    const employeeOption = document.createElement('option');
    employeeOption.value = 'employee';
    employeeOption.textContent = 'Сотрудник';
    systemGroup.appendChild(employeeOption);

    if (window.isAdmin === true) {
        const managerOption = document.createElement('option');
        managerOption.value = 'manager';
        managerOption.textContent = 'Менеджер';
        systemGroup.appendChild(managerOption);

        const adminOption = document.createElement('option');
        adminOption.value = 'admin';
        adminOption.textContent = 'Администратор';
        systemGroup.appendChild(adminOption);
    }

    selectEl.appendChild(systemGroup);

    if (customRoles.length && window.isAdmin === true) {
        const customGroup = document.createElement('optgroup');
        customGroup.label = 'Кастомные роли';
        customRoles.forEach(role => {
            const option = document.createElement('option');
            option.value = `custom:${role.id}`;
            option.textContent = role.name;
            customGroup.appendChild(option);
        });
        selectEl.appendChild(customGroup);
    }
}

function setRoleChoiceValue(selectEl, userRole, customRoleId) {
    if (!selectEl) return;
    if (customRoleId) {
        selectEl.value = `custom:${customRoleId}`;
        return;
    }
    selectEl.value = userRole || 'employee';
}

function normalizeRoleChoice(value) {
    const selected = (value || '').toString();
    if (selected.startsWith('custom:')) {
        const id = parseInt(selected.replace('custom:', ''), 10);
        return { role: 'employee', custom_role: Number.isFinite(id) ? id : null };
    }
    return { role: selected || 'employee', custom_role: null };
}

function createVaultAccessRow(container, initial) {
    const row = document.createElement('div');
    row.className = 'inline-row';
    row.style.display = 'flex';
    row.style.gap = '8px';
    row.style.marginBottom = '8px';
    row.style.flexWrap = 'wrap';

    const vaultSelect = document.createElement('select');
    vaultSelect.className = 'filter-select';
    vaultSelect.style.minWidth = '220px';

    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = 'Выберите хранилище';
    vaultSelect.appendChild(emptyOption);

    allVaults.forEach(vault => {
        const option = document.createElement('option');
        option.value = vault.id;
        option.textContent = vault.name;
        vaultSelect.appendChild(option);
    });

    const levelSelect = document.createElement('select');
    levelSelect.className = 'filter-select';
    levelSelect.style.minWidth = '180px';
    [
        { value: 'view', label: 'Просмотр' },
        { value: 'edit', label: 'Редактирование' },
        { value: 'admin', label: 'Администратор' },
    ].forEach(item => {
        const option = document.createElement('option');
        option.value = item.value;
        option.textContent = item.label;
        levelSelect.appendChild(option);
    });

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-small btn-danger';
    removeBtn.textContent = 'Удалить';
    removeBtn.addEventListener('click', () => row.remove());

    if (initial) {
        if (initial.vault_id) vaultSelect.value = String(initial.vault_id);
        if (initial.access_level) levelSelect.value = initial.access_level;
    }

    row.appendChild(vaultSelect);
    row.appendChild(levelSelect);
    row.appendChild(removeBtn);

    container.appendChild(row);
}

function collectVaultAccesses(container) {
    const result = [];
    const rows = container ? Array.from(container.querySelectorAll('.inline-row')) : [];
    rows.forEach(row => {
        const selects = row.querySelectorAll('select');
        if (selects.length < 2) return;
        const vaultId = selects[0].value;
        const accessLevel = selects[1].value;
        if (!vaultId) return;
        result.push({ vault_id: parseInt(vaultId), access_level: accessLevel });
    });
    return result;
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

function renderUsers(users) {
    usersTableBody.innerHTML = '';
    if (!users.length) {
        emptyState.classList.remove('hidden');
        return;
    }
    emptyState.classList.add('hidden');
    
    const currentUserRole = window.currentUserRole || '';
    const isAdmin = window.isAdmin === true;
    const isManager = window.isManager === true;
    const canEditUsers = window.canEditUsers === true;
    const canDeleteUsers = window.canDeleteUsers === true;
    
    users.forEach((user) => {
        const row = document.createElement('tr');
        const actionsCell = document.createElement('td');
        actionsCell.className = 'table-actions';
        actionsCell.setAttribute('data-label', 'Действия');
        
        const canManage = isAdmin || isManager || canEditUsers || canDeleteUsers;
        const canEditThisUser = isAdmin || (isManager && user.role === 'employee') || canEditUsers;
        const canDeleteThisUser = isAdmin || (isManager && user.role === 'employee') || canDeleteUsers;
        
        if (canManage) {
            if (canEditThisUser) {
                const editBtn = document.createElement('button');
                editBtn.className = 'btn btn-small';
                editBtn.textContent = 'Редактировать';
                editBtn.onclick = () => showEditUserModal(user.id);
                actionsCell.appendChild(editBtn);
            }
            
            if (canDeleteThisUser && user.is_active) {
                const deactivateBtn = document.createElement('button');
                deactivateBtn.className = 'btn btn-small';
                deactivateBtn.textContent = 'Отключить доступ';
                deactivateBtn.onclick = () => showConfirmModal(
                    'Отключить доступ',
                    `Вы уверены, что хотите отключить доступ пользователю ${user.email}?`,
                    () => deactivateUser(user.id)
                );
                actionsCell.appendChild(deactivateBtn);
            }
            
            if (canDeleteThisUser) {
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn btn-small btn-danger';
                deleteBtn.textContent = 'Удалить';
                deleteBtn.onclick = () => showConfirmModal(
                    'Удалить пользователя',
                    `Вы уверены, что хотите удалить пользователя ${user.email}? Это действие нельзя отменить.`,
                    () => deleteUser(user.id)
                );
                actionsCell.appendChild(deleteBtn);
            }
        } else {
            actionsCell.textContent = '-';
        }
        
        const emailCell = document.createElement('td');
        emailCell.className = 'clickable-cell';
        emailCell.setAttribute('data-label', 'Email');
        emailCell.onclick = () => showUserDetail(user.id);
        emailCell.textContent = user.email || '-';
        
        const nameCell = document.createElement('td');
        nameCell.className = 'clickable-cell';
        nameCell.setAttribute('data-label', 'Имя');
        nameCell.onclick = () => showUserDetail(user.id);
        nameCell.textContent = [user.first_name, user.last_name].filter(Boolean).join(' ') || '-';
        
        const roleCell = document.createElement('td');
        roleCell.className = 'clickable-cell';
        roleCell.setAttribute('data-label', 'Роль');
        roleCell.onclick = () => showUserDetail(user.id);
        roleCell.textContent = user.role;
        
        const statusCell = document.createElement('td');
        statusCell.className = 'clickable-cell';
        statusCell.setAttribute('data-label', 'Статус');
        statusCell.onclick = () => showUserDetail(user.id);
        statusCell.textContent = user.is_active ? 'Активен' : 'Отключен';
        
        row.appendChild(emailCell);
        row.appendChild(nameCell);
        row.appendChild(roleCell);
        row.appendChild(statusCell);
        row.appendChild(actionsCell);
        usersTableBody.appendChild(row);
    });
    
    const table = document.querySelector('#users-table');
    if (table) {
        addTableLabels(table);
    }
}

let currentFilters = {
    role: '',
    status: '',
    ordering: 'id',
};

function buildApiUrl() {
    const params = new URLSearchParams();
    if (currentFilters.role) params.append('role', currentFilters.role);
    if (currentFilters.status) params.append('status', currentFilters.status);
    if (currentFilters.ordering) params.append('ordering', currentFilters.ordering);
    
    const queryString = params.toString();
    return queryString ? `${apiUrl}?${queryString}` : apiUrl;
}

async function loadUsers() {
    const url = buildApiUrl();
    const response = await fetch(url, { credentials: 'include' });
    if (!response.ok) {
        formMessage.textContent = 'Ошибка загрузки пользователей.';
        formMessage.classList.add('is-error');
        return;
    }
    const payload = await response.json();
    const users = payload.results || payload;
    renderUsers(users);
}

async function createUser(formData) {
    const roleChoiceSelect = document.querySelector('#role-choice');
    const { role, custom_role } = normalizeRoleChoice(roleChoiceSelect ? roleChoiceSelect.value : formData.get('role_choice'));

    const payloadToSend = {
        email: formData.get('email'),
        first_name: formData.get('first_name') || '',
        last_name: formData.get('last_name') || '',
        phone: formData.get('phone') || '',
        role,
    };

    const password = formData.get('password');
    if (password) {
        payloadToSend.password = password;
    }

    const createVaultAccessesContainer = document.querySelector('#create-vault-accesses');
    payloadToSend.vault_accesses = collectVaultAccesses(createVaultAccessesContainer);

    if (window.isAdmin === true) {
        payloadToSend.custom_role = custom_role;
    }

    const response = await fetch(apiUrl, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(payloadToSend),
    });

    const payload = await response.json();
    if (!response.ok) {
        const message = payload.detail || Object.values(payload).flat().join(' ');
        formMessage.textContent = message || 'Ошибка создания пользователя.';
        formMessage.classList.add('is-error');
        return;
    }

    formMessage.classList.remove('is-error');
    formMessage.classList.add('is-success');
    if (payload.temporary_password) {
        formMessage.textContent = `Пользователь создан. Временный пароль: ${payload.temporary_password}`;
    } else {
        formMessage.textContent = 'Пользователь создан.';
    }
    form.reset();
    await loadUsers();
}

if (refreshButton) {
    refreshButton.addEventListener('click', loadUsers);
}

if (form) {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        formMessage.textContent = '';
        formMessage.classList.remove('is-error', 'is-success');
        const data = new FormData(form);
        await createUser(data);
    });
}

const confirmModal = document.querySelector('#confirm-modal');
const modalTitle = document.querySelector('#modal-title');
const modalMessage = document.querySelector('#modal-message');
const modalCancel = document.querySelector('#modal-cancel');
const modalConfirm = document.querySelector('#modal-confirm');

let currentConfirmAction = null;

function showConfirmModal(title, message, action) {
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    currentConfirmAction = action;
    confirmModal.classList.add('is-open');
}

function hideConfirmModal() {
    confirmModal.classList.remove('is-open');
    currentConfirmAction = null;
}

if (modalCancel) {
    modalCancel.addEventListener('click', hideConfirmModal);
}

if (modalConfirm) {
    modalConfirm.addEventListener('click', () => {
        if (currentConfirmAction) {
            currentConfirmAction();
            hideConfirmModal();
        }
    });
}

if (confirmModal) {
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal || e.target.classList.contains('modal-overlay')) {
            hideConfirmModal();
        }
    });
}

async function deactivateUser(userId) {
    const response = await fetch(`${apiUrl}${userId}/deactivate/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    });

    const payload = await response.json();
    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка отзыва доступа.';
        formMessage.textContent = message;
        formMessage.classList.add('is-error');
        return;
    }

    formMessage.classList.remove('is-error');
    formMessage.classList.add('is-success');
    formMessage.textContent = payload.message || 'Доступ успешно отозван.';
    await loadUsers();
}

async function deleteUser(userId) {
    const response = await fetch(`${apiUrl}${userId}/delete/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    });

    const payload = await response.json();
    if (!response.ok) {
        const message = payload.error || payload.detail || 'Ошибка удаления пользователя.';
        formMessage.textContent = message;
        formMessage.classList.add('is-error');
        return;
    }

    formMessage.classList.remove('is-error');
    formMessage.classList.add('is-success');
    formMessage.textContent = payload.message || 'Пользователь успешно удален.';
    await loadUsers();
}

const filterRole = document.querySelector('#filter-role');
const filterStatus = document.querySelector('#filter-status');
const filterOrdering = document.querySelector('#filter-ordering');
const clearFiltersBtn = document.querySelector('#clear-filters');

if (filterRole) {
    filterRole.addEventListener('change', () => {
        currentFilters.role = filterRole.value;
        loadUsers();
    });
}

if (filterStatus) {
    filterStatus.addEventListener('change', () => {
        currentFilters.status = filterStatus.value;
        loadUsers();
    });
}

if (filterOrdering) {
    filterOrdering.addEventListener('change', () => {
        currentFilters.ordering = filterOrdering.value;
        loadUsers();
    });
}

if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
        currentFilters = { role: '', status: '', ordering: 'id' };
        filterRole.value = '';
        filterStatus.value = '';
        filterOrdering.value = 'id';
        loadUsers();
    });
}

const userDetailModal = document.querySelector('#user-detail-modal');
const userDetailTitle = document.querySelector('#user-detail-title');
const userDetailContent = document.querySelector('#user-detail-content');
const userDetailClose = document.querySelector('#user-detail-close');

window.showUserDetail = async function(userId) {
    const response = await fetch(`${apiUrl}${userId}/`, { credentials: 'include' });
    if (!response.ok) {
        formMessage.textContent = 'Ошибка загрузки информации о пользователе.';
        formMessage.classList.add('is-error');
        return;
    }
    
    const user = await response.json();
    
    userDetailTitle.textContent = `Информация о пользователе: ${user.email}`;
    
    const roleNames = {
        'admin': 'Администратор',
        'manager': 'Менеджер',
        'employee': 'Сотрудник',
    };
    
    const accessLevelNames = {
        'view': 'Просмотр',
        'edit': 'Редактирование',
        'admin': 'Администратор',
    };
    
    let groupsHtml = '<p>Нет групп</p>';
    if (user.groups && user.groups.length > 0) {
        groupsHtml = '<ul class="user-detail-list">';
        user.groups.forEach(group => {
            groupsHtml += `<li>${group.name}</li>`;
        });
        groupsHtml += '</ul>';
    }
    
    let vaultsHtml = '<p>Нет доступов к хранилищам</p>';
    if (user.vault_accesses && user.vault_accesses.length > 0) {
        vaultsHtml = '<ul class="user-detail-list">';
        user.vault_accesses.forEach(access => {
            const grantedDate = new Date(access.granted_at).toLocaleDateString('ru-RU');
            vaultsHtml += `<li><strong>${access.vault_name}</strong> - ${accessLevelNames[access.access_level] || access.access_level} (предоставлен ${grantedDate}${access.granted_by ? ` пользователем ${access.granted_by}` : ''})</li>`;
        });
        vaultsHtml += '</ul>';
    }
    
    userDetailContent.innerHTML = `
        <div class="user-detail-section">
            <h4>Основная информация</h4>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Email:</span>
                <span class="user-detail-field-value">${user.email || '-'}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Имя:</span>
                <span class="user-detail-field-value">${user.first_name || '-'}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Фамилия:</span>
                <span class="user-detail-field-value">${user.last_name || '-'}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Телефон:</span>
                <span class="user-detail-field-value">${user.phone || '-'}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Роль:</span>
                <span class="user-detail-field-value">${roleNames[user.role] || user.role}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Статус:</span>
                <span class="user-detail-field-value">${user.is_active ? 'Активен' : 'Отключен'}</span>
            </div>
            <div class="user-detail-field">
                <span class="user-detail-field-label">Дата регистрации:</span>
                <span class="user-detail-field-value">${new Date(user.date_joined).toLocaleDateString('ru-RU')}</span>
            </div>
        </div>
        <div class="user-detail-section">
            <h4>Группы</h4>
            ${groupsHtml}
        </div>
        <div class="user-detail-section">
            <h4>Доступы к хранилищам</h4>
            ${vaultsHtml}
        </div>
    `;
    
    userDetailModal.classList.add('is-open');
}

function hideUserDetailModal() {
    userDetailModal.classList.remove('is-open');
}

if (userDetailClose) {
    userDetailClose.addEventListener('click', hideUserDetailModal);
}

if (userDetailModal) {
    userDetailModal.addEventListener('click', (e) => {
        if (e.target === userDetailModal || e.target.classList.contains('modal-overlay')) {
            hideUserDetailModal();
        }
    });
}

const editUserModal = document.querySelector('#edit-user-modal');
const editUserForm = document.querySelector('#edit-user-form');
const editUserTitle = document.querySelector('#edit-user-title');
const editMessage = document.querySelector('#edit-message');
const editUserCancel = document.querySelector('#edit-user-cancel');
let currentEditUserId = null;
let allGroups = [];

async function loadGroups() {
    try {
        const response = await fetch('/api/users/groups/', { credentials: 'include' });
        if (response.ok) {
            const payload = await response.json();
            allGroups = payload.groups || [];
        }
    } catch (err) {
        console.error('Ошибка загрузки групп:', err);
    }
}

async function showEditUserModal(userId) {
    currentEditUserId = userId;

    if (!allVaults.length) {
        await loadVaults();
    }
    
    const response = await fetch(`${apiUrl}${userId}/`, { credentials: 'include' });
    if (!response.ok) {
        formMessage.textContent = 'Ошибка загрузки данных пользователя.';
        formMessage.classList.add('is-error');
        return;
    }
    
    const user = await response.json();
    
    editUserTitle.textContent = `Редактировать пользователя: ${user.email}`;
    
    document.querySelector('#edit-email').value = user.email || '';
    document.querySelector('#edit-first-name').value = user.first_name || '';
    document.querySelector('#edit-last-name').value = user.last_name || '';
    document.querySelector('#edit-phone').value = user.phone || '';
    document.querySelector('#edit-is-active').checked = user.is_active || false;

    const editRoleChoice = document.querySelector('#edit-role-choice');
    buildRoleChoiceOptions(editRoleChoice);
    setRoleChoiceValue(editRoleChoice, user.role, user.custom_role);

    const groupsSelect = document.querySelector('#edit-groups');
    groupsSelect.innerHTML = '';
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        if (user.groups && user.groups.some(g => g.id === group.id)) {
            option.selected = true;
        }
        groupsSelect.appendChild(option);
    });
    
    editMessage.textContent = '';
    editMessage.classList.remove('is-error', 'is-success');

    const editVaultAccessesContainer = document.querySelector('#edit-vault-accesses');
    if (editVaultAccessesContainer) {
        editVaultAccessesContainer.innerHTML = '';
        const vaultAccesses = user.vault_accesses || [];
        vaultAccesses.forEach(access => {
            createVaultAccessRow(editVaultAccessesContainer, {
                vault_id: access.vault_id,
                access_level: access.access_level,
            });
        });
    }

    editUserModal.classList.add('is-open');
}

function hideEditUserModal() {
    editUserModal.classList.remove('is-open');
    currentEditUserId = null;
    editUserForm.reset();
    editMessage.textContent = '';
    editMessage.classList.remove('is-error', 'is-success');
}

async function updateUser(formData) {
    const editRoleChoice = document.querySelector('#edit-role-choice');
    const { role, custom_role } = normalizeRoleChoice(editRoleChoice ? editRoleChoice.value : formData.get('role_choice'));

    const data = {
        email: formData.get('email'),
        first_name: formData.get('first_name') || '',
        last_name: formData.get('last_name') || '',
        phone: formData.get('phone') || '',
        role,
        is_active: formData.get('is_active') === 'on',
        groups: Array.from(formData.getAll('groups')).map(id => parseInt(id)),
    };

    const editVaultAccessesContainer = document.querySelector('#edit-vault-accesses');
    data.vault_accesses = collectVaultAccesses(editVaultAccessesContainer);

    if (window.isAdmin === true) {
        data.custom_role = custom_role;
    }
    
    const response = await fetch(`${apiUrl}${currentEditUserId}/`, {
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
        const message = payload.error || payload.detail || Object.values(payload).flat().join(' ') || 'Ошибка обновления пользователя.';
        editMessage.textContent = message;
        editMessage.classList.add('is-error');
        editMessage.classList.remove('is-success');
        return;
    }
    
    editMessage.classList.remove('is-error');
    editMessage.classList.add('is-success');
    editMessage.textContent = 'Пользователь успешно обновлен.';
    
    setTimeout(() => {
        hideEditUserModal();
        loadUsers();
    }, 1000);
}

if (editUserForm) {
    editUserForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        editMessage.textContent = '';
        editMessage.classList.remove('is-error', 'is-success');
        
        const formData = new FormData(editUserForm);
        await updateUser(formData);
    });
}

if (editUserCancel) {
    editUserCancel.addEventListener('click', hideEditUserModal);
}

if (editUserModal) {
    editUserModal.addEventListener('click', (e) => {
        if (e.target === editUserModal || e.target.classList.contains('modal-overlay')) {
            hideEditUserModal();
        }
    });
}

loadGroups();
loadCustomRoles().then(() => {
    buildRoleChoiceOptions(document.querySelector('#role-choice'));
});
loadVaults().then(() => {
    const createVaultAccessesContainer = document.querySelector('#create-vault-accesses');
    const addCreateVaultAccessBtn = document.querySelector('#add-create-vault-access');
    if (addCreateVaultAccessBtn && createVaultAccessesContainer) {
        addCreateVaultAccessBtn.addEventListener('click', () => createVaultAccessRow(createVaultAccessesContainer));
    }

    const editVaultAccessesContainer = document.querySelector('#edit-vault-accesses');
    const addEditVaultAccessBtn = document.querySelector('#add-edit-vault-access');
    if (addEditVaultAccessBtn && editVaultAccessesContainer) {
        addEditVaultAccessBtn.addEventListener('click', () => createVaultAccessRow(editVaultAccessesContainer));
    }
});

const roleChoiceSelect = document.querySelector('#role-choice');
if (roleChoiceSelect) {
    buildRoleChoiceOptions(roleChoiceSelect);
}

loadUsers().catch(() => {
    formMessage.textContent = 'Ошибка загрузки пользователей.';
    formMessage.classList.add('is-error');
});
