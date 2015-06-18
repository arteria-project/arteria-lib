#! /bin/sh

### BEGIN INIT INFO
# Provides:          runfolder-ws 
# Required-Start:    $local_fs $remote_fs
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: Provides a web service interface on the runfolder monitor service
# Description: Provides a web service interface on the runfolder monitor service
### END INIT INFO

set -e

case "$1" in
  start)
	runfolder-ws
	;;
  stop|reload|restart|force-reload|status)
	;;
  *)
	echo "Usage:  {start|stop|restart|force-reload|status}" >&2
	exit 1
	;;
esac

exit 0
