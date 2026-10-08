"""Transport wrappers must return named missing evidence, not nullable-schema errors."""
import asyncio
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters


def test_stdio_missing_optional_scientific_evidence_is_a_structured_blocker():
    async def exercise():
        root = Path(__file__).resolve().parents[1]
        params = StdioServerParameters(command=sys.executable, args=["-B", "-m", "igem_drylab.mcp.server"], cwd=root,
                                      env={"PYTHONPATH": str(root / "src")})
        async with Client(params, read_timeout_seconds=30) as client:
            response = await client.call_tool("igem.m1.validate_construct_sequence", dict(construct_id="missing-motifs",
                ordered_part_ids=["part"], part_sequences={"part": "MAA"}, coding_dna="ATGGCTGCTTAA"))
            assert not response.is_error
            result = response.structured_content["result"]
            assert result["status"] == "blocked"
            assert result["missing_inputs"] == ["wetlab_forbidden_restriction_site_list"]
            screen = await client.call_tool("igem.m1.screen_sequence", dict(sequence="GGGSSGGGSSGGGSS", sequence_kind="enzyme_ligand_linker"))
            assert not screen.is_error
            assert screen.structured_content["result"]["verdict"] == "blocked"
    asyncio.run(exercise())
