# https://github.com/deadbits/vigil-llm
import os
import sys
import argparse
import logging
import pandas as pd
from typing import List, Dict

from sentence_transformers import SentenceTransformer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def embed(texts: List[str]) -> Dict:
    embedding = []

    try:
        embedding = model.encode(texts, batch_size=len(texts), device='cuda').tolist()
    except Exception as err:
        logger.error(f'Failed to get sentence-transformers embeddings: {err}')
        return embedding

    return embedding


def process_file(model_name: str, filepath: str, chunk_size: int = 100):
    df = pd.read_parquet(filepath)

    new_rows = []

    texts_chunk = []
    for idx, row in df.iterrows():
        texts_chunk.append(row['text'])

        if (idx + 1) % chunk_size == 0:
            result = embed(texts_chunk)
            for text, embedding in zip(texts_chunk, result):
                new_row = {
                    'text': text,
                    'embedding': embedding,
                    'metadata': {'model': model_name}
                }
            new_rows.append(new_row)
            texts_chunk = []

    if texts_chunk:
        result = embed(texts_chunk)
        for text, embedding in zip(texts_chunk, result):
            new_row = {
                'text': text,
                'embedding': embedding,
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
        '-d', '--dir',
        help='Directory containing parquet files to process',
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

    if not os.path.isdir(args.dir):
        logger.error(f"Directory {args.dir} does not exist")
        sys.exit(1)

    directory = args.dir

    try:
        model = SentenceTransformer(model_name)
    except Exception as err:
        logger.error(f'Failed to load SentenceTransformer model "{model_name}": {err}')
        sys.exit(1)

    for filename in os.listdir(directory):
        if filename.endswith(".parquet"):
            filepath = os.path.join(directory, filename)
            logging.info(f"Processing {filepath} ...")
            process_file(model_name=model_name, filepath=filepath)
