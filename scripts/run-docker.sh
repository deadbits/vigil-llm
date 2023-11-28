#!/bin/bash

if [ -n "$*" ]; then
    echo "Changing entrypoint to: $*"
    ENTRYPOINT="--entrypoint='$*'"
else
    ENTRYPOINT=""
fi

if [ ! -f .dockerenv ]; then
    echo "Creating empty .dockerenv"
    touch .dockerenv
fi


CONFIG_FILE="server.conf"

#shellcheck disable=SC2086
docker run --rm -it \
    --name vigil-llm \
    --env "NLTK_DATA=/data/nltk" \
    --env-file .dockerenv \
    --mount "type=bind,src=./data/nltk,dst=/root/nltk_data" \
    --mount "type=bind,src=./conf/${CONFIG_FILE},dst=/app/conf/server.conf" \
    --mount "type=bind,src=./data/torch-cache,dst=/root/.cache/torch/" \
    --mount "type=bind,src=./data/huggingface,dst=/root/.cache/huggingface/" \
    --mount "type=bind,src=./data,dst=/home/vigil/vigil-llm/data" \
    --mount "type=bind,src=./,dst=/app" \
    ${ENTRYPOINT} \
    vigil-llm