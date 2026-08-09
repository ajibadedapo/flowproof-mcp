from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .runner import MockBackend, NextflowBackend
from .service import RunManager

BASE_DIR = Path(os.environ.get("FLOWPROOF_RUNS_DIR", Path.home() / ".flowproof" / "runs"))
_BACKEND = os.environ.get("FLOWPROOF_BACKEND", "mock").lower()

app = FastMCP("flowproof")
manager = RunManager(
    BASE_DIR,
    backend=NextflowBackend() if _BACKEND == "nextflow" else MockBackend(),
)


@app.tool()
def list_pipelines() -> list[dict]:
    return [
        {"id": m.id, "description": m.description, "read_type": m.read_type.value}
        for m in manager.registry.list()
    ]


@app.tool()
def describe_pipeline(pipeline_id: str) -> dict:
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


@app.tool()
def run_pipeline(
    pipeline_id: str,
    inputs: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> dict:
    record = manager.start_run(pipeline_id, inputs, params)
    return {"run_id": record.run_id, "status": record.status.value}


@app.tool()
def get_run_status(run_id: str) -> dict:
    record = manager.get(run_id)
    return {"run_id": run_id, "status": record.status.value}


@app.tool()
def get_results(run_id: str) -> dict:
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


@app.tool()
def get_provenance(run_id: str) -> dict:
    record = manager.get(run_id)
    if not record.provenance_path:
        return {"run_id": run_id, "provenance": None}
    return {
        "run_id": run_id,
        "provenance": json.loads(Path(record.provenance_path).read_text()),
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
