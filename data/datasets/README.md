# Datasets

Before you run Vigil, you'll need to download the embedding datasets from the table below or load the database with your own embeddings.

Embeddings are currently available with two models:
* `text-embedding-ada-002`
* `all-MiniLM-L6-v2`

Make sure you have [git-lfs](https://git-lfs.com) installed before cloning the repos.

```bash
cd data/datasets
git lfs install
git clone <hf repo>
```

| Repo | Description | Model |
| ---- | ----------- | ----- |
| [vigil-instruction-bypass-ada-002](https://huggingface.co/datasets/deadbits/vigil-instruction-bypass-ada-002) | Instruction bypass style prompt injections | `text-embedding-ada-002`
| [vigil-jailbreaks-ada-002](https://huggingface.co/datasets/deadbits/vigil-jailbreak-ada-002) | Common jailbreak prompts | `text-embedding-ada-002`
| [vigil-instruction-bypass-all-MiniLM-L6-v2](https://huggingface.co/datasets/deadbits/vigil-instruction-bypass-all-MiniLM-L6-v2) | Instruction bypass style prompt injections | `all-MiniLM-L6-v2`
| [vigil-jailbreaks-all-MiniLM-L6-v2](https://huggingface.co/datasets/deadbits/vigil-jailbreak-all-MiniLM-L6-v2) | Common jailbreak prompts | `all-MiniLM-L6-v2`

> [!NOTE]
> The datasets contain the original text so you can use a Sentence Transformer model of your choosing if you don't want to use OpenAI or all-MiniLM-L6-v2. Support for additional embeddings will be added in the future.

### Load Datasets into Vector Database

Once downloaded, use the `parquet2vdb` utility to load the embeddings into Vigil's vector database:

```bash
cd vigil/utils
python -m parquet2vdb --config server.conf -d /path/to/<hf repo>
```

### Configure Vigil

Open the `server.conf` file in your favorite text editor:

```bash
vim server.conf
```

Modify the configuration options according to your needs. This includes setting up your preferred embedding model, scanners, and other settings.

> [!IMPORTANT]
> Your VectorDB scanner embedding model setting must match the model used to generate the embeddings loaded into the database, or similarity search will not work. For example, if you used the Vigil datasets (above), the `model` field must be set to `openai` or ``all-MiniLM-L6-v2`.

If you want to use the Vigil datasets with a different Sentence Transformers model, you can still download the datasets but prior to running `utils.parquet2vdb` execute the `utils.parquet2emb.py` script to load the Parquet files and embed the text with the model of your choice. This creates a new Parquet dataset you can load into the database using `utils.parqeut2vdb` [^1].

[^1]: Alternatively, you can skip `parquet2emb` and run `parquet2vdb` directly. But this will only load the embeddings into the database, you will not have a clean copy of the data saved to disk outside of ChromaDB.
