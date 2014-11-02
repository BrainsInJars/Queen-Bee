import re
import json
import logging
import sqlite3
import threading

from operator import itemgetter

from tornado import web

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

class BaseHandler(web.RequestHandler, object):
	def initialize(self, database=None, queenbee=None):
		self.database = database
		self.qb = queenbee

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

class CalleesHandler(BaseHandler):
	def get(self, callee_id=None):
		params = []
		query = "SELECT * FROM callees"

		if not callee_id is None:
			query = query + " WHERE phone=?"
			params.append(callee_id)

		with self.db as db:
			cursor = db.cursor()
			cursor.execute(query, params)
			result = cursor.fetchall()

		self.set_status(200)
		self.write({'success': 1, 'result': result})

	def _create_callee(self, **args):
		phone = args.get('phone', None)
		if phone is None or not re.match(r'^\+1\d{10}$', phone):
			raise web.HTTPError(400)

		sets = []
		params = []
		for key, value in args.items():
			if not key in ['phone', 'name', 'oncall']:
				raise web.HTTPError(400)
			sets.append(key)
			params.append(value)

		insert = 'INSERT INTO callees(' + ','.join(sets) + ') VALUES (' + ','.join(['?']*len(params)) + ')'

		with self.db as db:
			cursor = db.cursor()
			cursor.execute("SELECT count(*) FROM callees WHERE phone=?", (phone,))

			if cursor.fetchone().get('count(*)', 0) > 0:
				raise web.HTTPError(400)

			cursor.execute(insert, params)

		return phone

	def _update_callee(self, callee_id, **args):
		update = 'UPDATE callees'

		sets = []
		params = []
		for key, value in args.items():
			if not key in ['name', 'oncall']:
				raise web.HTTPError(400)

			sets.append(key)
			params.append(value)

		if not sets:
			raise web.HTTPError(400)

		update = update + ' SET ' + ' '.join(['%s=?' % key for key in sets])
		update = update + ' WHERE phone=?'
		params.append(callee_id)

		with self.db as db:
			cursor = db.cursor()
			result = cursor.execute(update, params)
			self.log.info((update, params, result.rowcount))

	def post(self, callee_id=None):
		self.log.info((callee_id, self.json))

		if callee_id is None:
			callee_id = self._create_callee(**self.json)
			self.set_status(201)
		else:
			self._update_callee(callee_id, **self.json)
			self.set_status(202)

		with self.db as db:
			cursor = db.cursor()
			cursor.execute("SELECT phone FROM callees WHERE oncall='1'")

			callees = map(itemgetter('phone'), cursor.fetchall())

		t = threading.Thread(target=setattr, args=[self.qb, 'callees', callees])
		t.daemon = True
		t.start()

		self.redirect('/api/callees/%s/' % callee_id)

	def delete(self, callee_id):
		with self.db as db:
			cursor = db.cursor()
			cursor.execute('DELETE FROM callees WHERE phone=?', (callee_id,))
			if cursor.rowcount == 0:
				raise web.HTTPError(404)

		self.set_status(202)

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

		query = query + ' ORDER BY occured DESC'

		if limit:
			query = query + ' LIMIT ?'
			params.append(int(limit))

		if offset:
			query = query + ' OFFSET ?'
			params.append(int(offset))

		with self.db as db:
			cursor = self.db.cursor()
			cursor.execute(query, params)

			result = cursor.fetchall()

		self.set_status(200)
		self.write({'success': 1, 'result': result})
