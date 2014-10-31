import os
import sys
import argparse
import logging
import logging.handlers

try:
	import ConfigParser as configparser
except ImportError:
	import configparser

import app
import daemon.runner

parser = argparse.ArgumentParser()
parser.add_argument("--if", default="0.0.0.0", dest="interface", help="Interface the webserver is accessable from")
parser.add_argument("--port", default=8080, type=int, dest="port", help="Port the webserver is accessable on")

parser.add_argument("--config", default=None, dest="config", help="File that stores configuration parameters")
parser.add_argument("--debug", default=False, dest="debug", action='store_true', help="Make the server run in debug mode")

argv = []
if len(sys.argv) > 2:
	argv = sys.argv[2:]
args = parser.parse_args(argv)

if args.debug:
	# Log to the console in debug mode
	logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s - %(message)s")
log = logging.getLogger()

base_path = "~/.queenbee/"
base_path = os.path.expanduser(base_path)

# Configure logging to file
log_path = os.path.join(base_path, "log")
log_file = os.path.join(log_path, "queenbee.log")

if not os.path.exists(log_path):
	os.makedirs(log_path)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.handlers.TimedRotatingFileHandler(log_file, when='midnight')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

# Load the config file
config_files = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "default.conf")]
config = configparser.ConfigParser()

if not args.config is None:
	args.config = os.path.expanduser(args.config)
	config_files.append(args.config)

for config_file in config_files:
	with open(config_file, 'r') as f:
		log.info('Loading config file "%s"' % config_file)
		config.readfp(f)
args.config = config

# Start up the daemon process
try:
	app = app.App("queenbee.pid", args)
	if args.debug:
		app.run()
	else:
		runner = daemon.runner.DaemonRunner()
		runner.daemon_context.files_preserve=[handler.stream]
		runner.do_action()
except Exception as ex:
	log.exception(ex)
