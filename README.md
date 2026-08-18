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

FlowProof is working and installable today (`pip install flowproof-mcp`). The pipeline registry, execution backends, and RO-Crate provenance are complete and covered by tests, and the MCP server exposes six tools (list, describe, run, status, results, provenance). It ships with two execution backends: a zero-dependency backend for development and CI, and a Nextflow backend that runs real pipelines.

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
| `ont-read-stats` | long | Oxford Nanopore read statistics (QC); optional Flye assembly. Runs on a built-in sample if you provide no input. |
| `variant-call-short` | short | Short-read QC to germline variant calling (nf-core/sarek) |
| `rnaseq` | short | RNA-seq quantification: QC, trimming, alignment, gene counts (nf-core/rnaseq) |
| `fetchngs` | short | Fetch raw reads and metadata from public archives, SRA/ENA/GEO (nf-core/fetchngs) |
| `viralrecon` | short | Viral genome reconstruction and variant calling from amplicon data (nf-core/viralrecon) |

New pipelines register by manifest; the server does not change.

Try it instantly: ask your assistant to "run ont-read-stats" with no input, and FlowProof runs the bundled Oxford Nanopore sample end to end and returns a verifiable provenance crate, no data or reference genome required.

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

## Cite

If you use FlowProof in your research, please cite the archived software release:

> Ajibade, H. A. (2026). *FlowProof: reproducible bioinformatics pipeline execution over the Model Context Protocol with verifiable provenance* (v0.1.2). Zenodo. https://doi.org/10.5281/zenodo.21932977

A machine-readable [`CITATION.cff`](./CITATION.cff) is included, so GitHub shows a "Cite this repository" button with BibTeX and APA formats.

```bibtex
@software{flowproof,
  author    = {Ajibade, Hammed Adedapo},
  title     = {FlowProof: reproducible bioinformatics pipeline execution over the Model Context Protocol with verifiable provenance},
  year      = {2026},
  version   = {0.1.2},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.21932977},
  url       = {https://github.com/ajibadedapo/flowproof-mcp}
}
```
