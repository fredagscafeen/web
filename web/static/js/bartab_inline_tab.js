window.addEventListener('load', function() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && !e.shiftKey) {
            const target = e.target;

            // Check if the current focused element is a 'raw_used' field
            if (target.matches('input[name$="-raw_used"]')) {

                // Find the main inline container (supports standard Django and Unfold)
                const inlineGroup = target.closest('#entries-data')
                if (!inlineGroup) return;

                // Grab all currently visible rows (ignoring the hidden empty-form template)
                const rows = Array.from(inlineGroup.querySelectorAll('.form-group:not(.empty-form)'));
                const currentRow = target.closest('.form-group');

                if (currentRow === rows[rows.length - 1]) {
                    e.preventDefault();

                    const addBtn = inlineGroup.querySelector('.add-row a') || inlineGroup.querySelector('a.add-row');

                    if (addBtn) {
                        addBtn.click();

                        // Give the DOM a tiny fraction of a second to render the new row
                        setTimeout(() => {
                            const newRows = Array.from(inlineGroup.querySelectorAll('.form-group:not(.empty-form)'));
                            const newlyAddedRow = newRows[newRows.length - 1];

                            if (newlyAddedRow) {
                                // Find the first interactable input/select in the new row
                                // (This will likely hit your 'added_cash' checkbox or 'raw_added' field)
                                const firstInput = newlyAddedRow.querySelector('input:not([type="hidden"]), select, textarea');
                                if (firstInput) {
                                    firstInput.focus();
                                }
                            }
                        }, 50);
                    }
                }
            }
        }
    });
});
