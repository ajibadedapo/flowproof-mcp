# FlowProof: reproducible bioinformatics pipeline execution over the Model Context Protocol with verifiable provenance

**Hammed Adedapo Ajibade**
Independent researcher
Correspondence: ajibadehammed@gmail.com · ORCID: 0000-0003-3120-4439

---

## Abstract

Large language model (LLM) assistants are increasingly able to reach scientific resources through the Model Context Protocol (MCP), and a recent community call has argued for MCP-enabled bioinformatics web services for LLM-driven discovery. The emerging ecosystem covers data access (MCP servers over biomedical databases) and analysis planning (AI agents that propose multi-step analyses), but the layer that lets an assistant actually *run* a pipeline and return a result that can be independently trusted remains underserved. We present FlowProof, an open-source MCP server that executes bioinformatics pipelines and returns their results together with a standards-based provenance record. Each run emits a Workflow Run RO-Crate capturing the pipeline version, container image, tool versions, parameters, and SHA-256 checksums of every input and output, so an AI-orchestrated analysis ships with the exact recipe and fixity information required to reproduce it. FlowProof separates a runner-agnostic core from its execution backends (a dependency-free backend for development and continuous integration, and a Nextflow backend for real workflows), is registry-driven so pipelines are added by manifest, and is drivable by any MCP-capable assistant over local or hosted transports. FlowProof is available on the Python Package Index as `flowproof-mcp` under the MIT license.

## Introduction

Reproducibility and provenance are longstanding requirements of computational biology, and the community has invested heavily in tools that make workflows portable and repeatable, including workflow managers such as Nextflow and community pipeline collections such as nf-core. A newer development is the use of LLM assistants to plan and carry out analyses on a researcher's behalf. The Model Context Protocol has quickly become a common way for such assistants to interact with external tools and data, and MCPmed has recently called for MCP-enabled bioinformatics web services as a standardized semantic layer for LLM-driven discovery.

Two layers of this ecosystem already have entrants. For *data access*, MCP servers expose biomedical databases so that an assistant can discover and retrieve datasets. For *analysis planning*, agent frameworks propose and sequence multi-step analyses. The layer that has received the least attention is *execution with trust*: actually running a reproducible pipeline and returning a result whose provenance can be independently verified. This matters more, not less, when a non-deterministic model is orchestrating the work: an assistant that "runs an analysis" is scientifically useful only if the result is auditable rather than a black box.

FlowProof targets this gap. It gives an LLM a disciplined execution surface in which pipelines are versioned and registered, execution is delegated to an established workflow manager, and every run produces a standards-based provenance record instead of an ad hoc log.

## Implementation

**MCP server and tools.** FlowProof is implemented in Python and exposes an MCP server with six tools: list available pipelines, describe a pipeline's inputs and parameters, run a pipeline, query a run's status, fetch its results, and fetch its provenance. Any MCP-capable client can drive it; no functionality is tied to a single assistant or vendor.

**Runner-agnostic core.** Execution is defined by a backend interface. A dependency-free backend produces deterministic results without a workflow engine, which keeps development and continuous integration fast and hermetic. A Nextflow backend runs real pipelines. Because the two share the same interface and provenance path, the same code produces provenance whether a run is a lightweight demonstration or a full analysis.

**Registry-driven pipelines.** Pipelines are plugins registered by manifest (identifier, inputs, parameters, output patterns, command template, container). Short-read and long-read (Oxford Nanopore) pipelines coexist, and new pipelines are added without modifying the server. Command templates are populated through input validation to prevent argument injection from untrusted values.

**Provenance.** After a run completes, FlowProof writes a Workflow Run RO-Crate. The crate records the executed action, the workflow and its version, the tool versions (for example the exact Nextflow build), the container image, and File entities carrying the byte size and SHA-256 checksum of every input and output. Emitting provenance in a community standard makes it interoperable with existing workflow-provenance tooling rather than a bespoke format.

**Transports and deployment.** FlowProof runs locally over stdio, so data and compute stay on the researcher's machine and no credential is required, which is the recommended mode for real data. It also runs as a hosted HTTP service for zero-install use. To keep a convenience surface from being mistaken for a production result, the hosted deployment runs a lightweight demonstration pipeline for real and refuses heavier reference-data workflows with a message directing the user to run them locally.

