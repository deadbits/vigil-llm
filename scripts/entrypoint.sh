#!/bin/bash

set -e

echo "Loading datasets ..."
python loader.py --config /app/conf/server.conf --datasets deadbits/vigil-instruction-bypass-ada-002,deadbits/vigil-jailbreak-ada-002

echo " "
echo "Starting API server ..."
cd /app
exec "$@"
