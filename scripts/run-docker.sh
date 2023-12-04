#!/bin/bash

if [ -z "${CONTAINER_ID}" ]; then
    CONTAINER_ID="vigil:latest"
fi

if [ -z "${PORT}" ]; then
    PORT="5000"
fi

# if you've passed a command in then it'll run that instead of the default
if [ -n "$*" ]; then
    echo "Changing entrypoint to: '$*'"
    ENTRYPOINT="-it --entrypoint=$*"
else
    ENTRYPOINT="--detach"
fi

if [ ! -f .dockerenv ]; then
    echo "Creating empty .dockerenv"
    touch .dockerenv
fi

if [ -z "${VIGIL_CONFIG}" ]; then
    echo "Using default docker.conf"
    VIGIL_CONFIG="docker.conf"
elif [ ! -f "./conf/${VIGIL_CONFIG}" ]; then
    echo "Config file ./conf/${VIGIL_CONFIG} does not exist"
    exit 1
fi

# mount the local dir if we're in dev mode
if [ -n "${DEV_MODE}" ]; then
    echo "Running in dev mode"
    DEVMODE='--mount type=bind,src=./,dst=/app'
else
    DEVMODE=''

fi

echo "Running container ${CONTAINER_ID} on port ${PORT} with config file ./conf/${VIGIL_CONFIG}"

#shellcheck disable=SC2086
docker run \
    --name vigil \
    --publish "${PORT}:5000" \
    --env "NLTK_DATA=/data/nltk" \
    --env-file .dockerenv \
    --env "VIGIL_CONFIG=/app/conf/${VIGIL_CONFIG}" \
    --mount "type=bind,src=./conf/${VIGIL_CONFIG},dst=/app/conf/${VIGIL_CONFIG}" \
    --mount "type=bind,src=./data/yara,dst=/app/data/yara" \
    --mount "type=bind,src=./data/nltk,dst=/root/nltk_data" \
    --mount "type=bind,src=./data/torch-cache,dst=/root/.cache/torch/" \
    --mount "type=bind,src=./data/huggingface,dst=/root/.cache/huggingface/" \
    --mount "type=bind,src=./data,dst=/home/vigil/vigil-llm/data" \
    ${DEVMODE} \
    ${ENTRYPOINT} \
    "${CONTAINER_ID}"
