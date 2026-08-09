# FlowProof, ready-to-post submission content

Everything below is drafted and ready. The parts that must be posted as you (registry PRs, forum posts, MCPmed) are identity-bound; paste and submit under your own account. Public repo: https://github.com/ajibadedapo/flowproof-mcp

---

## A. One-liners (reuse everywhere)

- Short: Run reproducible bioinformatics pipelines from an AI assistant over MCP, with verifiable provenance.
- Medium: FlowProof is an open MCP server that runs Nextflow bioinformatics pipelines and returns Workflow Run RO-Crate provenance (container digests, tool versions, input/output checksums), so an AI-produced result is reproducible byte-for-byte.

## B. awesome-mcp-servers PR (github.com/punkpeye/awesome-mcp-servers and similar)

Add under a Science / Bioinformatics heading:

```
- [ajibadedapo/flowproof-mcp](https://github.com/ajibadedapo/flowproof-mcp) - Run reproducible bioinformatics pipelines (Nextflow) from an AI assistant, with verifiable Workflow Run RO-Crate provenance.
```

PR title: `Add FlowProof (reproducible bioinformatics pipelines over MCP)`
PR body: `FlowProof is an open MCP server that runs Nextflow pipelines and returns verifiable provenance. Adds a bioinformatics/science entry. PyPI: flowproof-mcp.`

## C. Official MCP registry (github.com/modelcontextprotocol/registry)

Follow their server.json schema. Key fields:

- name: `io.github.ajibadedapo/flowproof-mcp`
- description: use the medium one-liner
- repository: https://github.com/ajibadedapo/flowproof-mcp
- package: PyPI `flowproof-mcp`, run command `uvx flowproof-mcp`

## D. mcp.so / Glama / Smithery / PulseMCP

Each is a form or auto-index of the GitHub repo. Submit the repo URL + the medium one-liner + tags: mcp, bioinformatics, genomics, nextflow, provenance.

## E. Show HN (news.ycombinator.com/submit)

Title:
```
Show HN: FlowProof – run reproducible bioinformatics pipelines from your AI assistant
```
URL: https://github.com/ajibadedapo/flowproof-mcp

First comment (post immediately after):
```
Hi HN. FlowProof is an open MCP server that lets an AI assistant run a bioinformatics pipeline and hand back results whose provenance can be independently verified.

The MCP-for-bio ecosystem today has data access (BioMCP wraps 40+ databases) and analysis-planning agents (Biomni, AutoBA). What was missing was reliable *execution* you can trust: an AI that runs a pipeline and proves the result. FlowProof runs Nextflow pipelines and emits a Workflow Run RO-Crate (container digests, tool versions, SHA-256 of every input/output), so the run is reproducible byte-for-byte.

It runs locally (uvx flowproof-mcp, your data stays on your machine) or as a hosted endpoint. Seeded with a short-read variant-calling and an Oxford Nanopore long-read assembly pipeline; new pipelines register by manifest.

It's early and I'd genuinely value feedback from people running Nextflow/Snakemake day to day: is verifiable provenance at the AI boundary useful to you, and what pipeline would you want wired first?
```

## F. nf-core / Nextflow Slack (#tools or #general)

```
Sharing a small open-source tool I built: FlowProof, an MCP server that lets an AI assistant run Nextflow pipelines and returns Workflow Run RO-Crate provenance for each run. Idea is to make AI-driven pipeline execution reproducible and verifiable rather than a black box. Local (uvx flowproof-mcp) or hosted. Repo: https://github.com/ajibadedapo/flowproof-mcp . Feedback very welcome, especially on the provenance model and which pipelines to support next.
```

## G. MCPmed engagement (post as yourself, authentically)

MCPmed (Briefings in Bioinformatics, 2026) is a call for MCP-enabled bioinformatics services. Find their GitHub/discussion and post something like:

```
MCPmed framed the need for MCP-enabled bioinformatics services really well. I built FlowProof to explore the execution+provenance side of that vision: an MCP server that runs Nextflow pipelines and returns Workflow Run RO-Crate provenance so AI-driven runs are reproducible and verifiable. Sharing as a community implementation in case it's useful to the effort: https://github.com/ajibadedapo/flowproof-mcp . Would value your thoughts on aligning the provenance/metadata model with what MCPmed envisions.
```

Do NOT overstate a relationship. This is an honest "I built a thing in the spirit of your call", not a claim of collaboration.

## H. Blog post (Stack Dispatch / engineering.hammedajibade.com)

Working title: "Running reproducible bioinformatics pipelines from your AI assistant"
Outline:
1. The gap: AI can look up data and plan analyses, but can't run a pipeline and prove the result.
2. Why provenance is the hard part (reproducibility, container digests, checksums, RO-Crate standard).
3. How FlowProof works (MCP tool surface, registry, Nextflow backend, provenance emitter).
4. Local vs hosted; the security model (per-user keys, argument-injection hardening).
5. What's next and a call for pipeline requests.
