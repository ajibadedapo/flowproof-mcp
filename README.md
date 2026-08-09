# FlowProof

[![PyPI](https://img.shields.io/pypi/v/flowproof-mcp.svg)](https://pypi.org/project/flowproof-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/flowproof-mcp.svg)](https://pypi.org/project/flowproof-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

Reproducible bioinformatics pipeline execution over the Model Context Protocol (MCP), with verifiable provenance.

FlowProof lets an AI assistant run a bioinformatics pipeline and hand back results whose provenance can be independently verified: pipeline version, container digests, tool versions, parameters, and SHA-256 checksums of every input and output, emitted as a Workflow Run RO-Crate.

It fills the layer the MCP-for-bioinformatics ecosystem is missing. Data access already has MCP servers (BioMCP); analysis planning already has AI agents (Biomni, AutoBA). The gap is reliable, trustworthy execution, which needs orchestration and provenance discipline. That is what FlowProof provides.

## Why it exists

An AI that "runs an analysis for you" is only useful if you can trust the result. FlowProof makes every run reproducible and independently checkable, so an AI-driven result is not a black box: it ships with the exact recipe and checksums to reproduce it byte-for-byte.

## Status

v1 scaffold. The core (pipeline registry, execution backends, provenance) is complete and tested. The MCP server exposes six tools. A mock backend runs without Nextflow for development and CI; the Nextflow backend runs real pipelines.

## Install

```
uv sync
```

## Using FlowProof

FlowProof works two ways. Both let an AI assistant run pipelines for you; you never touch a terminal after setup.

### Local (recommended for real data)

Runs on your own machine, so your data never leaves it and your compute runs the pipelines. No token needed.

Add this to your MCP client config (Claude Desktop: `claude_desktop_config.json`; Cursor: MCP settings):

```json
{
  "mcpServers": {
    "flowproof": {
      "command": "uvx",
      "args": ["flowproof-mcp"]
    }
  }
}
```

Then just ask your assistant: "list the FlowProof pipelines" or "run the ONT assembly on this file". Runs are written under `~/.flowproof/runs` (override with `FLOWPROOF_RUNS_DIR`).

### Cloud (instant, no install)

Connect your client to the hosted server. Nothing to install; the cloud runs it. Uses a bearer token today (per-user keys and OAuth are on the roadmap):

```json
{
  "mcpServers": {
    "flowproof": {
      "url": "https://flowproof.specvista.com/mcp/",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

## Run the server directly

```
flowproof                        # stdio (local, default)
FLOWPROOF_TRANSPORT=http flowproof   # HTTP server on :8000
```

## Tools

| Tool | Purpose |
|------|---------|
| `list_pipelines` | Registered pipelines with id, description, read type |
| `describe_pipeline` | Inputs, parameters, outputs for a pipeline |
| `run_pipeline` | Execute a pipeline reproducibly, returns a run id |
| `get_run_status` | Status of a run |
| `get_results` | Output file manifest with checksums |
| `get_provenance` | The verifiable Workflow Run RO-Crate record |

## Pipelines (seed)

| id | Read type | Analysis |
|----|-----------|----------|
| `variant-call-short` | short | Short-read QC to germline variant calling |
| `assembly-ont` | long | Oxford Nanopore long-read de novo assembly |

New pipelines register by manifest; the server does not change.

## Backends

- `MockBackend`: deterministic, dependency-free. Used for development and tests.
- `NextflowBackend`: runs `nextflow run` with a container profile. Requires Nextflow and Docker.

## Provenance

Every run emits `ro-crate-metadata.json` following the Workflow Run RO-Crate profile, capturing the workflow and version, container images, resolved tool versions, exact parameters, and SHA-256 checksums of all inputs and outputs.

## Develop

```
PYTHONPATH=src uv run --with pytest --no-project python -m pytest tests/ -q
```

## Architecture

See [DESIGN.md](./DESIGN.md).
