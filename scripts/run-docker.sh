#!/bin/bash

if [ -z "${CONTAINER_ID}" ]; then
    CONTAINER_ID="vigil-llm:latest"
fi

if [ -z "${PORT}" ]; then
    PORT="5000"
    fi

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

if [ -z "${CONFIG_FILE}" ]; then
    CONFIG_FILE="server.conf"
fi

echo "Running container ${CONTAINER_ID} on port ${PORT} with config file ./conf/${CONFIG_FILE}"


#shellcheck disable=SC2086
docker run \
    --name vigil-llm \
    --publish "${PORT}:5000" \
    --detach \
    --env "NLTK_DATA=/data/nltk" \
    --env-file .dockerenv \
    --mount "type=bind,src=./data/nltk,dst=/root/nltk_data" \
    --mount "type=bind,src=./conf/${CONFIG_FILE},dst=/app/conf/server.conf" \
    --mount "type=bind,src=./data/torch-cache,dst=/root/.cache/torch/" \
    --mount "type=bind,src=./data/huggingface,dst=/root/.cache/huggingface/" \
    --mount "type=bind,src=./data,dst=/home/vigil/vigil-llm/data" \
    --mount "type=bind,src=./,dst=/app" \
    --restart always \
    ${ENTRYPOINT} \
    "${CONTAINER_ID}"