import time
import logging
import threading

_PIN_AUTO = 17
_PIN_LOW = 18
_PIN_HIGH = 27

_PIN_RELIGHT = 22
_PIN_OUTPUT = 23

AUTO = 0x1
LOW = 0x2
HIGH = 0x4
OFF = 0x7

class VeriFlame(threading.Thread, object):
	def __init__(self, bouncetime=300):
		super(VeriFlame, self).__init__()

		self._state = 0
		self.bouncetime = bouncetime
		self.log = logging.getLogger('veriflame')

		self.daemon = True
		self.callback = None

		self.event_shutdown = threading.Event()
		self.event_pin_update = threading.Event()

		try:
			import RPi.GPIO as GPIO
			self.GPIO = GPIO
		except ImportError:
			self.GPIO = None

	# Read the current veriflame state
	def state(self):
		return self._state

	# Control miscellaneous output pin
	def output(self, state):
		if self.GPIO is None:
			return

		self.GPIO.output(_PIN_OUTPUT, state)

	# Attempt a relight of the furnace holding power off for holdtime seconds
	def relight(self, holdtime):
		if self.GPIO is None:
			return

		self.GPIO.output(_PIN_RELIGHT, True)
		time.sleep(holdtime)
		self.GPIO.output(_PIN_RELIGHT, False)

	def _read_state(self, pins):
		state = 0
		for index, pin in enumerate(pins):
			if self.GPIO.input(pin) == self.GPIO.HIGH:
				state = state | (1 << index)
		return state

	def run(self):
		if self.GPIO is None:
			return

		def pin_callback(channel):
			self.event_pin_update.set()

		self.GPIO.setmode(self.GPIO.BCM)
		input_pins = [_PIN_AUTO, _PIN_LOW, _PIN_HIGH]
		output_pins = [_PIN_RELIGHT, _PIN_OUTPUT]

		for index, pin in enumerate(input_pins):
			self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)
			self.GPIO.add_event_detect(pin, self.GPIO.BOTH, callback=pin_callback, bouncetime=self.bouncetime)

		for index, pin in enumerate(output_pins):
			self.GPIO.setup(pin, self.GPIO.OUT)
			self.GPIO.output(pin, False)

		# Force a callback on the iteration through the loop
		self.event_pin_update.set()
		while not self.event_shutdown.is_set():
			self.event_pin_update.wait(1.0)
			self.event_pin_update.clear()

			current = self._read_state(input_pins)
			if self._state != current:
				self._state = current

				if self.callback:
					try:
						self.callback(self._state)
					except Exception as ex:
						self.log.exception(ex)

		self.GPIO.cleanup()

	def shutdown(self):
		self.event_shutdown.set()
