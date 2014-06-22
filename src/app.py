import os
import logging
import threading
import atexit

import boto

try:
	import RPi.GPIO as GPIO
except ImportError:
	GPIO = None

class App(object):
	def __init__(self, pid, pid_timeout=5, bounce_timeout=0):
		self.log = logging.getLogger(self.__module__)

		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/null'
		self.stderr_path = '/dev/null'
		self.pidfile_path =  os.path.join('/var/run/', pid)
		self.pidfile_timeout = pid_timeout

		self.status = 0
		self.bounce_timeout = bounce_timeout
		self.terminate = threading.Event()

	def run(self):
		self.log.info("Starting")
		try:
			self._run()
		except Exception as ex:
			self.log.exception(ex)
		self.log.info("Shutting down")

	def _pin(self, pin, value):
		previous = self.status
		if value:
			self.status = (1 << pin) | self.status
		else:
			self.status = ~(1 << pin) & self.status

		if self.status == previous:
			return

		self.log.debug("State changed: 0x%02x" % self.status)

	def _change_pin(self, pin):
		self._pin(GPIO.input(pin))

	def _stop(self):
		self.terminate.set()

	def _run(self):
		atexit.register(self._stop)

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)

		# Configure input pins
		for pin in [17, 18, 27]:
			self.log.info("Configuring GPIO%02d" % (pin,))

			try:
				GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

				self._pin(pin, GPIO.input(pin))

				GPIO.add_event_detect(pin, GPIO.BOTH, bouncetime=self.bounce_timeout)
				GPIO.add_event_callback(pin, self._change_pin)
			except Exception as ex:
				self.log.exception(ex)
				self.log.info("Skipping GPIO%02d" % (pin,))

		# Set the relay output
		GPIO.setup(22, GPIO.OUT)
		GPIO.output(22, True)

		# TODO post heartbeat
		while not self.terminate.wait(1.0):
			for pin in [17, 18, 27]:
				self._pin(pin, GPIO.input(pin))
			self.log.info("Heartbeat")

		GPIO.cleanup()
