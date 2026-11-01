/**
 * Code for updating the preview link while typing the qr code slug
 */

document.addEventListener('DOMContentLoaded', function() {
    const slugInput = document.getElementById('id_slug');
    const nameInput = document.getElementById('id_name');

    if (slugInput) {
        let helpText = slugInput.closest('.grow.relative').querySelector('.leading-relaxed.mt-2.text-xs');

        const baseDomain = window.location.origin;

        function slugifyText(text) {
            return text.toString().toLowerCase().trim()
                .replace(/\s+/g, '-')
                .replace(/[^\w\-]+/g, '')
                .replace(/\-\-+/g, '-');
        }

        function updatePreview() {
            let currentSlug = slugInput.value;
            if (!currentSlug && nameInput) {
                currentSlug = slugifyText(nameInput.value);
            }
            currentSlug = currentSlug || '<slug>';

            if (helpText) {
                helpText.replaceChildren(
                    document.createTextNode(
                        'A unique identifier for the QR code. If left blank, it will be generated from the name. '
                    ),
                    document.createElement('br'),
                    (() => {
                        const liveLinkLabel = document.createElement('span');
                        liveLinkLabel.className = 'font-semibold text-primary-600 dark:text-primary-400';
                        liveLinkLabel.textContent = 'Live Link:';
                        return liveLinkLabel;
                    })(),
                    document.createTextNode(' '),
                    (() => {
                        const liveLink = document.createElement('code');
                        liveLink.className = 'bg-base-100 dark:bg-base-800 px-1.5 py-0.5 rounded font-mono text-xs font-medium';
                        liveLink.textContent = `${baseDomain}/qr/${currentSlug}`;
                        return liveLink;
                    })(),
                    document.createTextNode(' '),
                    document.createElement('br'),
                    (() => {
                        const note = document.createElement('span');
                        note.className = 'italic text-font-muted-light dark:text-font-muted-dark';
                        note.textContent = 'Note: Once printed, the slug should not be changed, as the physical QR code relies on it.';
                        return note;
                    })()
                );
            }
        }

        slugInput.addEventListener('input', updatePreview);
        if (nameInput) {
            nameInput.addEventListener('input', updatePreview);
        }

        updatePreview();
    }
});
