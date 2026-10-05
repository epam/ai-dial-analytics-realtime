#!/bin/sh
set -e

# If no args passed to `docker run`,
# then we assume the user is calling the analytics server
if [ $# -lt 1 ]; then
  exec uvicorn aidial_analytics_realtime.app:app \
    --host 0.0.0.0 \
    --port 5000 \
    --timeout-keep-alive "${TIMEOUT_KEEP_ALIVE:-5}"
fi

# Otherwise, we assume the user wants to run his own process,
# for example a `bash` shell to explore the container
exec "$@"
