document.addEventListener('keydown', function(e) {
    // Ctrl+Shift+K or Alt+K
    if ((e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k') ||
        (e.altKey && e.key.toLowerCase() === 'k')) {
        e.preventDefault();
        const searchRow = document.getElementById('search-row');
        if (searchRow) {
            searchRow.style.display = '';
            // Focus the search box if present
            const searchBox = searchRow.querySelector('textarea');
            if (searchBox) searchBox.focus();
        }
    }
    // Hide on Escape
    if (e.key === "Escape") {
        const searchRow = document.getElementById('search-row');
        if (searchRow) searchRow.style.display = 'none';
    }
});