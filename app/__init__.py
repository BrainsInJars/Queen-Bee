import os
import logging
import threading
import atexit
import time
import sqlite3

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

		# Configure communication with the VeriFlame
		bounce_timeout = self.config.getint('VeriFlame', 'bounce_timeout')
		self.veriflame = veriflame.VeriFlame(bouncetime=bounce_timeout)

		database = os.path.expanduser(self.config.get('DEFAULT', 'database'))
		self._init_database(database)

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

	def run(self):
		self.log.info("Starting")
		try:
			self._run()
		except Exception as ex:
			self.log.exception(ex)
		self.log.info("Shutting down")

	def _stop(self):
		self.terminate.set()

	def _run(self):
		atexit.register(self._stop)

		self.veriflame.callback = self._state_callback
		self.veriflame.start()
		ioloop.IOLoop.current().start()

		# TODO post heartbeat
		self.errors = 0
		while not self.terminate.wait(60.0):
			self._heartbeat()

		ioloop.IOLoop.current().stop()
		self.monitor.stop()

	def _heartbeat(self):
		try:
			self.qb.heartbeat()
			self.errors = 0
		except Exception as ex:
			self.log.exception(ex)

		self.errors = self.errors + 1
		if self.errors == 4:
			self._webscript_down(self)

	def _webscript_down(self):
		pass

	def _state_callback(self, state):
		if self.state == state:
			return

		self.state = state
		db = sqlite3.connect(database)
		with db:
			db.execute("INSERT INTO events(occured, type, value) VALUES (?, ?, ?)", (int(1000 * time.time()), 'flame', state))

	def _init_database(self, database):
		db = sqlite3.connect(database)
		with db:
			db.execute('''CREATE TABLE IF NOT EXISTS callees (
				phone TEXT,
				name TEXT,
				PRIMARY KEY(phone)
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
				self.state = self.state[0]

			self.log.info('Last recorded flame state: %d' % (self.state,))
