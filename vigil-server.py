# https://github.com/deadbits/vigil-llm
import time
import argparse
from typing import Any

from loguru import logger  # type: ignore

from flask import Flask, request, jsonify, abort  # type: ignore

from vigil.core.cache import LRUCache
from vigil.common import timestamp_str
from vigil.vigil import Vigil


logger.add("logs/server.log", format="{time} {level} {message}", level="INFO")

app = Flask(__name__)


def check_field(data, field_name: str, field_type: type, required: bool = True) -> Any:
    field_data = data.get(field_name, None)

    if field_data is None:
        if required:
            logger.error(f'Missing "{field_name}" field')
            return abort(400, f'Missing "{field_name}" field')
        return ""

    if not isinstance(field_data, field_type):
        logger.error(
            f'Invalid data type; "{field_name}" value must be a {field_type.__name__}'
        )
        return abort(
            400,
            f'Invalid data type; "{field_name}" value must be a {field_type.__name__}',
        )

    return field_data


@app.route("/settings", methods=["GET"])
def show_settings():
    """Return the current configuration settings"""
    logger.info(f"({request.path}) Returning config dictionary")
    config_dict = {
        s: dict(vigil.config.config.items(s)) for s in vigil.config.config.sections()
    }

    if "embedding" in config_dict:
        config_dict["embedding"].pop("openai_api_key", None)

    return jsonify(config_dict)


@app.route("/canary/add", methods=["POST"])
def add_canary():
    """Add a canary token to the prompt"""
    logger.info(f"({request.path}) Adding canary token to prompt")

    prompt = check_field(request.json, "prompt", str)
    always = check_field(request.json, "always", bool, required=False)
    length = check_field(request.json, "length", int, required=False)
    header = check_field(request.json, "header", str, required=False)

    updated_prompt = vigil.canary_tokens.add(
        prompt=prompt,
        always=always if always else False,
        length=length if length else 16,
        header=header if header else "<-@!-- {canary} --@!->",
    )
    logger.info(f"({request.path}) Returning response")

    return jsonify(
        {"success": True, "timestamp": timestamp_str(), "result": updated_prompt}
    )


@app.route("/canary/check", methods=["POST"])
def check_canary():
    """Check if the prompt contains a canary token"""
    logger.info(f"({request.path}) Checking prompt for canary token")

    prompt = check_field(request.json, "prompt", str)

    result = vigil.canary_tokens.check(prompt=prompt)
    if result:
        message = "Canary token found in prompt"
    else:
        message = "No canary token found in prompt"

    logger.info(f"({request.path}) Returning response")

    return jsonify(
        {
            "success": True,
            "timestamp": timestamp_str(),
            "result": result,
            "message": message,
        }
    )


@app.route("/add/texts", methods=["POST"])
def add_texts():
    """Add text to the vector database (embedded at index)"""
    texts = check_field(request.json, "texts", list)
    metadatas = check_field(request.json, "metadatas", list)

    logger.info(f"({request.path}) Adding text to VectorDB")

    res, ids = vigil.vectordb.add_texts(texts, metadatas)
    if res is False:
        logger.error(f"({request.path}) Error adding text to VectorDB")
        return abort(500, "Error adding text to VectorDB")

    logger.info(f"({request.path}) Returning response")

    return jsonify({"success": True, "timestamp": timestamp_str(), "ids": ids})


@app.route("/analyze/response", methods=["POST"])
def analyze_response():
    """Analyze a prompt and its response"""
    logger.info(f"({request.path}) Received scan request")

    input_prompt = check_field(request.json, "prompt", str)
    out_data = check_field(request.json, "response", str)

    start_time = time.time()
    result = vigil.output_scanner.perform_scan(input_prompt, out_data)
    result["elapsed"] = round((time.time() - start_time), 6)

    logger.info(f"({request.path}) Returning response")

    return jsonify(result)


@app.route("/analyze/prompt", methods=["POST"])
def analyze_prompt() -> Any:
    """Analyze a prompt against a set of scanners"""
    logger.info(f"({request.path}) Received scan request")

    input_prompt = check_field(request.json, "prompt", str)
    cached_response = lru_cache.get(input_prompt)

    if cached_response:
        logger.info(f"({request.path}) Found response in cache!")
        cached_response["cached"] = True
        return jsonify(cached_response)

    start_time = time.time()
    result = vigil.input_scanner.perform_scan(input_prompt, prompt_response="")
    result["elapsed"] = round((time.time() - start_time), 6)

    logger.info(f"({request.path}) Returning response")
    lru_cache.set(input_prompt, result)

    return jsonify(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", help="config file", type=str, required=True)

    args = parser.parse_args()

    vigil = Vigil.from_config(args.config)

    lru_cache = LRUCache(capacity=100)

    app.run(host="0.0.0.0", use_reloader=True)
