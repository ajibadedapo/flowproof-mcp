from __future__ import annotations

import json
from pathlib import Path

from .hashing import sha256_file
from .models import PipelineManifest, RunRecord, RunResult

PROFILE = "https://w3id.org/ro/wfrun/process/0.5"
RO_CRATE_SPEC = "https://w3id.org/ro/crate/1.1"


def build_crate(
    manifest: PipelineManifest,
    record: RunRecord,
    result: RunResult,
    run_dir: Path,
) -> dict:
    input_entities = []
    for name, value in sorted(record.inputs.items()):
        entity = {"@id": value, "@type": "File", "name": name}
        path = Path(value)
        if path.is_file():
            entity["contentSize"] = path.stat().st_size
            entity["sha256"] = sha256_file(path)
        input_entities.append(entity)

    output_entities = []
    for output in result.output_files:
        output_entities.append(
            {
                "@id": output.path,
                "@type": "File",
                "contentSize": output.size_bytes,
                "sha256": output.sha256,
            }
        )

    workflow_entity = {
        "@id": manifest.id,
        "@type": ["File", "SoftwareSourceCode", "ComputationalWorkflow"],
        "name": manifest.description,
        "version": "0.1.0",
        "softwareRequirements": [
            {"@id": manifest.container, "@type": "SoftwareApplication"}
        ],
    }

    run_action = {
        "@id": f"#run-{record.run_id}",
        "@type": "CreateAction",
        "name": f"FlowProof run of {manifest.id}",
        "instrument": {"@id": manifest.id},
        "object": [{"@id": e["@id"]} for e in input_entities],
        "result": [{"@id": e["@id"]} for e in output_entities],
        "actionStatus": (
            "http://schema.org/CompletedActionStatus"
            if result.status.value == "succeeded"
            else "http://schema.org/FailedActionStatus"
        ),
    }

    tools = [
        {"@id": f"#tool-{name}", "@type": "SoftwareApplication", "name": name, "version": version}
        for name, version in sorted(result.tool_versions.items())
    ]

    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": [{"@id": RO_CRATE_SPEC}, {"@id": PROFILE}],
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": f"FlowProof provenance for run {record.run_id}",
            "mainEntity": {"@id": manifest.id},
            "hasPart": [{"@id": e["@id"]} for e in input_entities + output_entities],
        },
        workflow_entity,
        run_action,
        {"@id": manifest.container, "@type": "SoftwareApplication", "name": manifest.container},
        *tools,
        *input_entities,
        *output_entities,
    ]

    return {"@context": RO_CRATE_SPEC + "/context", "@graph": graph}


def write_provenance(
    manifest: PipelineManifest,
    record: RunRecord,
    result: RunResult,
    run_dir: Path,
) -> Path:
    crate = build_crate(manifest, record, result, run_dir)
    path = run_dir / "ro-crate-metadata.json"
    path.write_text(json.dumps(crate, indent=2) + "\n")
    return path
