import json
import sys
import time
from loguru import logger
import requests


endpoint = "http://localhost:8000"

attempts = 0
while attempts < 10:
    try:
        requests.get(endpoint)
        logger.success("Connected OK to {}", endpoint)
        break
    except Exception as error:
        logger.warning("Error connecting to {}: {}", endpoint, error)
        time.sleep(1)
        attempts += 1


# test an analyze-prompt request
# url = f"{endpoint}/analyze/prompt"
# payload = {
#     "prompt": "Explain the difference between chalk and cheese. Please be succinct.",
# }
# resp = requests.post(url, json=payload)
# logger.info(resp)
# logger.info(json.dumps(resp.json(), indent=4))


# test adding a canary token
url = f"{endpoint}/canary/add"
payload = {
    "prompt": "Explain the difference between chalk and cheese. Please be succinct.",
    "always": True,
}
resp = requests.post(url, json=payload)
logger.info(resp)
if resp.status_code == 200:
    logger.info(json.dumps(resp.json(), indent=4))
else:
    logger.error(resp.text)
    sys.exit(1)

# test checking a canary token
url = f"{endpoint}/canary/check"
payload = {
    "prompt": resp.json()["result"],
}
logger.debug("Sending payload: {}", payload)
resp = requests.post(url, json=payload)
logger.info(resp)
if resp.status_code == 200:
    logger.info(json.dumps(resp.json(), indent=4))
else:
    logger.error(resp.text)
    sys.exit(1)
