# FlowProof (provisional name)

Reproducible bioinformatics pipeline execution as an MCP server, so an AI assistant can run a pipeline and return results with verifiable provenance.

## The gap this fills

The MCP-for-bioinformatics ecosystem is emerging (MCPmed is a 2026 call for it) but splits into two layers that already have entrants:

- Data access via MCP: BioMCP wraps 40+ biomedical databases.
- Analysis planning via AI agents: Biomni, AutoBA, BIA.

The missing layer is reliable execution with trust: letting an AI agent actually run a reproducible pipeline and hand back results whose provenance can be independently verified. That layer needs orchestration, containerized reproducibility, and provenance discipline, not more database wrappers or planning agents.

FlowProof owns that layer.

## Principles

- Deterministic, verifiable results over convenience. Every run emits a provenance record (pipeline version, container digests, tool versions, parameters, input and output checksums).
- Standards, not homemade formats. Provenance is emitted as Workflow Run RO-Crate.
- Runner-agnostic core. The execution backend is an interface; a mock backend runs without Nextflow, a Nextflow backend runs real pipelines.
- Registry-driven. Pipelines are plugins registered by manifest, so short-read and long-read (Oxford Nanopore) pipelines coexist and new ones drop in without touching the server.
- Open. Any MCP-capable assistant can drive it; nothing is locked to one platform.

## Architecture

```
AI assistant (MCP client)
        |  MCP (stdio)
   server.py            tool surface
        |
   registry.py          pipeline manifests, lookup
        |
   runner.py            RunBackend interface -> MockBackend | NextflowBackend
        |
   provenance.py        Workflow Run RO-Crate emitter
```

### MCP tool surface (v1)

- `list_pipelines` -> registered pipelines with id, description, read type.
- `describe_pipeline(pipeline_id)` -> inputs, parameters, outputs.
- `run_pipeline(pipeline_id, inputs, params)` -> starts a run, returns run_id.
- `get_run_status(run_id)` -> queued | running | succeeded | failed.
- `get_results(run_id)` -> output file manifest with checksums.
- `get_provenance(run_id)` -> the verifiable RO-Crate record.

### Pipeline registry (v1 seed, broader from the start)

- `variant-call-short` short-read QC to variant calling on an nf-core test dataset.
- `assembly-ont` long-read de novo assembly for Oxford Nanopore reads.

Each pipeline is a manifest: id, description, read type, declared inputs and params, output contract, and the backend command template.

### Provenance model

Each run produces a `ro-crate-metadata.json` (Workflow Run RO-Crate profile) capturing: the workflow entity and version, the container images and digests used, resolved tool versions, the exact parameters, and SHA-256 checksums of every input and output. This is what makes an AI-produced result trustworthy: it can be re-run and verified byte-for-byte.

## v1 scope

- Python package, MCP server over stdio.
- Registry with the two seed pipelines above.
- MockBackend (deterministic fake run for development and CI) and NextflowBackend (shells out to `nextflow run` with Docker profile).
- RO-Crate provenance emitter.
- Local execution only. Cloud, streaming logs, and AI failure-diagnosis are explicitly deferred.

## How it maps to hiring (ONT, EIT, Oxford RSE)

Demonstrates Nextflow, containerized reproducibility, provenance standards (RO-Crate), and production Python, plus the MCP/AI frontier that almost no bioinformatician has touched. A long-read seed pipeline targets Oxford Nanopore directly.

## Deferred (post-v1)

Cloud and HPC execution, streaming run logs, additional pipelines, AI-assisted failure diagnosis, a hosted registry, and the final published name after an npm/PyPI/GitHub availability check.

## Security follow-ups (tracked)

- Dashboard session hardening: move the session token from localStorage (XSS-exfiltratable) to an HttpOnly, Secure, SameSite cookie set by the API, with the session read from the cookie and CORS credentials enabled. This must be implemented and tested against the live HTTPS subdomains (app.flowproof.specvista.com and flowproof.specvista.com), so it is sequenced after DNS/TLS are live to avoid shipping an untested cross-origin cookie flow that could break auth. Auth gate is already fail-closed (FLOWPROOF_ALLOW_ANONYMOUS must be explicitly set for open mode).
