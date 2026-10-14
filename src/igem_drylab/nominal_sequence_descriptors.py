"""Document 2026-10-14 nominal charge and FUS sticker descriptors.

Author localCIDER kappa is not an exact permutation maximum. KR/DE nominal
charges do not represent pH-dependent physical net charge (H is neutral here).
"""
from importlib.metadata import version
from math import sqrt,fsum
from typing import Literal
from pydantic import Field
from .design_analysis import ScientificAnalysisInput


class NominalDescriptorsInput(ScientificAnalysisInput):
    sequence: str = Field(min_length=1,pattern=r'^[ACDEFGHIKLMNPQRSTVWY]+$')
    sequence_family: Literal['FUS_LC','other']


def compute_nominal_descriptors(payload: NominalDescriptorsInput):
    from localcider.sequenceParameters import SequenceParameters
    if version('localcider')!='0.1.21':raise ValueError('nominal_descriptors_require_localCIDER_0_1_21')
    sequence=payload.sequence;length=len(sequence)
    charges=[1 if aa in 'KR' else -1 if aa in 'DE' else 0 for aa in sequence]
    scd=fsum(charges[i]*charges[j]*sqrt(j-i) for i in range(length) for j in range(i+1,length))/length
    raw=SequenceParameters(sequence).get_kappa() if length>=6 else None
    usable=raw is not None and 0<=raw<=1
    return dict(method='localCIDER_kappa_5_6',native_version=version('localcider'),
        kappa_raw=raw,kappa=raw if usable else None,
        kappa_status='descriptive' if usable else 'not_applicable',
        scd_nominal_KR_DE=scd,
        scd_formula='sum(i<j,q_i*q_j*sqrt(j-i))/L; q(KR)=1,q(DE)=-1,others=0',
        nominal_ncpr=sum(charges)/length,nominal_fcr=sum(abs(q) for q in charges)/length,
        tyr_count=sequence.count('Y'),length=length,
        fus_tyr_sticker_fraction=sequence.count('Y')/length if payload.sequence_family=='FUS_LC' else None,
        aromatic_fraction=sum(sequence.count(a) for a in 'FWY')/length,arg_fraction=sequence.count('R')/length,
        scope='nominal_sequence_descriptors_not_effective_binding_sites_LLPS_probability_or_physical_charge',
        source_references=['https://doi.org/10.1073/pnas.1304749110','https://github.com/Pappulab/localCIDER',
                           'https://doi.org/10.1063/1.4929391'])
