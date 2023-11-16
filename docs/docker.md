## Docker
A Docker environment is available, although it is currently limited to OpenAI only and the vector database is not persisted between runs.

This [will be expanded](https://github.com/deadbits/vigil-llm/issues/35) in the future. 

### Docker quickstart

Follow the steps below to clone the repository and build/run the container.

```bash
git clone https://github.com/deadbits/vigil-llm
cd vigil-llm
docker build -t vigil .

# set your openai_api_key in docker.conf
vim conf/docker.conf

docker run -v `pwd`/conf/docker.conf:/app/conf/server.conf -p5000:5000 vigil
```
OpenAI embedding datasets are downloaded and loaded into vectordb at container run time.

The API server will be available on 0.0.0.0:5000.