(function () {
    function updateSuggestedSellingPrice() {
        const purchasePriceField = document.getElementById("id_purchasePriceInDKK");
        const suggestedPriceField = document.getElementById("suggested-selling-price");

        if (!purchasePriceField || !suggestedPriceField) {
            return;
        }

        const purchasePrice = Number.parseFloat(purchasePriceField.value);
        if (!Number.isFinite(purchasePrice)) {
            suggestedPriceField.textContent = "";
            return;
        }

        const suggestedPrice = Math.ceil((purchasePrice * 1.25) / 5) * 5;
        suggestedPriceField.textContent = String(suggestedPrice);
    }

    document.addEventListener("DOMContentLoaded", function () {
        const purchasePriceField = document.getElementById("id_purchasePriceInDKK");
        if (!purchasePriceField) {
            return;
        }

        purchasePriceField.addEventListener("input", updateSuggestedSellingPrice);
        purchasePriceField.addEventListener("change", updateSuggestedSellingPrice);
    });
})();
