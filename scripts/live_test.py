import json
from loguru import logger
import requests


endpoint = "http://localhost:8000"


while True:
    try:
        requests.get(endpoint)
        logger.success("Connected OK to {}", endpoint)
        break
    except Exception as error:
        logger.warning("Error connecting to {}: {}", endpoint, error)


url = f"{endpoint}/analyze/prompt"
payload = {
    "prompt": "Explain the difference between chalk and cheese. Please be succinct.",
}
resp = requests.post(url, json=payload)
logger.info(resp)
logger.info(json.dumps(resp.json(), indent=4))
