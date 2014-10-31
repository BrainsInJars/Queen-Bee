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

		self.state = 0
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

	# Fwr the current veriflame state
	def state(self):
		return self.state

	# Control miscellaneous output pin
	def output(self, state):
		if self.GPIO is None:
			return

		self.GPIO.output(_PIN_OUTPUT, state)

	# Attempt a relight of the furnace holding power off for holdtime seconds
	def relight(self, holdtime):
		if self.GPIO is None:
			return

		self.log.info("Starting relight")
		self.GPIO.output(_PIN_RELIGHT, True)
		time.sleep(holdtime)
		self.GPIO.output(_PIN_RELIGHT, False)
		self.log.info("Finished relight")

	def run(self):
		if self.GPIO is None:
			return

		def pin_callback(channel):
			self.event_pin_update.set()

		self.GPIO.setmode(self.GPIO.BCM)
		input_pins = [_PIN_AUTO, _PIN_LOW, _PIN_HIGH]
		output_pins = [_PIN_RELIGHT, _PIN_OUTPUT]

		self.state = 0
		for index, pin in enumerate(input_pins):
			self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)
			self.GPIO.add_event_detect(pin, self.GPIO.BOTH, callback=pin_callback, bouncetime=self.bouncetime)

			if self.GPIO.input(pin) == self.GPIO.HIGH:
				self.state = self.state | (1 << index)

		for pin in output_pins:
			self.GPIO.setup(pin, self.GPIO.OUT)
			self.GPIO.output(pin, False)

		while not self.event_shutdown.is_set():
			self.event_pin_update.wait(1.0)
			self.event_pin_update.clear()

			current = 0
			for index, pin in enumerate(input_pins):
				if self.GPIO.input(pin) == self.GPIO.HIGH:
					current = current | (1 << index)

			if self.state != current:
				self.state = current

				if self.callback:
					self.callback(self.state)

		self.GPIO.cleanup()

	def shutdown(self):
		self.event_shutdown.set()
