# https://github.com/deadbits/vigil-llm
import json
import os
import time
import argparse
from typing import Any, Dict, List

from loguru import logger  # type: ignore

from flask import Flask, Response, request, jsonify, abort
from pydantic import BaseModel, Field

from vigil.core.cache import LRUCache
from vigil.common import timestamp_str
from vigil.vigil import Vigil


logger.add("logs/server.log", format="{time} {level} {message}", level="INFO")

lru_cache = LRUCache(capacity=100)
app = Flask(__name__)


def check_field(
    data: Any, field_name: str, field_type: type, required: bool = True
) -> Any:
    """validate field input/type, takes the input from the request.json dict"""
    field_data = data.get(field_name, None)

    if field_data is None:
        if required:
            logger.error(f'Missing "{field_name}" field')
            abort(400, f'Missing "{field_name}" field')
        return ""

    if not isinstance(field_data, field_type):
        logger.error(
            f'Invalid data type; "{field_name}" value must be a {field_type.__name__}'
        )
        abort(
            400,
            f'Invalid data type; "{field_name}" value must be a {field_type.__name__}',
        )

    return field_data


@app.route("/settings", methods=["GET"])
def show_settings() -> Response:
    """Return the current configuration settings, but drop the OpenAI API key if it's there"""
    logger.info("({}) Returning config dictionary", request.path)
    config_dict = vigil._config.model_dump(exclude_none=True, exclude_unset=True)

    # don't return the OpenAI API key
    if "embedding" in config_dict:
        config_dict["embedding"].pop("openai_key", None)

    return jsonify(config_dict)


@app.route("/canary/list", methods=["GET"])
def list_canaries() -> Response:
    """Return the current canary tokens"""
    logger.info("({}) Returning canary tokens", request.path)
    return jsonify(vigil.canary_tokens.tokens)


class CanaryTokenRequest(BaseModel):
    """validate canary token request"""

    prompt: str
    always: bool = Field(False)
    length: int = Field(16)
    header: str = Field("<-@!-- {canary} --@!->")


@app.route("/canary/add", methods=["POST"])
def add_canary() -> Response:
    """Add a canary token to the system"""
    try:
        if request.json is None:
            abort(400, "No JSON data in request")
        canary = CanaryTokenRequest(**request.json)
    except ValueError as ve:
        logger.error("Failed to validate add_canary request: {}", ve)
        abort(400, f"Failed to validate request: {ve}")
    logger.info("({}) Adding canary token to prompt", request.path)

    updated_prompt = vigil.canary_tokens.add(
        prompt=canary.prompt,
        always=canary.always,
        length=canary.length,
        header=canary.header,
    )
    logger.info("({}) Returning response", request.path)

    return jsonify(
        {"success": True, "timestamp": timestamp_str(), "result": updated_prompt}
    )


@app.route("/canary/check", methods=["POST"])
def check_canary():
    """Check if the prompt contains a canary token"""
    logger.info("({}) Checking prompt for canary token", request.path)

    prompt = check_field(request.json, "prompt", str)

    result = vigil.canary_tokens.check(prompt=prompt)
    if result:
        message = "Canary token found in prompt"
    else:
        message = "No canary token found in prompt"

    logger.info("({}) Returning response", request.path)

    return jsonify(
        {
            "success": True,
            "timestamp": timestamp_str(),
            "result": result,
            "message": message,
        }
    )


class TextRequest(BaseModel):
    """used with /add/texts"""

    texts: List[str]
    metadatas: List[Dict[str, str]]


@app.route("/add/texts", methods=["POST"])
def add_texts() -> Response:
    """Add text to the vector database (embedded at index)"""
    try:
        if request.json is None:
            abort(400, "No JSON data in request")
        text_request = TextRequest(**request.json)
    except ValueError as ve:
        logger.error("({}) Failed to validate add_texts request: {}", request.path, ve)
        abort(400, f"Failed to validate request: {ve}")

    logger.info("({}) Adding text to VectorDB", request.path)

    if vigil.vectordb is None:
        abort(500, "No VectorDB loaded")
    res, ids = vigil.vectordb.add_texts(text_request.texts, text_request.metadatas)
    if res is False:
        logger.error("({}) Error adding text to VectorDB", request.path)
        return abort(500, "Error adding text to VectorDB")

    logger.info("({}) Returning response", request.path)

    return jsonify({"success": True, "timestamp": timestamp_str(), "ids": ids})


class AnalyzeRequest(BaseModel):
    """used with /analyze/response"""

    prompt: str
    response: str


@app.route("/analyze/response", methods=["POST"])
def analyze_response():
    """Analyze a prompt and its response"""
    logger.info("({}) Received scan request", request.path)

    try:
        analyze_request = AnalyzeRequest(**request.json)
    except ValueError as ve:
        logger.error(
            "({}) Failed to validate analyze_response request: {}", request.path, ve
        )
        abort(400, f"Failed to validate request: {ve}")

    start_time = time.time()
    result = vigil.output_scanner.perform_scan(
        analyze_request.prompt, analyze_request.response
    )
    result["elapsed"] = round((time.time() - start_time), 6)

    logger.info("({}) Returning response: {}", request.path, json.dumps(result))

    return jsonify(result)


@app.route("/analyze/prompt", methods=["POST"])
def analyze_prompt() -> Any:
    """Analyze a prompt against a set of scanners"""
    logger.info("({}) Received scan request", request.path)

    input_prompt = check_field(request.json, "prompt", str)
    cached_response = lru_cache.get(input_prompt)

    if cached_response:
        logger.info("({}) Found response in cache!", request.path)
        cached_response["cached"] = True
        return jsonify(cached_response)

    start_time = time.time()
    result = vigil.input_scanner.perform_scan(input_prompt, prompt_response="")
    result["elapsed"] = round((time.time() - start_time), 6)

    logger.info("({}) Returning response", request.path)
    lru_cache.set(input_prompt, result)

    return jsonify(result)


@app.route("/cache/clear", methods=["POST"])
def cache_clear() -> str:
    logger.info("({}) Clearing cache", request.path)
    lru_cache.empty()
    return "Cache cleared"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", help="config file", type=str, required=False)

    args = parser.parse_args()
    if not args.config:
        args.config = os.getenv("VIGIL_CONFIG")

    vigil = Vigil.from_config(args.config)

    app.run(host="0.0.0.0", use_reloader=True)
