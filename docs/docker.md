## Docker
A Docker environment is available, although it is currently limited to OpenAI only and the vector database is not persisted between runs.

This [will be expanded](https://github.com/deadbits/vigil-llm/issues/35) in the future. 

### Docker quickstart

Follow the steps below to clone the repository and build/run the container.

```bash
git clone https://github.com/deadbits/vigil-llm
cd vigil-llm
./scripts/build-docker.sh

# set your openai_api_key in docker.conf
vim conf/docker.conf

# run the docker instance
./scripts/run-docker.sh
```

OpenAI embedding datasets are downloaded and loaded into vectordb at container run time.

The API server will be available on 0.0.0.0:5000.

### Extra Configuration

The `run-docker.sh` script will take the following environment variables:

- PORT - change the port that's exposed (macOS binds port 5000 by default).
- CONTAINER_ID - if you want to use another container (ie, one in Docker Hub).
- DEV_MODE - set if you're working on the vigil code, it'll mount `./` as `/app` in the container.
- VIGIL_CONFIG - use a different configuration file from `./conf/`

Environment variables inside the container can be set by editing `.dockerenv` - this is useful if you want to set an OPENAI_API_KEY but use the default configuration file.
