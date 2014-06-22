import os, sys
import logging
import logging.handlers

import app
import daemon.runner

log = logging.getLogger()

base_path = "~/.queenbee/"
base_path = os.path.expanduser(base_path)

log_path = os.path.join(base_path, "log")
log_file = os.path.join(log_path, "queenbee.log")

if not os.path.exists(log_path):
	os.makedirs(log_path)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.handlers.TimedRotatingFileHandler(log_file, when='midnight')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

try:
	runner = daemon.runner.DaemonRunner(app.App("queenbee.pid"))
	runner.daemon_context.files_preserve=[handler.stream]
	runner.do_action()
except Exception as ex:
	log.exception(ex)