## Example: an independently verifiable run

Running the bundled Oxford Nanopore pipeline with no arguments executes it on a built-in sample and returns a Workflow Run RO-Crate. The following entries are taken verbatim from a real run and record the action, the exact tool version, and SHA-256 checksums of the input and output:

```json
{ "@id": "#run", "@type": "CreateAction",
  "instrument": { "@id": "assembly-ont" },
  "object": [{ "@id": "ont_sample.fastq" }],
  "result": [{ "@id": "results/read_stats.txt" }],
  "actionStatus": "http://schema.org/CompletedActionStatus" }
{ "@id": "#tool-nextflow", "@type": "SoftwareApplication",
  "name": "nextflow", "version": "26.04.6" }
{ "@id": "ont_sample.fastq", "@type": "File", "name": "reads",
  "contentSize": 120020,
  "sha256": "285a12b2d6dee106c3f7f30bf31582f6c2cd9546796997236e563888de498702" }
{ "@id": "results/read_stats.txt", "@type": "File",
  "contentSize": 59,
  "sha256": "c70ab03d12b9611d218bfa686d1e6d1788f2585d9aaab337c22de73f9d23eee2" }
```

A third party can recompute the input checksum, rerun the pipeline, and confirm the output checksum, closing the loop between an AI-issued instruction and an auditable, reproducible result.

## Discussion

FlowProof is complementary to, rather than competing with, existing MCP-for-bioinformatics efforts: data-access servers help an assistant find data, planning agents help it decide what to do, and FlowProof runs the resulting analysis reproducibly and returns verifiable provenance. It is also complementary to the broader reproducible-workflow ecosystem: it does not reinvent workflow execution but delegates to Nextflow and records provenance in a community standard, so it interoperates with existing pipelines and provenance consumers.

The current limitations are deliberate. The hosted deployment runs only a lightweight pipeline for real; reference-data workflows are expected to run in the user's own environment, where the data and compute reside. Signature verification of manifests is stubbed and intended for future work. The provenance model captures the information needed to reproduce a run and verify fixity; richer capture (for example per-process resource usage) is a natural extension.

## Availability

FlowProof is open source under the MIT license. It is installable from the Python Package Index (`pip install flowproof-mcp`; `uvx flowproof-mcp`) and requires Python 3.10 or later. Source code, documentation, and the complete example provenance crate are available in the project repository. The pipeline registry, execution backends, and provenance emitter are covered by an automated test suite.

## References

1. Flotho M, Diks IF, Flotho P, Molano LAG, Hirsch P, Keller A. MCPmed: a call for Model Context Protocol-enabled bioinformatics web services for LLM-driven discovery. *Briefings in Bioinformatics*. 2026;27(1):bbag076.
2. Di Tommaso P, Chatzou M, Floden EW, Barja PP, Palumbo E, Notredame C. Nextflow enables reproducible computational workflows. *Nature Biotechnology*. 2017;35(4):316–319.
3. Ewels PA, Peltzer A, Fillinger S, Patel H, Alneberg J, Wilm A, Garcia MU, Di Tommaso P, Nahnsen S. The nf-core framework for community-curated bioinformatics pipelines. *Nature Biotechnology*. 2020;38(3):276–278.
4. Leo S, Crusoe MR, Rodríguez-Navas L, et al. Recording provenance of workflow runs with RO-Crate. *PLOS ONE*. 2024;19(9):e0309210.
5. Anthropic. Model Context Protocol. 2024. https://modelcontextprotocol.io
6. BioMCP: Model Context Protocol server for biomedical data access. 2025. https://github.com/genomoncology/biomcp
7. Huang K, et al. Biomni: A General-Purpose Biomedical AI Agent. *bioRxiv*. 2025.
8. Zhou J, Zhang B, Chen X, Li H, Xu X, Chen S, Gao X. An AI Agent for Fully Automated Multi-Omic Analyses. *Advanced Science*. 2024;11(44):2407094.
