$(document).ready(function () {
	var rows = $("#items tbody tr");

	$("#itemsSearchInput").on("input", function() {
		var searchTerm = $(this).val().toLocaleUpperCase();
		var visibleRows = 0;

		rows.each(function() {
			var row = $(this);
			var matchesSearch = row.text().toLocaleUpperCase().indexOf(searchTerm) !== -1;

			row.toggle(matchesSearch);
			if (matchesSearch)
				visibleRows++;
		});

		$("#sortiment-count").text(
			searchTerm ? visibleRows + "/" + rows.length : rows.length
		);
	});
});
