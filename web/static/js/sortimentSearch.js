$(document).ready(function () {
	$("#items").tablesorter();

	$("#itemsSearchInput").on("keyup", function() {
		var value = $(this).val();
		var rows = $("table tr");

		if (rows.length == 1)
			return;

		var count = 0;

		rows.each(function(index) {
			if (index !== 0) {

				$row = $(this);

				var id = $row.find("td").text();

				if (id.toUpperCase().indexOf(value.toUpperCase()) !== -1) {
					$row.show();
					count++;
				}
				else {
					$row.hide();
				}

				if(index == (rows.length - 1) && value != "")
					$("#sortiment-count").text("(" + count + "/" + (rows.length - 1) + ")");
				else
					$("#sortiment-count").text("(" + (rows.length - 1) + ")");
			}
		});
	});
});
