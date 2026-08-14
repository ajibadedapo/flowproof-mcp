from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

mcp = pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TESTDATA = Path(__file__).resolve().parents[1] / "testdata" / "ont_sample.fastq"
SRC = Path(__file__).resolve().parents[1] / "src"


def _server_params(runs_dir: Path) -> StdioServerParameters:
    env = dict(os.environ)
    env["FLOWPROOF_RUNS_DIR"] = str(runs_dir)
    env["PYTHONPATH"] = str(SRC)
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "flowproof.server"],
        env=env,
    )


async def _drive(runs_dir: Path) -> dict:
    async with stdio_client(_server_params(runs_dir)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}

            listed = await session.call_tool("list_pipelines", {})
            described = await session.call_tool(
                "describe_pipeline", {"pipeline_id": "ont-read-stats"}
            )
            run = await session.call_tool(
                "run_pipeline",
                {"pipeline_id": "ont-read-stats", "inputs": {"reads": str(TESTDATA)}},
            )
            run_payload = json.loads(run.content[0].text)
            run_id = run_payload["run_id"]
            prov = await session.call_tool("get_provenance", {"run_id": run_id})
            return {
                "tool_names": tool_names,
                "listed": "".join(getattr(c, "text", "") for c in listed.content),
                "described": described.content[0].text,
                "run_status": run_payload["status"],
                "provenance": prov.content[0].text,
            }


def test_mcp_server_exposes_and_runs_tools(tmp_path: Path):
    import anyio

    result = anyio.run(_drive, tmp_path)
    assert {
        "list_pipelines",
        "describe_pipeline",
        "run_pipeline",
        "get_run_status",
        "get_results",
        "get_provenance",
    } <= result["tool_names"]
    assert "ont-read-stats" in result["listed"]
    assert "genome_size" in result["described"]
    assert result["run_status"] == "succeeded"
    prov = json.loads(result["provenance"])["provenance"]
    ids = {node["@id"] for node in prov["@graph"]}
    assert "ont-read-stats" in ids
