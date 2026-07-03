"""
Text embeddings via fastembed (lightweight ONNX, no torch, no API key).

Model bge-small-en-v1.5 (384-dim). The model is lazy-loaded on first use and
downloaded once (~130MB), then cached in the container. Calls are wrapped in a
threadpool so they don't block the async event loop.
"""
from __future__ import annotations

from fastapi.concurrency import run_in_threadpool

MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return [vec.tolist() for vec in model.embed(texts)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return await run_in_threadpool(_embed_sync, texts)


async def embed_query(text: str) -> list[float]:
    result = await embed_texts([text])
    return result[0]
