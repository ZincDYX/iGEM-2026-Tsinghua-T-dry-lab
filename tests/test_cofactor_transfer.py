"""Synthetic transform/transport oracles, not a project holo validation."""
import asyncio
import sys
from pathlib import Path

import numpy as np
import pytest

from igem_drylab.pocket_preparation import CofactorTransferInput, transfer_cofactor


def fixture(tmp_path):
    template=tmp_path/'template.pdb';target=tmp_path/'target.pdb'
    positions=[(0,0,0),(3,0,0),(0,4,0),(0,0,5)]
    def atom(i,xyz,hetero=False):
        x,y,z=xyz
        return (f"{'HETATM' if hetero else 'ATOM  '}{i:5d} {'C8M' if hetero else 'CA':>4} "
            f"{'FAD' if hetero else 'ALA'} A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C\n")
    template.write_text(''.join(atom(i,p) for i,p in enumerate(positions,1))+atom(5,(1,1,1),True))
    target.write_text(''.join(atom(i,(p[0]+10,p[1]-5,p[2]+2)) for i,p in enumerate(positions,1)))
    return CofactorTransferInput(template=dict(path=template,source_kind='experimental',source_reference='synthetic-not-experimental'),
        target=dict(path=target,source_kind='experimental',source_reference='synthetic-not-experimental'),
        cofactor=dict(chain='A',residues=[5]),template_to_target=dict(reference_chain='A',mobile_chain='A',
            residue_pairs=[(i,i) for i in range(1,5)],reviewed_reference='synthetic fixed transform oracle'),
        contact_pairs=[(('A','1','CA'),('A','5','C8M'))])


@pytest.mark.scientific_algorithm
def test_exact_cofactor_transform_and_contacts_are_not_a_bond_or_parameterization(tmp_path):
    result=transfer_cofactor(fixture(tmp_path))
    np.testing.assert_allclose(result['coordinates'][0]['xyz_angstrom'],[11,-4,3],atol=1e-12)
    assert result['candidate_contact_distances'][0]['distance_angstrom']==pytest.approx(np.sqrt(3))
    assert result['transform']['mapped_CA_rmsd_angstrom']<1e-12
    assert not result['chemical_topology_ready'] and not result['production_ready']


@pytest.mark.data_contract
def test_missing_contact_and_nonobserved_template_are_not_silently_accepted(tmp_path):
    request=fixture(tmp_path);request.contact_pairs=[(('A','99','CA'),('A','5','C8M'))]
    with pytest.raises(ValueError,match='contact_atom_missing'):transfer_cofactor(request)
    request=fixture(tmp_path);request.cofactor.residues=[1]
    with pytest.raises(ValueError,match='must_not_include_template_protein'):transfer_cofactor(request)


@pytest.mark.data_contract
def test_cofactor_transfer_real_stdio_contract(tmp_path):
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    request=fixture(tmp_path);root=Path(__file__).resolve().parents[1]
    async def exercise():
        async with Client(StdioServerParameters(command=sys.executable,args=['-B','-m','igem_drylab.mcp.server'],
                cwd=root,env={'PYTHONPATH':str(root/'src')}),read_timeout_seconds=30) as client:
            result=await client.call_tool('igem.m2.transfer_cofactor',{'payload':request.model_dump(mode='json')})
            assert not result.is_error
            assert result.structured_content['result']==transfer_cofactor(request)
    asyncio.run(exercise())
