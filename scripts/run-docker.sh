#!/bin/bash

if [ -z "${CONTAINER_ID}" ]; then
    CONTAINER_ID="vigil-llm:latest"
fi

if [ -z "${PORT}" ]; then
    PORT="5000"
    fi

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
    VIGIL_CONFIG="server.conf"
elif [ ! -f "./conf/${VIGIL_CONFIG}" ]; then
    echo "Config file ./conf/${VIGIL_CONFIG} does not exist"
    exit 1
fi

echo "Running container ${CONTAINER_ID} on port ${PORT} with config file ./conf/${VIGIL_CONFIG}"


#shellcheck disable=SC2086
docker run \
    --name vigil-llm \
    --publish "${PORT}:5000" \
    --env "NLTK_DATA=/data/nltk" \
    --env-file .dockerenv \
    --mount "type=bind,src=./data/nltk,dst=/root/nltk_data" \
    --mount "type=bind,src=./data/torch-cache,dst=/root/.cache/torch/" \
    --mount "type=bind,src=./data/huggingface,dst=/root/.cache/huggingface/" \
    --mount "type=bind,src=./data,dst=/home/vigil/vigil-llm/data" \
    --mount "type=bind,src=./conf/${VIGIL_CONFIG},dst=/app/conf/docker.conf" \
    --restart always \
    ${ENTRYPOINT} \
    "${CONTAINER_ID}"
    # --mount "type=bind,src=./,dst=/app" \ # <=- include this line if you want to work on it and mount the app in docker
