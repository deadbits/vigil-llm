## Detection Methods 🔍
Submitted prompts are analyzed by the configured `scanners`; each of which can contribute to the final detection.

**Available scanners:**
* Vector database
* YARA / heuristics
* Transformer model
* Prompt-response similarity
* Canary Tokens

### Vector database
The `vectordb` scanner uses a [vector database](https://github.com/chroma-core/chroma) loaded with embeddings of known injection and jailbreak techniques, and compares the submitted prompt to those embeddings. If the prompt scores above a defined threshold, it will be flagged as potential prompt injection.

All embeddings are available on HuggingFace and listed in the `Datasets` section of this document. 

### Heuristics
The `yara` scanner and the accompanying [rules](../data/yara/) act as heuristics detection. Submitted prompts are scanned against the rulesets with matches raised as potential prompt injection.

Custom rules can be used by adding them to the `data/yara` directory.

### Transformer model
The scanner uses the [transformers](https://github.com/huggingface/transformers) library and a HuggingFace model built to detect prompt injection phrases. If the score returned by the model is above a defined threshold, Vigil will flag the analyzed prompt as a potential risk.

* **Model:** [deepset/deberta-v3-base-injection](https://huggingface.co/deepset/deberta-v3-base-injection)

### Prompt-response similarity
The `prompt-response similarity` scanner accepts a prompt and an LLM's response to that prompt as input. Embeddings are generated for the two texts and cosine similarity is used in an attemopt to determine if the LLM response is related to the prompt. Responses that are not similar to their originating prompts may indicate the prompt has designed to manipulate the LLMs behavior.

This scanner uses the `embedding` configuration file settings.

### Relevance filtering
The `relevance` scanner uses an LLM to analyze a submitted prompt by first chunking the prompt then assessing the relevance of each chunk to the whole. Highly irregular chunks may be indicative of prompt injection or other malicious behaviors.

This scanner uses [LiteLLM](https://github.com/BerriAI/litellm) to interact with the models, so you can configure `Vigil` to use (almost) any model LiteLLM supports!
