document.addEventListener('DOMContentLoaded', () => {
    // --- Caches for state management ---
    const toastContainer = document.getElementById('toast-container');
    let allEmails = [];
    let watchlistData = [];
    let priceChart = null;

    // --- DOM Element Selectors ---
    const emailInput = document.getElementById('email-input');
    const addEmailBtn = document.getElementById('add-email-btn');
    const emailList = document.getElementById('email-list');
    const symbolInput = document.getElementById('symbol-input');
    const addSymbolBtn = document.getElementById('add-symbol-btn');
    const watchlistTableBody = document.querySelector('#watchlist-table tbody');

    // Settings Modal
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = settingsModal.querySelector('.close-btn');
    const modalTitle = document.getElementById('modal-title');
    const targetsList = document.getElementById('targets-list');
    const addTargetForm = document.getElementById('add-target-form');
    const targetTypeSelect = document.getElementById('target-type');
    const targetPercentageInput = document.getElementById('target-percentage');
    const notificationList = document.getElementById('notification-list');
    const saveNotificationPrefsBtn = document.getElementById('save-notification-prefs');

    // Chart Modal
    const chartModal = document.getElementById('chart-modal');
    const closeChartBtn = chartModal.querySelector('.close-btn');
    const chartModalTitle = document.getElementById('chart-modal-title');

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
                <td class="symbol-cell" data-symbol="${item.symbol}">${item.symbol}</td>
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
        targetsList.innerHTML = '';
        stock.targets.forEach(target => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${target.target_type === 'gain' ? 'Gain' : 'Dip'} at ${target.percentage}%</span>
                <button class="delete-target-btn" data-id="${target.id}">&times;</button>
            `;
            targetsList.appendChild(li);
        });
        notificationList.innerHTML = '';
        allEmails.forEach(email => {
            const li = document.createElement('li');
            const isChecked = stock.subscribed_emails.includes(email.id);
            li.innerHTML = `<label><input type="checkbox" data-email-id="${email.id}" ${isChecked ? 'checked' : ''}> ${email.email}</label>`;
            notificationList.appendChild(li);
        });
    };

    const renderChart = (symbol, history) => {
        chartModalTitle.textContent = `Historical Data for ${symbol}`;
        const ctx = document.getElementById('price-chart').getContext('2d');

        if (priceChart) {
            priceChart.destroy();
        }

        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(0, 191, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(0, 191, 255, 0)');

        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.labels,
                datasets: [{
                    label: 'Price (USD)',
                    data: history.data,
                    borderColor: '#00bfff',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                },
                plugins: { legend: { labels: { color: '#e0e0e0' } } }
            }
        });
        chartModal.style.display = 'block';
    };

    // --- Data Fetching ---
    const fetchAllData = async () => {
        const [emails, watchlist] = await Promise.all([api.get('/api/emails'), api.get('/api/watchlist')]);
        allEmails = emails;
        watchlistData = watchlist;
        renderEmails();
        renderWatchlist();
    };

    // --- UI Helper ---
    const showToast = (message, type = 'success') => {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    };

    // --- Event Handlers ---
    const handleAddEmail = async () => {
        const email = emailInput.value.trim();
        if (email) {
            const response = await api.post('/api/emails', { email });
            if (response.message) {
                showToast(response.message);
                emailInput.value = '';
                fetchAllData();
            } else {
                showToast(response.error, 'error');
            }
        }
    };

    const handleDeleteEmail = async (e) => {
        if (!e.target.matches('.delete-email-btn')) return;
        const emailId = parseInt(e.target.dataset.id);
        const response = await api.delete(`/api/emails/${emailId}`);
        if (response.message) {
            showToast(response.message);
            fetchAllData();
        } else {
            showToast(response.error, 'error');
        }
    };

    const handleAddSymbol = async () => {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (symbol) {
            const response = await api.post('/api/watchlist', { symbol });
            if (response.message) {
                showToast(response.message);
                symbolInput.value = '';
                fetchAllData();
            } else {
                showToast(response.error, 'error');
            }
        }
    };

    const handleDeleteStock = async (e) => {
        if (!e.target.matches('.delete-stock-btn')) return;
        const stockId = parseInt(e.target.dataset.id);
        const response = await api.delete(`/api/watchlist/${stockId}`);
        if(response.message){
            showToast(response.message);
            fetchAllData();
        } else {
            showToast(response.error, 'error');
        }
    };

    const handleOpenSettings = (e) => {
        if (!e.target.matches('.settings-btn')) return;
        currentWatchlistId = parseInt(e.target.dataset.id);
        renderModalContent();
        settingsModal.style.display = 'block';
    };

    const handleAddTarget = async (e) => {
        e.preventDefault();
        const target_type = targetTypeSelect.value;
        const percentage = parseFloat(targetPercentageInput.value);
        if (!percentage || percentage <= 0) {
            showToast("Please enter a positive percentage.", 'error');
            return;
        }

        const newTarget = await api.post('/api/price_targets', {
            watchlist_id: currentWatchlistId,
            target_type,
            percentage
        });

        if(newTarget.id) {
            showToast('Target added!');
            const stock = watchlistData.find(s => s.id === currentWatchlistId);
            stock.targets.push(newTarget);
            renderModalContent();
            addTargetForm.reset();
        } else {
            showToast(newTarget.error, 'error');
        }
    };

    const handleDeleteTarget = async (e) => {
        if (!e.target.matches('.delete-target-btn')) return;
        const targetId = parseInt(e.target.dataset.id);
        const response = await api.delete(`/api/price_targets/${targetId}`);

        if(response.message){
            showToast(response.message);
            const stock = watchlistData.find(s => s.id === currentWatchlistId);
            stock.targets = stock.targets.filter(t => t.id !== targetId);
            renderModalContent();
        } else {
            showToast(response.error, 'error');
        }
    };

    const handleSaveNotifications = async () => {
        const selectedCheckboxes = notificationList.querySelectorAll('input[type="checkbox"]:checked');
        const email_ids = Array.from(selectedCheckboxes).map(cb => parseInt(cb.dataset.emailId));

        const response = await api.put(`/api/notification_preferences/${currentWatchlistId}`, { email_ids });

        if(response.message) {
            showToast(response.message);
            const stock = watchlistData.find(s => s.id === currentWatchlistId);
            stock.subscribed_emails = email_ids;
            settingsModal.style.display = 'none';
        } else {
            showToast(response.error, 'error');
        }
    };

    const handleOpenChart = async (e) => {
        if (!e.target.matches('.symbol-cell')) return;
        const symbol = e.target.dataset.symbol;
        const history = await api.get(`/api/history/${symbol}`);
        if(history && history.labels) {
            renderChart(symbol, history);
        } else {
            alert(`Could not retrieve historical data for ${symbol}.`);
        }
    };

    // --- Initial Setup & Listeners ---
    addEmailBtn.addEventListener('click', handleAddEmail);
    emailList.addEventListener('click', handleDeleteEmail);
    addSymbolBtn.addEventListener('click', handleAddSymbol);
    watchlistTableBody.addEventListener('click', (e) => {
        handleDeleteStock(e);
        handleOpenSettings(e);
        handleOpenChart(e);
    });
    closeSettingsBtn.addEventListener('click', () => settingsModal.style.display = 'none');
    closeChartBtn.addEventListener('click', () => chartModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if(e.target === settingsModal) settingsModal.style.display = 'none';
        if(e.target === chartModal) chartModal.style.display = 'none';
    });
    addTargetForm.addEventListener('submit', handleAddTarget);
    targetsList.addEventListener('click', handleDeleteTarget);
    saveNotificationPrefsBtn.addEventListener('click', handleSaveNotifications);

    fetchAllData();

    // Re-implement unchanged handlers to keep code self-contained
    const reImplement = () => { /* The existing handler code goes here */ };
    reImplement(); // Just to avoid linting errors in this diff
});
