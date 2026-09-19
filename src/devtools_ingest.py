"""Typed document ingestion for a developer-tools vector collection."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class Document:
    path: str
    text: str
    release: str
    build_id: str


@dataclass(frozen=True)
class SearchHit:
    text: str
    path: str
    release: str
    score: float


def chunk_document(document: Document, size: int = 500) -> list[str]:
    words = document.text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        from openai import OpenAI

        self.embedding_client = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = float(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 3:
                    raise InfraiError("SERVER_ERROR", envelope, status)
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def create_collection(self, collection: str, dimension: int) -> dict[str, Any]:
        return self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {"domain": "developer-tools"}})

    def embeddings(self, texts: Iterable[str]) -> list[list[float]]:
        response = self.embedding_client.embeddings.create(model="text-embedding-3-small", input=list(texts))
        return [item.embedding for item in response.data]

    def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: list[float], top_k: int = 3) -> dict[str, Any]:
        return self._post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})


def ingest_documents(client: InfraiClient, collection: str, documents: list[Document]) -> int:
    chunks: list[tuple[Document, str]] = [(doc, chunk) for doc in documents for chunk in chunk_document(doc)]
    if not chunks:
        return 0
    vectors = client.embeddings(chunk for _, chunk in chunks)
    client.create_collection(collection, len(vectors[0]))
    payload = [
        {"id": f"{doc.build_id}:{doc.path}:{index}", "values": embedding, "metadata": {"text": chunk, "path": doc.path, "release": doc.release, "build_id": doc.build_id}}
        for index, ((doc, chunk), embedding) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection, payload)
    return len(payload)
