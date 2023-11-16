## Datasets

Before you run Vigil, you'll need to [download the embedding datasets from Hugging Face](https://vigil.deadbits.ai/overview/install-vigil/download-datasets) or load the database with your own embeddings.

Embeddings are currently available with three models:

* text-embedding-ada-002
* all-MiniLM-L6-v2
* all-mpnet-base-v2

Make sure you have [git-lfs](https://git-lfs.com) installed before cloning the repos.

```bash
cd data/datasets
git lfs install
git clone <hf repo>
```

> [!NOTE]
> The datasets contain the original text so you can use a Sentence Transformer model of your choosing if you don't want to use the models listed above. Check out the [full documentation](https://vigil.deadbits.ai/overview/install-vigil/download-datasets) for more information.

### Load Datasets into Vector Database

Once downloaded, use the `parquet2vdb` utility to load the embeddings into Vigil's vector database. 

Before you run the command below, make sure you've updated the `conf/server.conf` configuration file. You'll want to configure (at a minimum):

* `embedding.model` - same as embedding model from dataset you are loading
  * Example: `vigil-jailbreak-all-MiniLM-L6-v2` dataset requires `model = all-MiniLM-L6-v2`
  * Example: `vigil-jailbreak-ada-002` requires ``model = openai` and setting `embedding.openai_api_key`

```cd vigil/utils
python -m parquet2vdb --config server.conf -d /path/to/<hf repo>
```