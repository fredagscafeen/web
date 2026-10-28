(function () {
    function roundToTwoDecimals(value) {
        return Number(value.toFixed(2));
    }

    function setReadonlyValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.textContent = Number.isFinite(value) ? value.toFixed(2) : "";
        }
    }

    function updateReadonlyFields() {
        const purchasePriceExcludingVATField = document.getElementById(
            "id_purchasePriceInDKKExcludingVAT"
        );
        const priceField = document.getElementById("id_priceInDKK");
        const purchasePriceExcludingVAT = Number.parseFloat(
            purchasePriceExcludingVATField?.value
        );
        const price = Number.parseFloat(priceField?.value);
        const purchasePrice = Number.isFinite(purchasePriceExcludingVAT)
            ? roundToTwoDecimals(purchasePriceExcludingVAT * 1.25)
            : Number.NaN;
        const priceExcludingVAT = Number.isFinite(price)
            ? roundToTwoDecimals(price * 0.8)
            : Number.NaN;

        setReadonlyValue("purchase-price", purchasePrice);
        setReadonlyValue("price-excluding-vat", priceExcludingVAT);

        const suggestedPrice = Number.isFinite(purchasePrice)
            ? roundToTwoDecimals(Math.ceil((purchasePrice * 1.25) / 5) * 5)
            : Number.NaN;
        setReadonlyValue("suggested-selling-price", suggestedPrice);

        const actualProfit =
            Number.isFinite(purchasePrice) && Number.isFinite(price)
                ? priceExcludingVAT -
                  purchasePrice -
                  (price * 0.2 - purchasePrice * 0.25)
                : Number.NaN;
        const roundedActualProfit = Number.isFinite(actualProfit)
            ? roundToTwoDecimals(actualProfit)
            : Number.NaN;
        setReadonlyValue("actual-profit", roundedActualProfit);

        const profitMargin =
            Number.isFinite(purchasePriceExcludingVAT) &&
            Number.isFinite(priceExcludingVAT) &&
            purchasePrice !== 0 &&
            priceExcludingVAT !== 0
                ? ((priceExcludingVAT - purchasePriceExcludingVAT) /
                      priceExcludingVAT) *
                  100
                : Number.NaN;
        setReadonlyValue(
            "profit-margin",
            Number.isFinite(profitMargin)
                ? roundToTwoDecimals(profitMargin)
                : Number.NaN
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        const purchasePriceField = document.getElementById(
            "id_purchasePriceInDKKExcludingVAT"
        );
        const priceField = document.getElementById("id_priceInDKK");
        if (!purchasePriceField && !priceField) {
            return;
        }

        [purchasePriceField, priceField].forEach(function (field) {
            if (field) {
                field.addEventListener("input", updateReadonlyFields);
                field.addEventListener("change", updateReadonlyFields);
            }
        });
        updateReadonlyFields();
    });
})();
