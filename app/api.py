import logging
import sqlite3

from tornado import web

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

class BaseHandler(web.RequestHandler, object):
	def initialize(self, database=None):
		self.database = database

	def prepare(self):
		if self.request.headers.get("Content-Type", "").startswith("application/json"):
			self.json = json.loads(self.request.body)

		self.log = logging.getLogger(__name__)

		self.db = None
		if self.database:
			self.db = sqlite3.connect(self.database)
			self.db.row_factory = dict_factory

	def on_finish(self):
		if self.db:
			self.db.commit()
			self.db.close()

class EventsHandler(BaseHandler):
	def get(self):
		offset = self.get_argument('offset', None)
		limit = self.get_argument('limit', None)

		eventtype = self.get_argument('type', None)
		start = self.get_argument('start', None)
		end = self.get_argument('end', None)

		where = []
		params = []
		query = "SELECT * FROM events"

		if start and end:
			if start > end:
				raise web.HTTPError(401)

		if not start is None:
			where.append('start>=?')
			params.append(start)

		if not end is None:
			where.append('end<=?')
			params.append(end)

		if eventtype:
			where.append('type=?')
			params.append(eventtype)

		if where:
			query = query + ' WHERE ' + ' '.join(where)

		if limit:
			query = query + ' LIMIT ?'
			params.append(int(limit))

		if offset:
			query = query + ' OFFSET ?'
			params.append(int(offset))

		self.log.debug((query, params))

		cursor = self.db.cursor()
		cursor.execute(query, params)

		self.set_status(200)
		self.write({'success': 1, 'result': cursor.fetchall()})
