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

    parameter_values = [
        {
            "@id": f"#param-{name}",
            "@type": "PropertyValue",
            "name": name,
            "value": value,
        }
        for name, value in sorted(record.params.items())
    ]

    run_action = {
        "@id": f"#run-{record.run_id}",
        "@type": "CreateAction",
        "name": f"FlowProof run of {manifest.id}",
        "instrument": {"@id": manifest.id},
        "object": [{"@id": e["@id"]} for e in input_entities]
        + [{"@id": p["@id"]} for p in parameter_values],
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
        *parameter_values,
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


def verify_crate(crate: dict) -> dict:
    graph = crate.get("@graph", [])
    if not isinstance(graph, list):
        return {
            "valid": False,
            "missing": ["@graph"],
            "outputs": 0,
            "linkedOutputs": 0,
            "datasetLinkedOutputs": 0,
        }

    run_actions = [
        node for node in graph
        if node.get("@type") == "CreateAction" and str(node.get("@id", "")).startswith("#run-")
    ]
    terminal_statuses = {
        "http://schema.org/CompletedActionStatus",
        "http://schema.org/FailedActionStatus",
    }
    run_statuses = [
        action.get("actionStatus")
        for action in run_actions
        if action.get("actionStatus") in terminal_statuses
    ]
    run_instrument_ids = {
        action.get("instrument", {}).get("@id")
        for action in run_actions
        if isinstance(action.get("instrument"), dict) and action.get("instrument", {}).get("@id")
    }
    output_ids = {
        item.get("@id")
        for action in run_actions
        for item in action.get("result", [])
        if isinstance(item, dict) and item.get("@id")
    }
    dataset_part_ids = {
        item.get("@id")
        for node in graph
        if node.get("@id") == "./" and node.get("@type") == "Dataset"
        for item in node.get("hasPart", [])
        if isinstance(item, dict) and item.get("@id")
    }
    outputs = [
        node for node in graph
        if node.get("@type") == "File" and node.get("sha256") and node.get("contentSize") is not None
    ]
    linked_outputs = [node for node in outputs if node.get("@id") in output_ids]
    dataset_linked_outputs = [
        node for node in linked_outputs if node.get("@id") in dataset_part_ids
    ]
    linked_output_ids = [node.get("@id") for node in linked_outputs]
    duplicate_linked_output_ids = {
        output_id
        for output_id in linked_output_ids
        if output_id and linked_output_ids.count(output_id) > 1
    }
    workflow = [
        node for node in graph
        if isinstance(node.get("@type"), list) and "ComputationalWorkflow" in node.get("@type", [])
    ]
    workflow_ids = {node.get("@id") for node in workflow if node.get("@id")}
    missing = []
    if not run_actions:
        missing.append("run action")
    if run_actions and len(run_statuses) != len(run_actions):
        missing.append("run status")
    if not outputs:
        missing.append("hashed outputs")
    if outputs and not linked_outputs:
        missing.append("run-linked hashed outputs")
    if duplicate_linked_output_ids:
        missing.append("unique run outputs")
    if linked_outputs and len(dataset_linked_outputs) != len(linked_outputs):
        missing.append("dataset-linked run outputs")
    if not workflow:
        missing.append("workflow")
    if workflow and run_actions and not (workflow_ids & run_instrument_ids):
        missing.append("run-linked workflow")
    return {
        "valid": not missing,
        "missing": missing,
        "outputs": len(outputs),
        "linkedOutputs": len(linked_outputs),
        "datasetLinkedOutputs": len(dataset_linked_outputs),
        "runStatusPresent": len(run_statuses) == len(run_actions) if run_actions else False,
        "workflowLinked": bool(workflow_ids & run_instrument_ids) if workflow and run_actions else False,
    }


def verify_provenance_path(path: Path) -> dict:
    return verify_crate(json.loads(path.read_text()))
