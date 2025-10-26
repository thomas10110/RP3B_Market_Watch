document.addEventListener('DOMContentLoaded', () => {
    // --- Caches for state management ---
    let allEmails = [];
    let watchlistData = [];

    // --- DOM Element Selectors ---
    const emailInput = document.getElementById('email-input');
    const addEmailBtn = document.getElementById('add-email-btn');
    const emailList = document.getElementById('email-list');
    const symbolInput = document.getElementById('symbol-input');
    const addSymbolBtn = document.getElementById('add-symbol-btn');
    const watchlistTableBody = document.querySelector('#watchlist-table tbody');
    const modal = document.getElementById('settings-modal');
    const closeModalBtn = document.querySelector('.close-btn');
    const modalTitle = document.getElementById('modal-title');
    const targetsList = document.getElementById('targets-list');
    const addTargetForm = document.getElementById('add-target-form');
    const targetTypeSelect = document.getElementById('target-type');
    const targetPercentageInput = document.getElementById('target-percentage');
    const notificationList = document.getElementById('notification-list');
    const saveNotificationPrefsBtn = document.getElementById('save-notification-prefs');

    let currentWatchlistId = null;

    // --- API Helper ---
    const api = {
        get: (url) => fetch(url).then(res => res.json()),
        post: (url, data) => fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(res => res.json()),
        put: (url, data) => fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(res => res.json()),
        delete: (url) => fetch(url, { method: 'DELETE' }).then(res => res.json()),
    };

    // --- Render Functions ---
    const renderEmails = () => {
        emailList.innerHTML = '';
        allEmails.forEach(email => {
            const li = document.createElement('li');
            li.innerHTML = `<span>${email.email}</span><button class="delete-email-btn" data-id="${email.id}">&times;</button>`;
            emailList.appendChild(li);
        });
    };

    const renderWatchlist = () => {
        watchlistTableBody.innerHTML = '';
        watchlistData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.symbol}</td>
                <td>${item.initial_price ? item.initial_price.toFixed(2) : 'N/A'}</td>
                <td>${item.last_price ? item.last_price.toFixed(2) : 'N/A'}</td>
                <td>${new Date(item.last_updated).toLocaleString()}</td>
                <td>
                    <button class="settings-btn" data-id="${item.id}">Settings</button>
                    <button class="delete-stock-btn" data-id="${item.id}">Delete</button>
                </td>
            `;
            watchlistTableBody.appendChild(row);
        });
    };

    const renderModalContent = () => {
        const stock = watchlistData.find(s => s.id === currentWatchlistId);
        if (!stock) return;

        modalTitle.textContent = `Settings for ${stock.symbol}`;

        // Render targets
        targetsList.innerHTML = '';
        stock.targets.forEach(target => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${target.target_type === 'gain' ? 'Gain' : 'Dip'} at ${target.percentage}%</span>
                <button class="delete-target-btn" data-id="${target.id}">&times;</button>
            `;
            targetsList.appendChild(li);
        });

        // Render notification preferences
        notificationList.innerHTML = '';
        allEmails.forEach(email => {
            const li = document.createElement('li');
            const isChecked = stock.subscribed_emails.includes(email.id);
            li.innerHTML = `
                <label>
                    <input type="checkbox" data-email-id="${email.id}" ${isChecked ? 'checked' : ''}>
                    ${email.email}
                </label>
            `;
            notificationList.appendChild(li);
        });
    };

    // --- Data Fetching and State Update ---
    const fetchAllData = async () => {
        const [emails, watchlist] = await Promise.all([
            api.get('/api/emails'),
            api.get('/api/watchlist')
        ]);
        allEmails = emails;
        watchlistData = watchlist;
        renderEmails();
        renderWatchlist();
    };

    // --- Event Handlers ---
    const handleAddEmail = async () => {
        const email = emailInput.value.trim();
        if (email) {
            await api.post('/api/emails', { email });
            emailInput.value = '';
            fetchAllData();
        }
    };

    const handleDeleteEmail = async (e) => {
        if (!e.target.matches('.delete-email-btn')) return;
        const emailId = parseInt(e.target.dataset.id);
        await api.delete(`/api/emails/${emailId}`);
        fetchAllData();
    };

    const handleAddSymbol = async () => {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (symbol) {
            await api.post('/api/watchlist', { symbol });
            symbolInput.value = '';
            fetchAllData();
        }
    };

    const handleDeleteStock = async (e) => {
        if (!e.target.matches('.delete-stock-btn')) return;
        const stockId = parseInt(e.target.dataset.id);
        await api.delete(`/api/watchlist/${stockId}`);
        fetchAllData();
    };

    const handleOpenSettings = (e) => {
        if (!e.target.matches('.settings-btn')) return;
        currentWatchlistId = parseInt(e.target.dataset.id);
        renderModalContent();
        modal.style.display = 'block';
    };

    const handleAddTarget = async (e) => {
        e.preventDefault();
        const target_type = targetTypeSelect.value;
        const percentage = parseFloat(targetPercentageInput.value);
        if (!percentage || percentage <= 0) {
            alert("Please enter a positive percentage.");
            return;
        }

        const newTarget = await api.post('/api/price_targets', {
            watchlist_id: currentWatchlistId,
            target_type,
            percentage
        });

        // Update local state and re-render modal
        const stock = watchlistData.find(s => s.id === currentWatchlistId);
        stock.targets.push(newTarget);
        renderModalContent();
        addTargetForm.reset();
    };

    const handleDeleteTarget = async (e) => {
        if (!e.target.matches('.delete-target-btn')) return;
        const targetId = parseInt(e.target.dataset.id);
        await api.delete(`/api/price_targets/${targetId}`);

        // Update local state and re-render modal
        const stock = watchlistData.find(s => s.id === currentWatchlistId);
        stock.targets = stock.targets.filter(t => t.id !== targetId);
        renderModalContent();
    };

    const handleSaveNotifications = async () => {
        const selectedCheckboxes = notificationList.querySelectorAll('input[type="checkbox"]:checked');
        const email_ids = Array.from(selectedCheckboxes).map(cb => parseInt(cb.dataset.emailId));

        await api.put(`/api/notification_preferences/${currentWatchlistId}`, { email_ids });

        // Update local state and close modal
        const stock = watchlistData.find(s => s.id === currentWatchlistId);
        stock.subscribed_emails = email_ids;
        modal.style.display = 'none';
    };

    // --- Initial Setup ---
    addEmailBtn.addEventListener('click', handleAddEmail);
    emailList.addEventListener('click', handleDeleteEmail);
    addSymbolBtn.addEventListener('click', handleAddSymbol);
    watchlistTableBody.addEventListener('click', handleDeleteStock);
    watchlistTableBody.addEventListener('click', handleOpenSettings);
    closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => e.target === modal ? modal.style.display = 'none' : null);
    addTargetForm.addEventListener('submit', handleAddTarget);
    targetsList.addEventListener('click', handleDeleteTarget);
    saveNotificationPrefsBtn.addEventListener('click', handleSaveNotifications);

    fetchAllData();
});
