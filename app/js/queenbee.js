var QueenBee = (function (Q, $, undefined) {
	"use strict";

	Q.callees = (function (_) {
		_.list = function () {
			return $.ajax('/api/callees/', {type: "GET"});
		};

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