"""Explicit CG sampling diagnostics, never an LLPS or M1 pass certificate."""
from importlib.metadata import version
import math
import numpy as np
from pydantic import Field, model_validator
from scipy.stats import t
from .design_analysis import ScientificAnalysisInput


class ReplicateTrace(ScientificAnalysisInput):
    seed: int
    values: list[float] = Field(min_length=4)
    source_reference: str = Field(min_length=1)


class SamplingInput(ScientificAnalysisInput):
    candidate_id: str
    observable: str
    unit: str
    traces: list[ReplicateTrace] = Field(min_length=1)
    expected_seeds: list[int] = Field(min_length=2)
    sampling_interval_ns: float = Field(gt=0)
    confidence_level: float = Field(gt=0,lt=1)
    relative_halfwidth_target: float = Field(gt=0)
    protocol_reference: str = Field(min_length=1)

    @model_validator(mode='after')
    def independent_seeds(self):
        seeds=[trace.seed for trace in self.traces]
        if len(set(seeds))!=len(seeds) or len(set(self.expected_seeds))!=len(self.expected_seeds) or set(seeds)-set(self.expected_seeds):
            raise ValueError('sampling_requires_distinct_declared_replicate_seeds')
        if any(not np.all(np.isfinite(trace.values)) for trace in self.traces):
            raise ValueError('sampling_trace_contains_nonfinite_observations')
        return self


def _statistical_inefficiency(values):
    from pymbar.timeseries import statistical_inefficiency
    if version('pymbar')!='4.0.3':raise ValueError('sampling_requires_tested_pymbar_4_0_3')
    return float(statistical_inefficiency(values,fast=False,fft=False,mintime=3))


def _ci(mean, sem, df, confidence):
    half=float(t.ppf((1+confidence)/2,df)*sem)
    return [float(mean-half),float(mean+half)],half


def assess_sampling(payload: SamplingInput):
    replicates=[];means=[];alpha=payload.confidence_level
    for trace in payload.traces:
        values=np.asarray(trace.values,dtype=float);mean=float(values.mean());means.append(mean)
        row=dict(seed=trace.seed,saved_production_samples=len(values),mean=mean,source_reference=trace.source_reference)
        if np.var(values)==0:
            row.update(status='constant_trace_autocorrelation_undefined',statistical_inefficiency=None,
                drift_assessed=False,relative_precision_target_met=False)
            replicates.append(row);continue
        g=_statistical_inefficiency(values);block_length=max(1,math.ceil(g));blocks=len(values)//block_length
        row.update(statistical_inefficiency=g,integrated_autocorrelation_time_ns=(g-1)/2*payload.sampling_interval_ns,
            effective_sample_count=len(values)/g,equal_block_samples=block_length,equal_block_count=blocks,
            trailing_partial_block_samples=len(values)%block_length,
            partial_block_mean=float(values[blocks*block_length:].mean()) if len(values)%block_length else None)
        # Original full production mean retains every sample. The block SEM and
        # split-half drift diagnostic use equal blocks, with the remainder
        # explicitly reported, not silently deleted from the native trajectory.
        if blocks<4:
            row.update(status='insufficient_blocks_for_split_drift',drift_assessed=False,relative_precision_target_met=False)
            replicates.append(row);continue
        block_means=values[:blocks*block_length].reshape(blocks,block_length).mean(axis=1)
        sem=float(block_means.std(ddof=1)/np.sqrt(blocks));ci,half=_ci(mean,sem,blocks-1,alpha)
        a,b=np.array_split(block_means,2);va=float(np.var(a,ddof=1)/len(a));vb=float(np.var(b,ddof=1)/len(b))
        delta=float(b.mean()-a.mean());variance=va+vb
        if variance>0:
            df=variance**2/(va**2/(len(a)-1)+vb**2/(len(b)-1));drift_ci,_=_ci(delta,np.sqrt(variance),df,alpha)
        else:drift_ci=[delta,delta]
        significant=not drift_ci[0]<=0<=drift_ci[1]
        relative=half/abs(mean) if mean else None
        row.update(status='sampling_diagnostics_computed',block_standard_error=sem,confidence_interval=ci,
            relative_CI_halfwidth=relative,relative_precision_target_met=relative is not None and relative<=payload.relative_halfwidth_target,
            drift_assessed=True,split_block_mean_difference=delta,split_difference_confidence_interval=drift_ci,
            drift_detected=significant,block_means=block_means.tolist())
        replicates.append(row)
    complete=set(trace.seed for trace in payload.traces)==set(payload.expected_seeds)
    ensemble_mean=float(np.mean(means));ensemble_ci=None;relative=None
    if complete:
        sem=float(np.std(means,ddof=1)/np.sqrt(len(means)));ensemble_ci,half=_ci(ensemble_mean,sem,len(means)-1,alpha)
        relative=half/abs(ensemble_mean) if ensemble_mean else None
    ready=complete and relative is not None and relative<=payload.relative_halfwidth_target and all(
        r.get('drift_assessed') and not r.get('drift_detected') and r.get('relative_precision_target_met') for r in replicates)
    return dict(candidate_id=payload.candidate_id,observable=payload.observable,unit=payload.unit,
        confidence_level=alpha,relative_halfwidth_target=payload.relative_halfwidth_target,
        expected_seeds=payload.expected_seeds,observed_seeds=[trace.seed for trace in payload.traces],replicates=replicates,
        mean_of_independent_replicate_means=ensemble_mean,independent_replicate_CI=ensemble_ci,
        independent_replicate_relative_halfwidth=relative,
        sampling_status='declared_diagnostics_met' if ready else 'sampling_not_converged' if complete else 'independent_replicates_incomplete',
        method='pymbar4.0.3 non-fast statistical inefficiency; ceil(g) equal blocks; Student-t block/replicate CI; Welch split-block mean difference',
        method_source='https://pymbar.readthedocs.io/en/stable/timeseries.html',protocol_reference=payload.protocol_reference,
        formal_M1_pass=False,LLPS_proven=False,
        limitations='No detected drift is not proof of stationarity. Equal-block errors assume adequate residual decorrelation. Diagnostics do not prove slab coexistence, finite-size independence, fusion assembly or LLPS.')
