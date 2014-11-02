(function ($, undefined) {
	"use strict";

	function refresh_events () {
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

	function validate_phone(evt) {
		var value = $(this).val();

		if(value.match(/^(\+?1)?(\d{10})$/i)) {
			$(this).parents('div.form-group').removeClass('has-error');
			$('#add-callee').attr('disabled', false);
		} else {
			$(this).parents('div.form-group').addClass('has-error');
			$('#add-callee').attr('disabled', true);
		}
	}

	function submit_callee(evt) {
		var phone = $('#create-callee input[name=phone]').val();
		var groups = phone.match(/^(\+?1)?(\d{10})$/i);

		if(!groups) {
			return;
		}
		phone = '+1' + groups[2];

		QueenBee.callees.create({
			name: $('#create-callee input[name=name]').val(),
			phone: phone,
			oncall: false
		}).done(function () {
			$('#create-callee').trigger('reset');
			$(this).attr('disabled', true);
			refresh_callees();
		});
	}

	function remove_callee(callee) {
		var name = callee.phone;
		if(callee.name !== "") {
			name = callee.name + ' (' + name + ')';
		}

		return function (evt) {
			if(!confirm("Are you sure you want to delete " + name + " from the on call list?")) {
				return;
			}
			QueenBee.callees.delete(callee.phone).done(refresh_callees);
		};
	}

	function toggle_oncall(evt) {
		QueenBee.callees.update($(this).val(), {oncall: this.checked}).done(refresh_callees);
	}

	function refresh_callees () {
		QueenBee.callees.list().done(function(data) {
			var table = $('#callees-table tbody').empty();

			var oncallcount = 0;
			$.each(data['result'], function(idx, callee) {
				var del = $('<a>')
					.append($('<span>', {'class': "glyphicon glyphicon-trash"}))
					.on('click', remove_callee(callee))
					;

				var oncall = $('<input>', {type: 'checkbox', value: callee.phone, checked: (callee.oncall != 0)})
					.on('change', toggle_oncall)
					;

				if(callee.oncall) {
					oncallcount = oncallcount + 1;
				}

				var row = $('<tr>', {'callee-id': callee.phone})
					.append($('<td>').append(del), $('<td>').text(callee.name), $('<td>').text(callee.phone), $('<td>').append(oncall))
				;

				table.append(row)
			});

			if(oncallcount > 0) {
				$('#alert-no-one-oncall').addClass('hidden');
			} else {
				$('#alert-no-one-oncall').removeClass('hidden');
			}
		});
	}

	$(function () {
		$('#refresh-events').on('click', refresh_events);
		setInterval(refresh_events, 30000);
		refresh_events();

		$('#create-callee input[name=phone]').on('keyup', validate_phone);
		$('#add-callee').on('click', submit_callee);

		setInterval(refresh_callees, 30000);
		refresh_callees();
	});
})(jQuery);
