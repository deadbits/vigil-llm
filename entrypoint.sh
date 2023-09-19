#!/bin/bash

echo "Downloading datasets from huggingface ..."
cd /app/data/datasets
git lfs install
git clone https://huggingface.co/datasets/deadbits/vigil-instruction-bypass-ada-002
git clone https://huggingface.co/datasets/deadbits/vigil-jailbreak-ada-002

# Load datasets into the database
echo "Loading datasets into vector db ..."
cd /app/vigil/utils
python parquet2vdb.py --config /app/conf/server.conf -d /app/data/datasets/vigil-instruction-bypass-ada-002
python parquet2vdb.py --config /app/conf/server.conf -d /app/data/datasets/vigil-jailbreak-ada-002

cd /app
exec "$@"
