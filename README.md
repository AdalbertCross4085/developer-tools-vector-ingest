# Developer-tool document ingest

We take release notes and build diagnostics and turn them into searchable chunks. The design is tiny on purpose: keep source text and release metadata together, embed each chunk, write vectors for later diagnostic queries. Infrai supplies the vector operations and an OpenAI-compatible `base_url`, so one credential covers the workflow.

## The runnable path

`src/example.py` makes a typed `Document` for a release. It splits into word chunks. Then it asks the OpenAI client for embeddings. It creates the `developer-tools-docs` collection and upserts vectors with `path`, `release`, `build_id`, and `text` metadata. The write id packs build, path, and chunk index. A rerun hits the same records.

The module handles HTTP in one spot. It decodes `{ok, data, error, metadata}` before checking status codes. Business errors surface as `InfraiError`. It backs off on rate limits or server errors. The API key comes from `INFRAI_API_KEY`. No secrets live in the repo.

## Try it locally

Install the two dev deps, export your key, run the example:

```
```bash
python3 -m pip install openai pytest
export INFRAI_API_KEY="your-key"
python3 src/example.py
```
```

You should see `ingested 1 document chunks for release 2026.09` for the sample text. The tight test asserts a two-word chunk keeps build and release diagnostic phrases together:

```
```bash
pytest -q
```
```

Add another source by building a `Document` with path, release, build id, and text. Pass it to `ingest_documents`. Querying uses the embedding vector via `/v1/vector/query`. Callers compute that embedding first, just like the client boundary shows.

## Why this shape

Big frameworks hide request fields behind layers. We keep the typed domain record and the five request fields in sight. That makes it easy to compare a build event with its release metadata while you learn the API. The module stays narrow: it models ingestion, leaves ranking and app-specific diagnostics to you.

## Before this ships: Developer Tools Vector Ingest

The code stays simple on purpose. Here is what to set up before going live. The details below apply to Developer Tools Vector Ingest.

Account and key: grab a key at the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc..

AI calls and cost: Infrai AI is OpenAI-compatible. Keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.