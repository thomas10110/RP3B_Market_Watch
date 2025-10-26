document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('email-input');
    const addEmailBtn = document.getElementById('add-email-btn');
    const emailList = document.getElementById('email-list');

    const symbolInput = document.getElementById('symbol-input');
    const addSymbolBtn = document.getElementById('add-symbol-btn');
    const watchlistTableBody = document.querySelector('#watchlist-table tbody');

    // Fetch and display emails
    const fetchEmails = async () => {
        const response = await fetch('/api/emails');
        const emails = await response.json();
        emailList.innerHTML = '';
        emails.forEach(email => {
            const li = document.createElement('li');
            li.textContent = email;
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.addEventListener('click', async () => {
                await fetch('/api/emails', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                fetchEmails();
            });
            li.appendChild(deleteBtn);
            emailList.appendChild(li);
        });
    };

    // Fetch and display watchlist
    const fetchWatchlist = async () => {
        const response = await fetch('/api/watchlist');
        const watchlist = await response.json();
        watchlistTableBody.innerHTML = '';
        watchlist.forEach(item => {
            const row = document.createElement('tr');
            const gainTarget = item.gain_target !== null ? item.gain_target : '';
            const dipTarget = item.dip_target !== null ? item.dip_target : '';
            row.innerHTML = `
                <td>${item.symbol}</td>
                <td>${item.last_price}</td>
                <td>${item.last_updated}</td>
                <td><input type="number" class="gain-target" data-id="${item.id}" placeholder="e.g., 5" value="${gainTarget}"></td>
                <td><input type="number" class="dip-target" data-id="${item.id}" placeholder="e.g., 5" value="${dipTarget}"></td>
                <td><button class="save-target-btn" data-id="${item.id}">Save</button>
                <button class="delete-symbol-btn" data-symbol="${item.symbol}">Delete</button></td>
            `;
            watchlistTableBody.appendChild(row);
        });
    };

    // Event listeners
    addEmailBtn.addEventListener('click', async () => {
        const email = emailInput.value;
        if (email) {
            await fetch('/api/emails', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            emailInput.value = '';
            fetchEmails();
        }
    });

    addSymbolBtn.addEventListener('click', async () => {
        const symbol = symbolInput.value;
        if (symbol) {
            await fetch('/api/watchlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            symbolInput.value = '';
            fetchWatchlist();
        }
    });

    watchlistTableBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('delete-symbol-btn')) {
            const symbol = e.target.dataset.symbol;
            await fetch('/api/watchlist', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            fetchWatchlist();
        }

        if (e.target.classList.contains('save-target-btn')) {
            const watchlist_id = e.target.dataset.id;
            const gain_target = document.querySelector(`.gain-target[data-id="${watchlist_id}"]`).value;
            const dip_target = document.querySelector(`.dip-target[data-id="${watchlist_id}"]`).value;
            await fetch('/api/price_targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ watchlist_id, gain_target, dip_target })
            });
        }
    });

    // Initial data load
    fetchEmails();
    fetchWatchlist();
});
