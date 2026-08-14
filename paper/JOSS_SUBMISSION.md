# JOSS submission checklist for FlowProof

The Journal of Open Source Software (JOSS) publishes short, peer-reviewed papers about open-source research software and issues a citable DOI. Review happens openly on GitHub. This file is your step-by-step guide.

## Before you submit: what JOSS requires (and FlowProof's status)

| Requirement | Status | Action needed |
|---|---|---|
| Open source, OSI-approved license | ✅ MIT | none |
| Public source repository | ✅ github.com/ajibadedapo/flowproof-mcp | ensure `paper/paper.md` + `paper/paper.bib` are pushed there |
| `paper.md` with title, authors, affiliations, summary, statement of need, references | ✅ drafted | confirm content |
| `paper.bib` with references | ✅ verified | all DOIs checked (MCPmed 10.1093/bib/bbag076; Biomni; AutoBA; Workflow Run RO-Crate; Nextflow; nf-core) |
| Author ORCID | ⛔ placeholder | **create an ORCID (free, orcid.org) and replace `0000-0000-0000-0000`** |
| Documentation (install, usage, API) | ✅ README | none |
| Automated tests | ✅ 34 tests | none |
| "Substantial scholarly effort" | ⚠️ judged by editor | the real RO-Crate provenance example + Nextflow execution + registry strengthen this; be ready to expand if asked |
| Statement of need aimed at a diverse audience | ✅ | none |

## The one-time to-dos (only you can do these)

1. **Get an ORCID** at https://orcid.org (2 minutes, free). Put it in `paper.md`.
2. **Fill in your email/affiliation** in `paper.md` (independent researcher is fine).
3. **Verify the citations** in `paper.bib`, replace or correct any DOI you can't confirm.
4. **Push `paper/paper.md`, `paper/paper.bib`, and `paper/example-provenance.json` to the public repo** (`github.com/ajibadedapo/flowproof-mcp`). JOSS reviews from there.
5. **Tag a release** of the software (e.g. `v0.1.0`) on GitHub so there's a citable version.

## How to submit (after the to-dos)

1. Go to https://joss.theoj.org and sign in with GitHub.
2. Click **Submit a paper**.
3. Provide:
   - **Repository URL**: `https://github.com/ajibadedapo/flowproof-mcp`
   - **Branch** (if the paper isn't on the default branch)
   - **Version**: `v0.1.1`
4. The Editorial Bot compiles `paper.md` into a PDF, check it renders correctly (fix `paper.md`/`paper.bib` and it recompiles).
5. An editor does a **pre-review scope check** (this is where the "substantial effort" judgement happens). If accepted into review, reviewers work through a checklist (installs cleanly, tests run, docs adequate, statement of need clear, functionality claims true).
6. You respond to reviewer issues on GitHub. On acceptance you archive a release (Zenodo) and JOSS mints the DOI.

## Honest expectation

- **Timeline**: pre-review + review typically takes several weeks to a couple of months.
- **Risk**: an editor may consider the package on the small side and ask you to expand scope or decline. The provenance/verification substance is your strongest argument; if pushed, expanding the pipeline set or the provenance model is the way to answer.
- **Fallback**: the bioRxiv preprint (`preprint.docx`) is your unblocked, immediately-citable credential regardless of the JOSS outcome, and a JOSS paper and a preprint are not mutually exclusive.
