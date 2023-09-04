# https://github.com/deadbits/vigil-llm
import os
import sys
import argparse
import logging
import pandas as pd

from typing import Dict

from sentence_transformers import SentenceTransformer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def embed(text) -> Dict:
    embedding = []

    try:
        embedding = model.encode(text, device='cuda').tolist()
    except Exception as err:
        logger.error(f'Failed to get sentence-transformers embeddings: {err}')
        return embedding

    return embedding


def process_file(model_name: str, filepath: str):
    df = pd.read_parquet(filepath)
    new_rows = []

    for idx, row in df.iterrows():
        text = row['text']
        result = embed([text])

        if result:
            new_row = {
                'text': text,
                'embedding': result,
                'metadata': {'model': model_name}
            }
            new_rows.append(new_row)

    new_df = pd.DataFrame(new_rows)
    new_filepath = filepath.replace('.parquet', '_new.parquet')
    new_df.to_parquet(new_filepath)
    print(f"Saved new data to {new_filepath}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-f', '--file',
        help='Parquet file to process',
        type=str,
        required=True
    )

    parser.add_argument(
        '-m', '--model',
        help='Sentence-transformers model name',
        type=str,
        required=True
    )

    args = parser.parse_args()

    model_name = args.model

    if not os.path.isfile(args.file):
        logger.error(f"Directory {args.file} does not exist")
        sys.exit(1)

    filepath = args.file

    try:
        model = SentenceTransformer(model_name)
    except Exception as err:
        logger.error(f'Failed to load SentenceTransformer model "{model_name}": {err}')
        sys.exit(1)

    logging.info(f"Processing {filepath} ...")
    process_file(model_name=model_name, filepath=filepath)
