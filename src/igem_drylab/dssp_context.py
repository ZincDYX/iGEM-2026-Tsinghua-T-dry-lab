"""Native DSSP assignments in complete fusion context, auxiliary evidence only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from Bio.PDB.DSSP import make_dssp_dict
import numpy as np
from pydantic import Field

from .design_analysis import ScientificAnalysisInput
from .region_assessment import Region, RegionAssessmentInput, assess_regions
from .template_geometry import StructureInput
from .pipeline.config import ConstructDefinition
from .constructs.sequence_qc import assemble_and_validate_construct
from .constructs.linker_features import normalize_amino_acid_sequence
from .workflow.models import SequenceRecord


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


class LinkerContextReviewInput(ScientificAnalysisInput):
    """An approved alternative branch; the isolated-predictor gap is preserved."""
    construct_definition: ConstructDefinition
    linker: SequenceRecord
    source_part_id: str = Field(min_length=1)
    occurrence: int = Field(default=1, ge=1)
    model: StructureInput
    native_output: Path
    confidence_minimum: float = Field(ge=0, le=100)
    confidence_rule_reference: str = Field(min_length=1)
    protocol_approval_reference: str = Field(min_length=1)


def review_linker_context(payload: LinkerContextReviewInput) -> dict:
    linker_roles={'linker','enzyme_ligand_linker','scaffold_linker','rigid_linker'}
    if payload.linker.role not in linker_roles:
        raise ValueError('context_review_requires_a_linker_source_record')
    construct=payload.construct_definition
    qc=assemble_and_validate_construct(construct_id=construct.id,
        ordered_part_ids=construct.ordered_part_ids(),
        part_sequences={**construct.sequences,**{p.id:p.sequence for p in construct.parts if p.sequence is not None}},
        coding_dna=None,forbidden_restriction_sites=None,require_sequence_evidence=False)
    sequence=qc.full_protein_sequence
    if qc.errors or sequence != payload.model.expected_sequence:
        raise ValueError('context_model_must_match_the_exact_declared_complete_construct')
    if payload.model.source_kind != 'prediction':
        raise ValueError('linker_context_requires_paired_complete_prediction')
    linker_sequence=normalize_amino_acid_sequence(payload.linker.sequence)
    regions=[]; matching=[]
    for index, (part,boundary) in enumerate(zip(construct.parts,qc.part_boundaries,strict=True)):
        fragment=part.sequence or construct.sequences.get(part.id)
        if not fragment:
            raise ValueError('context_review_requires_every_declared_part_sequence')
        fragment=normalize_amino_acid_sequence(fragment)
        regions.append(Region(name=f'{part.id}#{index+1}',role=part.kind,start=boundary.start_aa,end=boundary.end_aa))
        if part.id == payload.source_part_id:
            if part.kind not in linker_roles or fragment != linker_sequence:
                raise ValueError('context_linker_identity_does_not_match_declared_part')
            if payload.linker.role != 'linker' and part.kind != payload.linker.role:
                raise ValueError('context_linker_role_does_not_match_declared_part')
            matching.append(index)
    if payload.occurrence>len(matching):
        raise ValueError('requested_linker_occurrence_not_present_in_construct')
    index=matching[payload.occurrence-1]; region=regions[index]
    dssp=assess_dssp_context(DsspContextInput(model=payload.model,native_output=payload.native_output,
        regions=[region],confidence_minimum=payload.confidence_minimum,
        confidence_rule_reference=payload.confidence_rule_reference))
    observations=assess_regions(RegionAssessmentInput(candidate_id=construct.id,
        tool_input_id=payload.model.confidence_file.name.partition('_scores_rank_')[0],
        sequence=sequence,confidence_file=payload.model.confidence_file,
        regions=regions[max(0,index-1):index+2]))
    atoms,_=payload.model.read()
    ca=[atom for atom in atoms if atom.name=='CA' and not atom.is_hetero]
    def distance(first,second):
        return float(np.linalg.norm(ca[first-1].coordinate-ca[second-1].coordinate))
    assignments=dssp['regions'][0]
    complete=assignments['mapped_residues']==len(linker_sequence)
    credible=assignments['high_confidence_residues']==len(linker_sequence)
    return dict(schema_version='m1-linker-context-review-v1',candidate_id=payload.linker.id,
        construct_id=construct.id,localization_context=construct.localization_context,
        source_part_id=payload.source_part_id,source_fragment_role=payload.linker.role,
        source_fragment_localization=payload.linker.localization_context,
        occurrence=payload.occurrence,protocol_approval_reference=payload.protocol_approval_reference,
        original_protocol=dict(version='isolated-secondary-structure',status='missing_evidence',
            missing=['applicable isolated PSIPRED/JPred prediction'],preserved=True),
        approved_context_protocol=dict(version='complete-fusion-DSSP-geometry',
            status='observed_high_confidence' if complete and credible else 'observed_with_uncertainty',
            substituted_for_isolated_prediction=False,formal_M1_pass=False,formal_M1_veto_allowed=False),
        linker_region=region.model_dump(),DSSP=dssp,
        region_observations=observations['regions'],interdomain_pae=observations['interdomain_pae'],
        geometry=dict(unit='angstrom',CA_end_to_end=distance(region.start,region.end),
            preceding_peptide_CA_distance=distance(region.start-1,region.start) if region.start>1 else None,
            following_peptide_CA_distance=distance(region.end,region.end+1) if region.end<len(sequence) else None,
            interpretation='Observed coordinates only; no unreviewed reach, clash, SASA or rejection threshold.'),
        model_sha256=dssp['model_sha256'],confidence_sha256=observations['confidence_sha256'],
        scope='approved_context_review_not_isolated_prediction_or_complete_M1_acceptance')


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
