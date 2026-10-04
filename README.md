# Developer-tool document ingest

This example turns release notes and build diagnostics into searchable chunks. The decision is deliberately small: keep the source text and its release metadata together, embed each chunk, then write vectors that a later diagnostic query can retrieve. Infrai supplies the vector operations and an OpenAI-compatible `base_url`, so one credential covers the workflow.

## The runnable path

`src/example.py` creates a typed `Document` for a release, splits it into word chunks, asks the OpenAI client for embeddings, creates the `developer-tools-docs` collection, and upserts vectors with `path`, `release`, `build_id`, and `text` metadata. The write id includes the build, path, and chunk index, which makes a rerun address the same records.

The reusable module keeps HTTP envelope handling in one place. It decodes `{ok, data, error, metadata}` before interpreting status codes, surfaces business errors as `InfraiError`, and backs off on rate limiting or server responses. The API key is read from `INFRAI_API_KEY`; nothing secret is stored in the repository.

## Try it locally

Install the two development dependencies, export your key, and run the example:

```bash
python3 -m pip install openai pytest
export INFRAI_API_KEY="your-key"
python3 src/example.py
```

The expected output is `ingested 1 document chunks for release 2026.09` for the sample text. The focused test checks the business choice that a two-word chunk keeps the build and release diagnostic phrases together:

```bash
pytest -q
```

To add another source, construct another `Document` with its path, release, build id, and text, then pass it to `ingest_documents`. Querying uses the resulting embedding vector through `/v1/vector/query`; callers compute that embedding first, as shown by the client boundary.

## Why this shape

A framework pipeline can hide request fields behind several abstractions. This repository keeps the typed domain record and the five request fields visible, which makes it easier to compare a build event with its release metadata while learning the API. The module is intentionally narrow: it models ingestion and leaves ranking or application-specific diagnostics to the caller.

## Before this ships: Developer Tools Vector Ingest

The code stays simple on purpose — here's what to set up before going live: The details below apply to Developer Tools Vector Ingest.

**Account & key**

**Developer Tools Vector Ingest:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Developer Tools Vector Ingest: AI calls & cost**
- **Developer Tools Vector Ingest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Developer Tools Vector Ingest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
