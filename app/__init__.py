import os
import logging
import threading
import atexit
import time
import sqlite3

from operator import itemgetter

import api
import veriflame
import queenbee

from twilio import rest
from tornado import web, ioloop, httpserver

working = os.path.expanduser('~/.queenbee')
database = os.path.join(working, 'queenbee.db')

def resources_dir(*args):
	return os.path.join(os.path.abspath(os.path.dirname(os.path.abspath(__file__))), *args)

class App(object):
	def __init__(self, pid, args, pid_timeout=5):
		self.config = args.config
		self.log = logging.getLogger()

		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/null'
		self.stderr_path = '/dev/null'
		self.pidfile_path =  os.path.join('/var/run/', pid)
		self.pidfile_timeout = pid_timeout

		self.terminate = threading.Event()

		# Configure external services
		self.qb = queenbee.QueenBee(self.config.get('QueenBee', 'key'), self.config.get('QueenBee', 'secret'))
		self.twilio = rest.TwilioRestClient(self.config.get('Twilio', 'key'), self.config.get('Twilio', 'secret'))

		self.twilio_from = self.config.get('Twilio', 'from')

		self.network = 0
		self.notify_on_recovery = False

		# Configure communication with the VeriFlame
		bounce_timeout = self.config.getint('VeriFlame', 'bounce_timeout')
		self.veriflame = veriflame.VeriFlame(bouncetime=bounce_timeout)

		self.database = os.path.expanduser(self.config.get('DEFAULT', 'database'))
		self._init_database(self.database)

		self.application = web.Application([
			# Static content handlers
			(r'/', web.RedirectHandler, {'url': '/index.html'}),
			(r'/(.*\.html)?', web.StaticFileHandler, {'path': resources_dir()}),
			(r'/js/(.*\.js)', web.StaticFileHandler, {'path': resources_dir('js')}),
			(r'/css/(.*\.css)', web.StaticFileHandler, {'path': resources_dir('css')}),
			(r'/images/(.*)', web.StaticFileHandler, {'path': resources_dir('images')}),

			(r'/api/events/', api.EventsHandler, {'database': database}),
		], debug = args.debug)

		self.server = httpserver.HTTPServer(self.application)
		self.server.listen(args.port, address=args.interface)
		self.log.info('Webserver listening on %s:%d' % (args.interface, args.port))

	def open_db(self):
		db = sqlite3.connect(self.database)
		db.row_factory = api.dict_factory
		return db

	def run(self):
		self.log.info("Starting")

		atexit.register(self._stop)

		try:
			self._run()
		except Exception as ex:
			self.log.exception(ex)

		self.log.info("Shutting down")

	def _stop(self):
		self.terminate.set()

	def _run(self):
		self.veriflame.callback = self._state_callback
		self.veriflame.start()

		loop = ioloop.IOLoop.instance()
		loop_thread = threading.Thread(target=loop.start)
		loop_thread.daemon = True
		loop_thread.start()

		self._heartbeat()

		loop.stop()
		self.veriflame.stop()

	def _heartbeat(self):
		errors = 0
		while not self.terminate.wait(60.0):
			try:
				self.qb.heartbeat()

				if self.network == 1:
					self._sms(self._get_callees(), 'webscript.io is back up')
					self._log_event('webscript', 1)
				elif self.network == 2:
					if self.notify_on_recovery:
						self.qb.message = self._get_message(self.state)
						self._call(self._get_callees())
					self._log_event('network', 1)

				self.network = 0
				errors = 0
			except Exception as ex:
				self.log.exception(ex)

			errors = errors + 1
			if errors == 4:
				self.network = 1

				try:
					self._sms(self._get_callees(), 'webscript.io is down')
					self._log_event('webscript', 0)
				except Exception as ex:
					self.log.exception(ex)
					self._log_event('network', 0)

	def _sms(self, callees, message):
		for callee in callees:
			self.twilio.messages.create(to=callee, from_=self.twilio_from, body=message)

	def _call(self, callees):
		callback = self.qb.conference_url

		self.log.info('Outbound callback: %s' % callback)
		for callee in callees:
			self.twilio.calls.create(to=callee, from_=self.twilio_from, url=callback)

	def _get_message(self, state):
		return {
			veriflame.AUTO: 'The furnace flame is OK',
			veriflame.LOW: 'The furnace flame is low',
			veriflame.HIGH: 'The furnace flame is high',
			veriflame.OFF: 'The furnace is off',
		}.get('', 'The furnace is in an unknown state')

	def _get_callees(self):
		with self.open_db() as db:
			cursor = db.cursor()
			cursor.execute("SELECT phone FROM callees WHERE oncall=1")
			callees = map(itemgetter('phone'), cursor.fetchall())
		return callees

	def _log_event(self, eventtype, value):
		with self.open_db() as db:
			db.execute("INSERT INTO events(occured, type, value) VALUES (?, ?, ?)", (int(1000 * time.time()), eventtype, value))

	def _state_callback(self, state):
		if self.state == state:
			return

		self._log_event('flame', state)
		self.message = self._get_message(state)
		if self.network == 0:
			self.qb.message = self.message

		if self.state == veriflame.AUTO:
			if state != veriflame.OFF:
				# Attempt a relight
				self._log_event('relight', 1)
				self.veriflame.relight(2.0)
				self._log_event('relight', 0)

				if self.network == 1:
					self._sms(self._get_callees(), self.message)
				elif self.network == 2:
					self.notify_on_recovery = True
				else:
					self._call(self._get_callees())

		elif state == veriflame.AUTO:
			self.notify_on_recovery = False
			if self.state != veriflame.OFF:
				if self.network == 0:
					self._call(self._get_callees())
				elif self.network == 1:
					self._sms(self._get_callees(), self.message)

		self.state = state

	def _init_database(self, database):
		with self.open_db() as db:
			db.execute('''CREATE TABLE IF NOT EXISTS callees (
				phone TEXT PRIMARY KEY,
				name TEXT,
				oncall INTEGER
			)''')

			db.execute('''CREATE TABLE IF NOT EXISTS events (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				occured INTEGER,
				type TEXT,
				value INTEGER
			)''')

			cursor = db.cursor()
			cursor.execute("SELECT value FROM events WHERE type='flame' ORDER BY occured DESC LIMIT 1");

			self.state = cursor.fetchone()
			if self.state is None:
				self.state = veriflame.OFF

				db.execute("INSERT INTO events(occured, type, value) VALUES (?, ?, ?)", (int(1000 * time.time()), 'flame', self.state))
			else:
				self.state = self.state['value']

			self.log.info('Last recorded flame state: %d' % (self.state,))
