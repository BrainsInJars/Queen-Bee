var QueenBee = (function (Q, $, undefined) {
	"use strict";

	Q.callees = (function (_) {
		_.list = function () {
			return $.ajax('/api/callees/', {type: "GET"});
		};
		_.get = function (callee_id) {
			return $.ajax('/api/callees/' + encodeURI(callee_id) + '/', {type: "GET"});
		};
		_.create = function (params) {
			return $.ajax('/api/callees/',
				{
					type: "POST",
					dataType: "json",
					data: JSON.stringify(params),
					contentType: "application/json; charset=utf-8"
				});
		};
		_.update = function (callee_id, params) {
			return $.ajax('/api/callees/' + encodeURI(callee_id) + '/',
				{
					type: "POST",
					dataType: "json",
					data: JSON.stringify(params),
					contentType: "application/json; charset=utf-8"
				});
		};
		_.delete = function (callee_id) {
			return $.ajax('/api/callees/' + encodeURI(callee_id) + '/', {type: "DELETE"});
		}

		return _;
	})(Q.calless || {});

	Q.events = (function (_) {
		/*
		start: the earliest time to get events from
		end: the latest time to get events from
		type: the type pf event we are looking for
		limit: maximum number of results to return
		offset: offset into the events
		*/
		_.list = function (context) {
			return $.ajax('/api/events/', {type: "GET", data: context});
		}
		return _;
	})(Q.events || {});

	return Q;
})(QueenBee || {}, jQuery);