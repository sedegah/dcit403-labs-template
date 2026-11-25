import hashlib
import math
import re
from typing import List

DIM = 512


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _embed_one(text):
    vector = [0.0] * DIM
    for token in _tokenize(text):
        index = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % DIM
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm > 0:
        vector = [value / norm for value in vector]
    return vector


class HashingEmbeddingFunction:
    def __call__(self, input: List[str]) -> List[List[float]]:
        return [_embed_one(text) for text in input]

    def embed_query(self, input):
        return self(input if isinstance(input, list) else [input])

    def embed_documents(self, input):
        return self(input)

    def name(self) -> str:
        return "hashing-512"

    def __repr__(self):
        return "HashingEmbeddingFunction(dim=512)"
