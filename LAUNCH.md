# FlowProof, launch and evidence playbook

Goal: turn FlowProof from "built" into distributed, used, and recognized, so it becomes usable evidence for a UK Global Talent (Digital Technology) application and for bioinformatics engineering roles.

Honest framing: on its own, a brand-new repo is weak evidence. Its value comes from external validation, adoption, registry presence, and contribution to the field's own emerging standard (MCPmed). This playbook is ordered by leverage.

## Phase 1, publish (do first)

### 1a. PyPI

The package is built and validated (`dist/flowproof_mcp-0.1.0-*.whl`, twine check passed). To publish:

1. Create a PyPI account at https://pypi.org (if none).
2. Account settings, API tokens, add a token scoped to the whole account for the first upload.
3. From `products/flowproof`, run (token stays on your machine):

   ```
   uvx twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN
   ```

After this, anyone can `uvx flowproof-mcp` or `pip install flowproof-mcp`. Record the release date; it is a citable milestone.

### 1b. GitHub (public repo)

FlowProof currently lives in the private monorepo. For discovery and evidence it needs a public repo (github.com/ajibadedapo/flowproof-mcp or a dedicated org). Push the `products/flowproof` subtree there with the README, LICENSE, tests, and CI badge. External stars, forks, and issues are direct evidence artifacts.

## Phase 2, register (discovery)

Submit to the MCP directories (each a PR or form):

- Official MCP registry: https://github.com/modelcontextprotocol/registry
- mcp.so, Glama (glama.ai/mcp), Smithery (smithery.ai), PulseMCP
- `awesome-mcp-servers` GitHub lists (open a PR adding FlowProof under a bioinformatics/science section)

Suggested one-line registry description:

> FlowProof, run reproducible bioinformatics pipelines (Nextflow) from an AI assistant, with verifiable Workflow Run RO-Crate provenance.

## Phase 3, contribute to the field (highest GTV signal)

MCPmed is a 2026 Briefings in Bioinformatics (Oxford) call for MCP-enabled bioinformatics services. FlowProof is a direct, concrete answer to that call.

- Read the paper and repo, engage in their GitHub discussion, and add FlowProof as a community implementation (execution + provenance layer), citing the paper.
- If appropriate, propose a short technical note or preprint positioning FlowProof against the MCPmed vision. A citation or listing in an academic-adjacent effort is strong Global Talent evidence.

## Phase 4, tell the story (reach)

- Launch post on the engineering blog (engineering.hammedajibade.com / Stack Dispatch), then cross-post to dev.to and a "Show HN".
- nf-core / Nextflow community Slack, share as a community tool.
- A 90-second demo: an AI assistant runs a pipeline and shows the verifiable provenance.

Draft Show HN title:

> Show HN: FlowProof, run reproducible bioinformatics pipelines from your AI assistant (MCP + provenance)

Draft opening line:

> AI can already look up biological data and plan analyses, but it cannot reliably run a pipeline and prove the result. FlowProof is an open MCP server that runs Nextflow pipelines and returns Workflow Run RO-Crate provenance (container digests, tool versions, input/output checksums), so an AI-produced result is reproducible byte-for-byte.

## GTV evidence map

Global Talent (Digital Technology) weighs a mandatory criterion (you are, or will be, a leader) plus optional criteria. FlowProof supports:

- Innovation: a novel product at the AI (MCP) x bioinformatics frontier, answering an explicit academic call (MCPmed).
- Technical contribution beyond day-job: an open-source tool adopted/listed in the ecosystem (registries, stars, downloads).
- Recognition: any citation, registry listing, community adoption, or press.

Evidence to collect as it accrues: PyPI download stats, GitHub stars/forks/issues, registry listings, the MCPmed engagement, blog/HN traction, and any third-party mention. FlowProof is a supporting piece; the spine of the case is Ubriot (revenue, the Arkifi partnership, apps live in both stores) plus the track record of shipping multiple production products.

## Status

Live: https://flowproof.specvista.com (MCP API), https://app.flowproof.specvista.com (dashboard). Package built and validated as flowproof-mcp. Remaining: run the PyPI upload, create the public repo, then Phases 2 to 4.
