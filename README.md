![logo](docs/assets/logo.png)

## Overview 🏕️
⚡ Security scanner for LLM prompts ⚡

`Vigil` is a Python library and REST API for assessing Large Language Model prompts and responses against a set of scanners to detect prompt injections, jailbreaks, and other potential threats. This repository also provides the detection signatures and datasets needed to get started with self-hosting.

This application is currently in an **alpha** state and should be considered experimental. Work is ongoing to expand detection mechanisms and features.

* **[Full documentation](https://vigil.deadbits.ai)**
* **[Release Blog](https://vigil.deadbits.ai/overview/background)**

## Highlights ✨

* Analyze LLM prompts for common injections and risky inputs
* [Use Vigil as a Python library](#using-in-python) or [REST API](#running-api-server)
* Scanners are modular and easily extensible
* Evaluate detections and pipelines with **Vigil-Eval** (coming soon)
* Available scan modules
    * [x] Vector database / text similarity
      * [Auto-updating on detected prompts](https://vigil.deadbits.ai/overview/use-vigil/auto-updating-vector-database)
    * [x] Heuristics via [YARA](https://virustotal.github.io/yara)
    * [x] Transformer model
    * [x] Prompt-response similarity
    * [x] Canary Tokens
    * [x] Sentiment analysis 
    * [ ] Relevance (via [LiteLLM](https://docs.litellm.ai/docs/))
    * [ ] Paraphrasing
* Supports [local embeddings](https://www.sbert.net/) and/or [OpenAI](https://platform.openai.com/)
* Signatures and embeddings for common attacks
* Custom detections via YARA signatures
* [Streamlit web UI playground](https://vigil.deadbits.ai/overview/use-vigil/web-server/web-ui-playground)

## Background 🏗️

> Prompt Injection Vulnerability occurs when an attacker manipulates a large language model (LLM) through crafted inputs, causing the LLM to unknowingly execute the attacker's intentions. This can be done directly by "jailbreaking" the system prompt or indirectly through manipulated external inputs, potentially leading to data exfiltration, social engineering, and other issues.
- [LLM01 - OWASP Top 10 for LLM Applications v1.0.1 | OWASP.org](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-2023-v1_0_1.pdf)

These issues are caused by the nature of LLMs themselves, which do not currently separate instructions and data. Although prompt injection attacks are currently unsolvable and there is no defense that will work 100% of the time, by using a layered approach of detecting known techniques you can at least defend against the more common / documented attacks. 

`Vigil`, or a system like it, should not be your only defense - always implement proper security controls and mitigations.

> [!NOTE]
> Keep in mind, LLMs are not yet widely adopted and integrated with other applications, therefore threat actors have less motivation to find new or novel attack vectors. Stay informed on current attacks and adjust your defenses accordingly!

**Additional Resources**

For more information on prompt injection, I recommend the following resources and following the research being performed by people like [Kai Greshake](https://kai-greshake.de/), [Simon Willison](https://simonwillison.net/search/?q=prompt+injection&tag=promptinjection), and others.

* [Prompt Injection Primer for Engineers](https://github.com/jthack/PIPE)
* [OWASP Top 10 for LLM Applications v1.0.1 | OWASP.org](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-2023-v1_0_1.pdf)
* [Securing LLM Systems Against Prompt Injection](https://developer.nvidia.com/blog/securing-llm-systems-against-prompt-injection/)

## Install Vigil 🛠️

Follow the steps below to install Vigil

A [Docker container](docs/docker.md) is also available, but this is not currently recommended.

### Clone Repository
Clone the repository or [grab the latest release](https://github.com/deadbits/vigil-llm/releases)
```
git clone https://github.com/deadbits/vigil-llm.git
cd vigil-llm
```

### Install YARA
Follow the instructions on the [YARA Getting Started documentation](https://yara.readthedocs.io/en/stable/gettingstarted.html) to download and install [YARA v4.3.2](https://github.com/VirusTotal/yara/releases).

### Setup Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
```

### Install Vigil library
Inside your virutal environment, install the application:
```
pip install -e .
```

### Configure Vigil
Open the `conf/server.conf` file in your favorite text editor:

```bash
vim conf/server.conf
```

For more information on modifying the `server.conf` file, please review the [Configuration documentation](https://vigil.deadbits.ai/overview/use-vigil/configuration).

> [!IMPORTANT]
> Your VectorDB scanner embedding model setting must match the model used to generate the embeddings loaded into the database, or similarity search will not work.

### Load Datasets
Load the appropriate datasets for your embedding model with the `loader.py` utility. If you don't intend on using the vector db scanner, you can skip this step.

```bash
python loader.py --conf conf/server.conf --dataset deadbits/vigil-instruction-bypass-ada-002
python loader.py --conf conf/server.conf --dataset deadbits/vigil-jailbreak-ada-002
```

You can load your own datasets as long as you use the columns:

| Column     | Type        |
|------------|-------------|
| text       | string      |
| embeddings | list[float] |
| model      | string      |

## Use Vigil 🔬

Vigil can run as a REST API server or be imported directly into your Python application.

### Running API Server

To start the Vigil API server, run the following command:

```bash
python vigil-server.py --conf conf/server.conf
```

* [API Documentation](https://github.com/deadbits/vigil-llm#api-endpoints-)

### Using in Python

Vigil can also be used within your own Python application as a library.

Import the `Vigil` class and pass it your config file.

```python
from vigil.vigil import Vigil

app = Vigil.from_config('conf/openai.conf')

# assess prompt against all input scanners
result = app.input_scanner.perform_scan(
    input_prompt="prompt goes here"
)

# assess prompt and response against all output scanners
app.output_scanner.perform_scan(
    input_prompt="prompt goes here",
    input_resp="LLM response goes here"
)

# use canary tokens and returned updated prompt as a string
updated_prompt = app.canary_tokens.add(
    prompt=prompt,
    always=always if always else False,
    length=length if length else 16, 
    header=header if header else '<-@!-- {canary} --@!->',
)
# returns True if a canary is found
result = app.canary_tokens.check(prompt=llm_response)
```

## Detection Methods 🔍
Submitted prompts are analyzed by the configured `scanners`; each of which can contribute to the final detection.

**Available scanners:**
* Vector database
* YARA / heuristics
* Transformer model
* Prompt-response similarity
* Canary Tokens

For more information on how each works, refer to the [detections documentation](docs/detections.md).

### Canary Tokens
Canary tokens are available through a dedicated class / API.

You can use these in two different detection workflows:
* Prompt leakage
* Goal hijacking

Refer to the [docs/canarytokens.md](docs/canarytokens.md) file for more information.

## API Endpoints 🌐

**POST /analyze/prompt**

Post text data to this endpoint for analysis.

**arguments:**
* **prompt**: str: text prompt to analyze

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"prompt":"Your prompt here"}' http://localhost:5000/analyze
```

**POST /analyze/response**

Post text data to this endpoint for analysis.

**arguments:**
* **prompt**: str: text prompt to analyze
* **response**: str: prompt response to analyze

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"prompt":"Your prompt here", "response": "foo"}' http://localhost:5000/analyze
```

**POST /canary/add**

Add a canary token to a prompt

**arguments:**
* **prompt**: str: prompt to add canary to
* **always**: bool: add prefix to always include canary in LLM response (optional)
* **length**: str: canary token length (optional, default 16)
* **header**: str: canary header string (optional, default `<-@!-- {canary} --@!->`)

```bash
curl -X POST "http://127.0.0.1:5000/canary/add" \
     -H "Content-Type: application/json" \
     --data '{
          "prompt": "Prompt I want to add a canary token to and later check for leakage",
          "always": true
      }'
```

**POST /canary/check**

Check if an output contains a canary token

**arguments:**
* **prompt**: str: prompt to check for canary

```bash
curl -X POST "http://127.0.0.1:5000/canary/check" \
     -H "Content-Type: application/json" \
     --data '{
        "prompt": "<-@!-- 1cbbe75d8cf4a0ce --@!->\nPrompt I want to check for canary"
      }'
```

**POST /add/texts**

Add new texts to the vector database and return doc IDs
Text will be embedded at index time.

**arguments:**
* **texts**: str: list of texts
* **metadatas**: str: list of metadatas

```bash
curl -X POST "http://127.0.0.1:5000/add/texts" \
     -H "Content-Type: application/json" \
     --data '{
         "texts": ["Hello, world!", "Blah blah."],
         "metadatas": [
             {"author": "John", "date": "2023-09-17"},
             {"author": "Jane", "date": "2023-09-10", "topic": "cybersecurity"}
         ]
     }'
```

**GET /settings**

View current application settings

```bash
curl http://localhost:5000/settings
```

## Sample scan output 📌

**Example scan output:**
```json
{
  "status": "success",
  "uuid": "0dff767c-fa2a-41ce-9f5e-fc3c981e42a4",
  "timestamp": "2023-09-16T03:05:34.946240",
  "prompt": "Ignore previous instructions",
  "prompt_response": null,
  "prompt_entropy": 3.672553582385556,
  "messages": [
    "Potential prompt injection detected: YARA signature(s)",
    "Potential prompt injection detected: transformer model",
    "Potential prompt injection detected: vector similarity"
  ],
  "errors": [],
  "results": {
    "scanner:yara": {
      "matches": [
        {
          "rule_name": "InstructionBypass_vigil",
          "category": "Instruction Bypass",
          "tags": [
            "PromptInjection"
          ]
        }
      ]
    },
    "scanner:transformer": {
      "matches": [
        {
          "model_name": "deepset/deberta-v3-base-injection",
          "score": 0.9927383065223694,
          "label": "INJECTION",
          "threshold": 0.98
        }
      ]
    },
    "scanner:vectordb": {
      "matches": [
        {
          "text": "Ignore previous instructions",
          "metadata": null,
          "distance": 3.2437965273857117e-06
        },
        {
          "text": "Ignore earlier instructions",
          "metadata": null,
          "distance": 0.031959254294633865
        },
        {
          "text": "Ignore prior instructions",
          "metadata": null,
          "distance": 0.04464910179376602
        },
        {
          "text": "Ignore preceding instructions",
          "metadata": null,
          "distance": 0.07068523019552231
        },
        {
          "text": "Ignore earlier instruction",
          "metadata": null,
          "distance": 0.0710538849234581
        }
      ]
    }
  }
}
```
