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
                helpText.innerHTML = `A unique identifier for the QR code. If left blank, it will be generated from the name. <br>` +
                    `<span class="font-semibold text-primary-600 dark:text-primary-400">Live Link:</span> ` +
                    `<code class="bg-base-100 dark:bg-base-800 px-1.5 py-0.5 rounded font-mono text-xs font-medium">${baseDomain}/qr/${currentSlug}</code> <br>` +
                    `<span class="italic text-font-muted-light dark:text-font-muted-dark">Note: Once printed, the slug should not be changed, as the physical QR code relies on it.</span>`;
            }
        }

        slugInput.addEventListener('input', updatePreview);
        if (nameInput) {
            nameInput.addEventListener('input', updatePreview);
        }

        updatePreview();
    }
});
