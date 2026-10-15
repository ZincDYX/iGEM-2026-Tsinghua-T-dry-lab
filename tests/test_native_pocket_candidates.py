"""Native P2Rank format fixtures, not real pocket validation."""
from hashlib import sha256
import csv,json
import pytest
from igem_drylab.pocket_preparation import PocketPredictionInput,read_pocket_candidates


def fixture(tmp_path):
    structure=tmp_path/'synthetic.pdb'
    structure.write_text('ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 20.00           C\n'
                         'ATOM      2  CA  GLY A   2A      3.000   0.000   0.000  1.00 20.00           C\n')
    output=tmp_path/'synthetic.pdb_predictions.csv'
    output.write_text('name, rank, score, probability, center_x, center_y, center_z, residue_ids\n'
                      'pocket1, 1, 20.0, 0.9, 1.0, 2.0, 3.0, A_1 A_2A\n')
    record=tmp_path/'native-run.json'
    def bind():
        record.write_text(json.dumps(dict(tool_name='P2Rank',tool_version='synthetic-format-not-project-job',
            returncode=0,command=['synthetic-format-fixture'],profile='default',
            input_sha256=sha256(structure.read_bytes()).hexdigest(),output_sha256=sha256(output.read_bytes()).hexdigest())))
    bind()
    return PocketPredictionInput(structure=dict(path=structure,source_kind='experimental',source_reference='synthetic-not-experimental-data'),
        predictions_file=output,execution_record=record),bind


@pytest.mark.data_contract
def test_native_pocket_mapping_preserves_insertion_and_never_approves_holo(tmp_path):
    request,_=fixture(tmp_path);result=read_pocket_candidates(request)
    assert result['candidates'][0]['center_angstrom']==[1.,2.,3.]
    assert result['candidates'][0]['residues']==[dict(chain='A',residue='1'),dict(chain='A',residue='2A')]
    assert not result['production_ready'] and not result['chemical_topology_ready']
    assert not result['candidates'][0]['catalytic_pocket_confirmed']


@pytest.mark.data_contract
def test_wrong_model_raw_bytes_and_residues_are_rejected(tmp_path):
    request,bind=fixture(tmp_path)
    request.predictions_file.write_text(request.predictions_file.read_text().replace('A_2A','A_99'))
    with pytest.raises(ValueError,match='matching_native_execution'):read_pocket_candidates(request)
    bind()
    with pytest.raises(ValueError,match='residue_not_in_exact_input'):read_pocket_candidates(request)


@pytest.mark.data_contract
def test_real_stdio_pocket_parser_is_the_same_contract(tmp_path):
    import asyncio,sys
    from pathlib import Path
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    request,_=fixture(tmp_path);root=Path(__file__).resolve().parents[1]
    async def exercise():
        async with Client(StdioServerParameters(command=sys.executable,args=['-B','-m','igem_drylab.mcp.server'],
                cwd=root,env={'PYTHONPATH':str(root/'src')}),read_timeout_seconds=30) as client:
            response=await client.call_tool('igem.m2.read_pocket_candidates',{'payload':request.model_dump(mode='json')})
            assert not response.is_error
            assert response.structured_content['result']==read_pocket_candidates(request)
    asyncio.run(exercise())
