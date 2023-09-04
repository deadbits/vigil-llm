#!/usr/bin/env python3
# json2parquet.py
# https://github.com/deadbits/vigil-llm
import os
import sys
import json
import argparse
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded JSON from {file_path}")
        return data

    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        return None

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {file_path}")
        return None


def convert_to_parquet(json_data):
    try:
        df = pd.DataFrame(json_data)
        table = pa.table(df)
        logger.info("Successfully converted JSON to Parquet")
        return table
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return None


def save_parquet_to_disk(parquet_table, file_path):
    try:
        pq.write_table(parquet_table, file_path)
        logger.info(f"Successfully saved Parquet to {file_path}")
    except Exception as err:
        logger.error(f"Failed to save Parquet: {err}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-f', '--file',
        help='json file',
        type=str,
        required=True
    )

    parser.add_argument(
        '-o', '--output',
        help='output file',
        type=str,
        required=True,
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        logger.error(f"File {args.file} not found.")
        sys.exit(1)

    if os.path.exists(args.output):
        logger.error(f"Ouput file {args.output} already exists.")
        sys.exit(1)

    json_data = load_json_file(args.file)

    if json_data:
        # Convert JSON to Parquet
        parquet_data = convert_to_parquet(json_data)

        if parquet_data:
            # Save Parquet back to disk
            save_parquet_to_disk(parquet_data, args.output)
