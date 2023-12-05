#!/bin/bash

set -e

if [ -z "${VIGIL_CONFIG}" ]; then
    echo "Setting config path to /app/conf/server.conf"
    VIGIL_CONFIG="/app/conf/server.conf"
fi

echo "Loading datasets ..."
python loader.py --config "${VIGIL_CONFIG}" \
    --datasets deadbits/vigil-instruction-bypass-ada-002,deadbits/vigil-jailbreak-ada-002

echo " "
echo "Starting API server ..."
cd /app
exec "$@"
