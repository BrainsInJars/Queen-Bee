(function ($, undefined) {
	"use strict";

	function refresh_events() {
		QueenBee.events.list({limit: 20}).done(function(data) {
			var table = $('#events-table tbody').empty();

			$.each(data['result'], function(idx, evt) {
				var occured = new Date(evt['occured']);

				var row = $('<tr>')
					.append($('<td>').text(occured.toLocaleString()))
					.append($('<td>').text(evt['type']))
					.append($('<td>').text(evt['value']))
				;
				table.append(row);
			});
		});
	}

	$(function () {
		$('#refresh-events').on('click', refresh_events);

		setInterval(refresh_events, 30000);
		refresh_events();
	});
})(jQuery);
