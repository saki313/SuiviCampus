/* Scripts applicatifs globaux */

// Restaure le mode sombre au chargement
(function() {
    const dark = localStorage.getItem('darkMode') === 'true';
    if (dark) {
        document.documentElement.dataset.bsTheme = 'dark';
        const toggle = document.getElementById('darkModeToggle');
        if (toggle) toggle.checked = true;
    }
})();

// Helper : badge HTML pour un niveau de risque
window.risqueBadge = function(niveau) {
    const cls = (niveau || '').replace('é', 'e');
    return `<span class="badge badge-risque-${cls}">${niveau || '—'}</span>`;
};

// Helper : formate un nombre avec 1 décimale
window.fmt = function(v, suffixe='') {
    if (v === null || v === undefined) return '—';
    return Number(v).toFixed(1) + suffixe;
};

// Initialisation DataTables avec defaults français
window.initDataTable = function(selector, opts) {
    const defaults = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/fr.json'
        },
        pageLength: 25,
        responsive: true,
    };
    return $(selector).DataTable(Object.assign({}, defaults, opts || {}));
};
