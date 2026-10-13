"""Native DSSP assignments in complete fusion context, auxiliary evidence only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from Bio.PDB.DSSP import make_dssp_dict
from pydantic import Field

from .design_analysis import ScientificAnalysisInput
from .region_assessment import Region
from .template_geometry import StructureInput


class DsspContextInput(ScientificAnalysisInput):
    model: StructureInput
    native_output: Path
    regions: list[Region] = Field(min_length=1)
    confidence_minimum: float = Field(ge=0,le=100)
    confidence_rule_reference: str = Field(min_length=1)


def assess_dssp_context(payload: DsspContextInput) -> dict:
    if payload.model.source_kind != 'prediction':
        raise ValueError('fusion_context_requires_exact_paired_prediction')
    atoms, confidence = payload.model.read()
    record=json.loads(payload.native_output.with_suffix('.run.json').read_text())
    model_hash=sha256(payload.model.path.read_bytes()).hexdigest()
    output_hash=sha256(payload.native_output.read_bytes()).hexdigest()
    if record['model_sha256']!=model_hash or record['output_sha256']!=output_hash or record['returncode']!=0:
        raise ValueError('DSSP_native_execution_does_not_bind_this_model_and_output')
    assignments,_=make_dssp_dict(str(payload.native_output))
    ca=[atom for atom in atoms if atom.name=='CA' and not atom.is_hetero]
    sequence=payload.model.expected_sequence
    rows=[]
    for region in payload.regions:
        if region.end>len(ca): raise ValueError('DSSP_region_outside_complete_fusion')
        residues=[]
        for index in range(region.start-1,region.end):
            atom=ca[index];key=(atom.chain,(' ',atom.residue,atom.insertion or ' '))
            assignment=assignments.get(key)
            if assignment and ('C' if assignment[0].islower() else assignment[0])!=sequence[index]:
                raise ValueError('DSSP_residue_identity_does_not_match_complete_fusion')
            score=confidence[(atom.chain,atom.residue,atom.insertion)]
            residues.append(dict(position_1based=index+1,residue=sequence[index],
                state=assignment[1] if assignment else None,plddt=score,
                high_confidence=score>payload.confidence_minimum))
        mapped=[row for row in residues if row['state'] is not None]
        credible=[row for row in mapped if row['high_confidence']]
        secondary=lambda values:sum(row['state'] in 'HGIEB' for row in values)/len(values) if values else None
        rows.append(dict(name=region.name,role=region.role,start=region.start,end=region.end,
            residues=residues,mapped_residues=len(mapped),high_confidence_residues=len(credible),
            secondary_fraction_all_mapped=secondary(mapped),
            secondary_fraction_high_confidence_mapped=secondary(credible),
            formal_M1_veto_allowed=False))
    return dict(schema_version='dssp-full-fusion-context-v1',regions=rows,tool='DSSP',
        tool_version=record['tool_version'],model_sha256=model_hash,output_sha256=output_hash,
        confidence_minimum=payload.confidence_minimum,confidence_operator='strict_greater_than',
        confidence_rule_reference=payload.confidence_rule_reference,
        assignment_definition='DSSP H/G/I helices and E/B strand/bridge; P/T/S/loop retained separately',
        scope='auxiliary_complete_fusion_context_not_isolated_PSIPRED_JPred_or_formal_M1_acceptance')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--dssp',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    payload=DsspContextInput.model_validate(json.loads(args.request.read_text()))
    payload.model.read()  # Validate the exact complete coordinate/confidence pair first.
    payload.native_output.parent.mkdir(parents=True,exist_ok=True)
    if payload.native_output.exists(): raise FileExistsError('Preserve an existing native DSSP job')
    command=[str(args.dssp.absolute()),'--output-format=dssp',str(payload.model.path),str(payload.native_output)]
    version=subprocess.check_output([str(args.dssp.absolute()),'--version'],text=True).strip()
    completed=subprocess.run(command,capture_output=True,check=True)
    payload.native_output.with_suffix('.stderr.txt').write_bytes(completed.stderr)
    payload.native_output.with_suffix('.run.json').write_text(json.dumps(dict(tool_name='DSSP',
        tool_version=version,returncode=completed.returncode,command=command,
        model_sha256=sha256(payload.model.path.read_bytes()).hexdigest(),
        output_sha256=sha256(payload.native_output.read_bytes()).hexdigest()),indent=2))
    result=assess_dssp_context(payload)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))


if __name__=='__main__': main()
