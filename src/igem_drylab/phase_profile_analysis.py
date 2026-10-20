"""Explicit space/time windows on raw CG profiles; no automatic phase guessing."""
import csv
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator
from .design_analysis import ScientificAnalysisInput


class PhaseProfileAnalysisInput(ScientificAnalysisInput):
    """CSV columns: step,lower,upper,density. Bin edges/units must be supplied."""
    path: Path
    density_unit: Literal['g/cm3','molecule/nm3','mol/L']
    coordinate_unit: Literal['angstrom','nm','reduced']
    start_step: int = Field(ge=0)
    end_step: int = Field(ge=0)
    dense_regions: list[tuple[float,float]] = Field(min_length=1)
    dilute_regions: list[tuple[float,float]] = Field(min_length=1)
    analysis_reference: str = Field(min_length=1)
    coordinate_frame_reference: str = Field(min_length=1)
    independent_replicate_id: str = Field(min_length=1)

    @model_validator(mode='after')
    def windows(self):
        if self.start_step>self.end_step:raise ValueError('phase_time_window_reversed')
        intervals=self.dense_regions+self.dilute_regions
        if any(not lo<hi for lo,hi in intervals):raise ValueError('phase_regions_require_ordered_bounds')
        if any(max(a,c)<min(b,d) for i,(a,b) in enumerate(intervals) for c,d in intervals[i+1:]):
            raise ValueError('phase_regions_must_not_overlap')
        return self


def analyse_phase_profile(payload: PhaseProfileAnalysisInput):
    with payload.path.open(newline='') as stream:rows=list(csv.DictReader(stream))
    if not rows or set(rows[0])!={'step','lower','upper','density'}:
        raise ValueError('phase_profile_requires_step_and_complete_bin_edges_and_density')
    frames={}
    for row in rows:
        step=int(row['step']);lo,hi,density=(float(row[k]) for k in ('lower','upper','density'))
        if step<0 or not all(math.isfinite(v) for v in (lo,hi,density)) or lo>=hi or density<0:
            raise ValueError('invalid_raw_phase_profile_bin')
        frames.setdefault(step,[]).append((lo,hi,density))
    observations=[]
    for step,bins in sorted(frames.items()):
        bins=sorted(bins)
        if any(b>c for (_,b,_),(c,_,_) in zip(bins,bins[1:])):
            raise ValueError('raw_phase_profile_bins_overlap')
        if not payload.start_step<=step<=payload.end_step:continue
        def average(regions):
            mass,width=0.,0.
            for start,end in regions:
                selected=[(lo,hi,value) for lo,hi,value in bins if lo>=start and hi<=end]
                if not selected or not math.isclose(selected[0][0],start) or not math.isclose(selected[-1][1],end) or any(not math.isclose(b,c) for (_,b,_),(c,_,_) in zip(selected,selected[1:])):
                    raise ValueError('phase_windows_must_match_contiguous_complete_native_bin_edges_no_interpolation')
                mass+=math.fsum((hi-lo)*v for lo,hi,v in selected);width+=end-start
            return mass/width
        dense,dilute=average(payload.dense_regions),average(payload.dilute_regions)
        observations.append(dict(step=step,dense=dense,dilute=dilute))
    if not observations:raise ValueError('explicit_phase_time_window_contains_no_observations')
    if len(observations)>2 and len({b['step']-a['step'] for a,b in zip(observations,observations[1:])})!=1:
        raise ValueError('irregular_saved_steps_require_explicit_time_weighting_not_equal_frame_mean')
    dense=float(np.mean([r['dense'] for r in observations]));dilute=float(np.mean([r['dilute'] for r in observations]))
    return dict(method='explicit_bin_width_weighted_phase_regions',density_unit=payload.density_unit,
        coordinate_unit=payload.coordinate_unit,dense_phase_concentration=dense,dilute_phase_concentration=dilute,
        enrichment_factor=dense/dilute if dilute>0 else None,observations=observations,
        independent_replicate_id=payload.independent_replicate_id,
        analysis_reference=payload.analysis_reference,coordinate_frame_reference=payload.coordinate_frame_reference,
        uncertainty=None,llps_score=None,saturation_concentration=None,
        scope='declared_single_replicate_equal_weight_saved_frames_not_independent_frame_CI_or_M1_ranking')
