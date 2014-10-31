(function ($, undefined) {
	"use strict";

	function refresh_events() {
		var states = {
			0: 'Off',
			1: 'Ok',
			2: 'Low Flame',
			4: 'High Flame',
			7: 'Off'
		};

		QueenBee.events.list({limit: 20}).done(function(data) {
			var table = $('#events-table tbody').empty();

			$.each(data['result'], function(idx, evt) {
				var occured = new Date(evt['occured']);

				var row = $('<tr>')
					.append($('<td>').text(occured.toLocaleString()))
					.append($('<td>').text(states[evt['value']]))
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
