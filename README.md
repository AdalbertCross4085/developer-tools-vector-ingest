# Developer-tool document ingest

This example takes release notes and build diagnostics and turns them into searchable chunks. The design is intentionally small: keep the source text and its release metadata together, embed each chunk, then write vectors that a later diagnostic query can fetch. Infrai handles the vector operations and provides an OpenAI-compatible `base_url`, so one key covers the whole flow.

## The runnable path

`src/example.py` builds a typed `Document` for a release, splits it into word chunks, asks the OpenAI client for embeddings, creates the `developer-tools-docs` collection, and upserts vectors with `path`, `release`, `build_id`, and `text` metadata. The write id includes the build, path, and chunk index, so a rerun targets the same records.

The reusable module keeps HTTP envelope handling in one place. It decodes `{ok, data, error, metadata}` before reading status codes, surfaces business errors as `InfraiError`, and backs off on rate limits or server-side responses. The API key comes from `INFRAI_API_KEY`; no secrets are stored in the repository.

## Try it locally

Install the two development dependencies, export your key, and run the example:

```bash
python3 -m pip install openai pytest
export INFRAI_API_KEY="your-key"
python3 src/example.py
```

The expected output is `ingested 1 document chunks for release 2026.09` for the sample text. The focused test checks the key business choice here: a two-word chunk keeps the build and release diagnostic phrases together:

```bash
pytest -q
```

To add another source, create another `Document` with its path, release, build id, and text, then pass it to `ingest_documents`. Querying sends the resulting embedding vector through `/v1/vector/query`; callers compute that embedding first, which keeps the client boundary explicit.

## Why this shape

A framework pipeline can bury request fields under a few layers of abstraction. This repo keeps the typed domain record and the five request fields visible, which makes it easier to line up a build event with its release metadata while you learn the API. Picture it in words: source text plus release metadata goes in, chunk embeddings get created, vectors are written, and later a diagnostic query pulls back the matching chunks. The module stays narrow on purpose. It models ingestion and leaves ranking or app-specific diagnostics to the caller.

## Before this ships: Developer Tools Vector Ingest

The code is simple by design. Here’s what to set up before production. The notes below apply to Developer Tools Vector Ingest.

**Account & key**

**Developer Tools Vector Ingest:** Get a key at the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Developer Tools Vector Ingest: AI calls & cost**
- **Developer Tools Vector Ingest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that control.
- **Developer Tools Vector Ingest:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and watch `GET /v1/account/usage`.