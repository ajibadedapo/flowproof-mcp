# bioRxiv submission metadata for FlowProof

Copy each field into the matching box in the bioRxiv submission form (submit.biorxiv.org). Upload `preprint.docx` as the manuscript. Placeholders in **[brackets]** are the only things you must fill in.

---

## Title
FlowProof: reproducible bioinformatics pipeline execution over the Model Context Protocol with verifiable provenance

## Manuscript type
New Results

## Subject area / Category
Bioinformatics

## Authors
- Hammed Adedapo Ajibade — Independent researcher — ORCID: 0000-0003-3120-4439 — corresponding author

## Corresponding author email
ajibadehammed@gmail.com

## Abstract
Large language model (LLM) assistants are increasingly able to reach scientific resources through the Model Context Protocol (MCP), and a recent community call has argued for MCP-enabled bioinformatics web services for LLM-driven discovery. The emerging ecosystem covers data access (MCP servers over biomedical databases) and analysis planning (AI agents that propose multi-step analyses), but the layer that lets an assistant actually run a pipeline and return a result that can be independently trusted remains underserved. We present FlowProof, an open-source MCP server that executes bioinformatics pipelines and returns their results together with a standards-based provenance record. Each run emits a Workflow Run RO-Crate capturing the pipeline version, container image, tool versions, parameters, and SHA-256 checksums of every input and output, so an AI-orchestrated analysis ships with the exact recipe and fixity information required to reproduce it. FlowProof separates a runner-agnostic core from its execution backends (a dependency-free backend for development and continuous integration, and a Nextflow backend for real workflows), is registry-driven so pipelines are added by manifest, and is drivable by any MCP-capable assistant over local or hosted transports. FlowProof is available on the Python Package Index as flowproof-mcp under the MIT license.

## Keywords
Model Context Protocol; reproducibility; provenance; workflows; Nextflow; RO-Crate; large language models; bioinformatics

## License
Recommended: **CC-BY 4.0** (allows reuse with attribution; standard for open tools).
Alternatives bioRxiv offers: CC-BY-NC-ND 4.0, CC-BY-ND 4.0, CC0, or "No reuse without permission". Pick CC-BY unless you have a reason not to.

## Competing Interest Statement
The author declares no competing interests.

## Funding Statement
This work received no specific funding.

## Author Contributions
H.A.A. conceived the software, designed and implemented it, and wrote the manuscript.

## Data and Code Availability Statement
FlowProof is open source under the MIT license. Source code and documentation: https://github.com/ajibadedapo/flowproof-mcp . Released package: https://pypi.org/project/flowproof-mcp/ . The example provenance crate referenced in the manuscript is included in the repository. No new biological data were generated; the bundled demonstration input is synthetic.

## Previously submitted / dual posting
Not previously published. (If you also submit to JOSS, that is compatible with a bioRxiv preprint; you may note the intended venue.)

---

### Honest notes before you click submit
- bioRxiv does **not** require an endorser (that's arXiv), but it does a light screen, and submissions from an **independent researcher with no institutional email** are occasionally queried. Use your best professional email. If it's held, a one-line reply explaining it's independent open-source research usually clears it.
- Make sure the **ORCID and email placeholders are filled** in both `preprint.docx` and this form, and that the manuscript's citations are verified.
