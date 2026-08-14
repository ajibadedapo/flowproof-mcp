from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .provenance import verify_crate
from .registry import registry
from .runner import MockBackend, NextflowBackend
from .service import RunManager

BASE_DIR = Path(os.environ.get("FLOWPROOF_RUNS_DIR", Path.home() / ".flowproof" / "runs"))
_BACKEND = os.environ.get("FLOWPROOF_BACKEND", "mock").lower()
_HOSTED = os.environ.get("FLOWPROOF_TRANSPORT", "").lower() == "http"

app = FastMCP("flowproof")
manager = RunManager(
    BASE_DIR,
    backend=NextflowBackend() if _BACKEND == "nextflow" else MockBackend(),
)


@app.tool(
    description=(
        "List the available bioinformatics pipelines. Returns each pipeline's id, "
        "a short description, and its read_type (short-read or long-read). Call this "
        "first to discover what can be run, then describe_pipeline for details."
    )
)
def list_pipelines() -> list[dict]:
    return [
        {"id": m.id, "description": m.description, "read_type": m.read_type.value}
        for m in manager.registry.list()
    ]


@app.tool(
    description=(
        "Return the full manifest for one pipeline: its required inputs, tunable "
        "parameters, container image, and output file patterns. Call this before "
        "run_pipeline to learn exactly which inputs and params it expects."
    )
)
def describe_pipeline(
    pipeline_id: Annotated[
        str, Field(description="The pipeline id, as returned by list_pipelines.")
    ],
) -> dict:
    m = manager.registry.get(pipeline_id)
    return {
        "id": m.id,
        "description": m.description,
        "read_type": m.read_type.value,
        "container": m.container,
        "inputs": [
            {"name": i.name, "description": i.description, "required": i.required}
            for i in m.inputs
        ],
        "params": [
            {"name": p.name, "description": p.description, "default": p.default}
            for p in m.params
        ],
        "outputs": list(m.output_globs),
    }


@app.tool(
    description=(
        "Start a pipeline run and return a run_id to track it. Provide inputs (a map "
        "of input name to file path or value) and params (a map of parameter name to "
        "value), as described by describe_pipeline. The run executes asynchronously; "
        "poll get_run_status, then fetch get_results and get_provenance when it completes."
    )
)
def run_pipeline(
    pipeline_id: Annotated[
        str, Field(description="The pipeline id to run, from list_pipelines.")
    ],
    inputs: Annotated[
        dict[str, str] | None,
        Field(description="Map of input name to file path or value, per describe_pipeline."),
    ] = None,
    params: Annotated[
        dict[str, str] | None,
        Field(description="Map of parameter name to value, per describe_pipeline."),
    ] = None,
) -> dict:
    if _HOSTED and not registry.get(pipeline_id).hosted_runnable:
        raise ValueError(
            f"'{pipeline_id}' needs local compute (large nf-core workflow plus reference data) "
            "and does not run on the hosted demo. Run it where your data lives: "
            "`uvx flowproof-mcp` (data stays on your machine, no token). "
            "The hosted service runs 'assembly-ont' for real."
        )
    record = manager.start_run(pipeline_id, inputs, params)
    return {"run_id": record.run_id, "status": record.status.value}


@app.tool(
    description=(
        "Get the current status of a run (queued, running, succeeded, or failed) by "
        "its run_id, as returned by run_pipeline."
    )
)
def get_run_status(
    run_id: Annotated[str, Field(description="The run id returned by run_pipeline.")],
) -> dict:
    record = manager.get(run_id)
    return {"run_id": run_id, "status": record.status.value}


@app.tool(
    description=(
        "Get the outputs of a run: each output file with its SHA-256 checksum and size "
        "in bytes, plus the run status. Use the checksums to verify results independently."
    )
)
def get_results(
    run_id: Annotated[str, Field(description="The run id returned by run_pipeline.")],
) -> dict:
    record = manager.get(run_id)
    result = record.result
    files = (
        [
            {"path": f.path, "sha256": f.sha256, "size_bytes": f.size_bytes}
            for f in result.output_files
        ]
        if result
        else []
    )
    return {"run_id": run_id, "status": record.status.value, "outputs": files}


@app.tool(
    description=(
        "Get the Workflow Run RO-Crate provenance for a run: workflow version, container "
        "digests, tool versions, parameters, and input/output SHA-256 checksums, the full "
        "record needed to reproduce the run byte-for-byte."
    )
)
def get_provenance(
    run_id: Annotated[str, Field(description="The run id returned by run_pipeline.")],
) -> dict:
    record = manager.get(run_id)
    if not record.provenance_path:
        return {"run_id": run_id, "provenance": None}
    provenance = json.loads(Path(record.provenance_path).read_text())
    return {
        "run_id": run_id,
        "provenance": provenance,
        "receipt": verify_crate(provenance),
    }


def main() -> None:
    transport = os.environ.get("FLOWPROOF_TRANSPORT", "stdio").lower()
    if transport in ("http", "streamable-http"):
        import uvicorn

        from .http_app import asgi

        uvicorn.run(
            asgi,
            host=os.environ.get("FLOWPROOF_HOST", "0.0.0.0"),
            port=int(os.environ.get("FLOWPROOF_PORT", "8000")),
        )
    else:
        app.run()


if __name__ == "__main__":
    main()
