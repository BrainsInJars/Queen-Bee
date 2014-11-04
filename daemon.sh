#! /bin/bash
# /etc/init.d/queenbee

### BEGIN INIT INFO
# Provides: queenbee
# Required-Start: $all
# Should-Start: 
# Required-Stop: 
# Should-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Queen Bee monitoring system
# Description: Monitors the state of the BeeKingdom glas furnace
### END INIT INFO

# Activate the python virtual environment
#    . /path_to_virtualenv/activate

DAEMON=/root/Queen-Bee
PARAMS=--config /root/queenbee.conf

case "$1" in
  start)
    echo "Starting server"
	# Start the daemon 
    python $DAEMON start $PARAMS
    ;;
  stop)
    echo "Stopping server"
    # Stop the daemon
    python $DAEMON stop $PARAMS
    ;;
  *)
    # Refuse to do other stuff
    echo "Usage: /etc/init.d/queenbee {start|stop}"
    exit 1
    ;;
esac

exit 0
