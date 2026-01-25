const generatorForm = document.querySelector('#generator-form');
const formMessage = document.querySelector('#form-message');
const resultPanel = document.querySelector('#result-panel');
const passwordDisplay = document.querySelector('#password-display');
const copyBtn = document.querySelector('#copy-btn');
const regenerateBtn = document.querySelector('#regenerate-btn');
const savePanel = document.querySelector('#save-panel');
const saveForm = document.querySelector('#save-form');
const saveVault = document.querySelector('#save-vault');
const saveMessage = document.querySelector('#save-message');
const cancelSaveBtn = document.querySelector('#cancel-save-btn');

const apiUrl = '/api/passwords/generate/';
const vaultsUrl = '/api/passwords/vaults/';
const saveUrl = '/api/passwords/save/';

let currentPassword = '';

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

async function generatePassword(formData) {
    const data = {
        length: parseInt(formData.get('length')),
        use_uppercase: formData.get('use_uppercase') === 'on',
        use_lowercase: formData.get('use_lowercase') === 'on',
        use_digits: formData.get('use_digits') === 'on',
        use_special: formData.get('use_special') === 'on',
        exclude_chars: formData.get('exclude_chars') || '',
    };

    const response = await fetch(apiUrl, {
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
        formMessage.textContent = payload.error || 'Ошибка генерации пароля.';
        formMessage.classList.add('is-error');
        formMessage.classList.remove('is-success');
        resultPanel.style.display = 'none';
        return;
    }

    formMessage.classList.remove('is-error');
    formMessage.classList.add('is-success');
    formMessage.textContent = 'Пароль успешно сгенерирован.';
    
    currentPassword = payload.password;
    passwordDisplay.textContent = currentPassword;
    resultPanel.style.display = 'block';
    
    await loadVaults();
    
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function loadVaults() {
    try {
        const response = await fetch(vaultsUrl, { credentials: 'include' });
        if (!response.ok) {
            return;
        }
        const payload = await response.json();
        const vaults = payload.vaults || [];
        
        saveVault.innerHTML = '<option value="">Выберите хранилище...</option>';
        vaults.forEach(vault => {
            const option = document.createElement('option');
            option.value = vault.id;
            option.textContent = vault.name;
            saveVault.appendChild(option);
        });
    } catch (err) {
        console.error('Ошибка загрузки хранилищ:', err);
    }
}

async function savePasswordToVault(formData) {
    const data = {
        vault_id: parseInt(formData.get('vault_id')),
        title: formData.get('title'),
        login: formData.get('login'),
        password: currentPassword,
        url: formData.get('url') || '',
        notes: formData.get('notes') || '',
    };

    const response = await fetch(saveUrl, {
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
        saveMessage.textContent = payload.error || 'Ошибка сохранения пароля.';
        saveMessage.classList.add('is-error');
        saveMessage.classList.remove('is-success');
        return;
    }

    saveMessage.classList.remove('is-error');
    saveMessage.classList.add('is-success');
    saveMessage.textContent = `Пароль успешно сохранен в хранилище "${payload.vault_name}".`;
    
    saveForm.reset();
    setTimeout(() => {
        savePanel.style.display = 'none';
        saveMessage.textContent = '';
        saveMessage.classList.remove('is-error', 'is-success');
    }, 2000);
}

if (generatorForm) {
    generatorForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        formMessage.textContent = '';
        formMessage.classList.remove('is-error', 'is-success');
        
        const formData = new FormData(generatorForm);
        
        const useUppercase = formData.get('use_uppercase') === 'on';
        const useLowercase = formData.get('use_lowercase') === 'on';
        const useDigits = formData.get('use_digits') === 'on';
        const useSpecial = formData.get('use_special') === 'on';
        
        if (!useUppercase && !useLowercase && !useDigits && !useSpecial) {
            formMessage.textContent = 'Необходимо выбрать хотя бы один тип символов.';
            formMessage.classList.add('is-error');
            return;
        }
        
        await generatePassword(formData);
    });
}

if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
        const password = passwordDisplay.textContent;
        if (!password) return;
        
        try {
            await navigator.clipboard.writeText(password);
            copyBtn.textContent = 'Скопировано!';
            setTimeout(() => {
                copyBtn.textContent = 'Копировать';
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
                copyBtn.textContent = 'Скопировано!';
                setTimeout(() => {
                    copyBtn.textContent = 'Копировать';
                }, 2000);
            } catch (err) {
                formMessage.textContent = 'Не удалось скопировать пароль.';
                formMessage.classList.add('is-error');
            }
            document.body.removeChild(textarea);
        }
    });
}

const saveToVaultBtn = document.querySelector('#save-to-vault-btn');

if (saveToVaultBtn) {
    saveToVaultBtn.addEventListener('click', async () => {
        if (!currentPassword) {
            formMessage.textContent = 'Сначала сгенерируйте пароль.';
            formMessage.classList.add('is-error');
            return;
        }
        
        await loadVaults();
        const vaults = Array.from(saveVault.options).length - 1;
        
        if (vaults === 0) {
            saveMessage.textContent = 'У вас нет доступных хранилищ для сохранения пароля.';
            saveMessage.classList.add('is-error');
            savePanel.style.display = 'block';
            return;
        }
        
        savePanel.style.display = 'block';
        saveMessage.textContent = '';
        saveMessage.classList.remove('is-error', 'is-success');
        savePanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
}

if (saveForm) {
    saveForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        saveMessage.textContent = '';
        saveMessage.classList.remove('is-error', 'is-success');
        
        const formData = new FormData(saveForm);
        await savePasswordToVault(formData);
    });
}

if (cancelSaveBtn) {
    cancelSaveBtn.addEventListener('click', () => {
        savePanel.style.display = 'none';
        saveForm.reset();
        saveMessage.textContent = '';
        saveMessage.classList.remove('is-error', 'is-success');
    });
}

if (regenerateBtn) {
    regenerateBtn.addEventListener('click', async () => {
        if (generatorForm) {
            const formData = new FormData(generatorForm);
            await generatePassword(formData);
        }
    });
}

loadVaults();
