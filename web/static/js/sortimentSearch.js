$(document).ready(function () {
	$("#items").tablesorter(
			{sortList: [[1, 0]]}
	);

	$("#itemsSearchInput").on("keyup", function() {
		var value = $(this).val();

		$("table tr").each(function(index) {
			if (index !== 0) {

				$row = $(this);

				var id = $row.find("td").text();

				if (id.toUpperCase().indexOf(value.toUpperCase()) !== -1) {
					$row.show();
				}
				else {
					$row.hide();
				}
			}
		});
	});
});

