"""Typed, pool-aware projection of recorded amount-model output; no solver."""
from typing import Literal
from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .models import WorkflowError


class RecordedPool(BaseModel):
    model_config=ConfigDict(extra='ignore',allow_inf_nan=False)
    role: str
    volume_L: float=Field(gt=0)
    volume_source: dict
    amounts_umol: dict[str,list[float|None]]
    concentrations_um: dict[str,list[float|None]]


class RecordedCompartments(BaseModel):
    model_config=ConfigDict(extra='ignore',allow_inf_nan=False)
    schema_version: Literal['m4-compartment-amount-v1']
    formula_version: str
    status: str
    scenario: str
    time_h: list[float]=Field(max_length=100_000)
    pools: dict[str,RecordedPool]
    numerical_settings: dict

    @model_validator(mode='after')
    def check_recorded_units(self):
        if not self.time_h or any(a>=b for a,b in zip(self.time_h,self.time_h[1:])):
            raise ValueError('invalid_recorded_time_grid')
        settings=self.numerical_settings
        absolute=settings.get('amount_absolute_tolerance_umol')
        relative=settings.get('relative_tolerance')
        if (isinstance(absolute,bool) or not isinstance(absolute,(int,float)) or not isfinite(absolute) or absolute<=0
            or isinstance(relative,bool) or not isinstance(relative,(int,float)) or not isfinite(relative) or not 0<relative<1):
            raise ValueError('recorded_amount_tolerance_required')
        for pool in self.pools.values():
            if pool.volume_source.get('unit')!='L' or pool.volume_source.get('value')!=pool.volume_L:
                raise ValueError('pool_volume_source_mismatch')
            if set(pool.amounts_umol)!=set(pool.concentrations_um):
                raise ValueError('pool_species_mismatch')
            for species,amounts in pool.amounts_umol.items():
                concentrations=pool.concentrations_um[species]
                if len(amounts)!=len(self.time_h) or len(concentrations)!=len(self.time_h):
                    raise ValueError('pool_series_length_mismatch')
                for amount,concentration in zip(amounts,concentrations):
                    # Missing values remain missing, never zero. No inferred volume.
                    if amount is None or concentration is None: continue
                    if abs(amount-concentration*pool.volume_L)>absolute+relative*abs(amount):
                        raise ValueError('pool_amount_concentration_volume_mismatch')
        return self


def unwrap_recorded_result(raw):
    """Inherited outer synthetic flags cannot be lost behind a valid inner result."""
    scope={'claim_scope':None,'source_type':None,'formal_prediction_allowed':None}
    current=raw
    for _ in range(8):
        if not isinstance(current,dict): break
        if current.get('source_type') in {'synthetic','derived_from_synthetic','synthetic_forward'}:
            scope.update(source_type='synthetic',formal_prediction_allowed=False)
        elif scope['source_type'] != 'synthetic' and current.get('source_type'):
            scope['source_type'] = current['source_type']
        if current.get('formal_prediction_allowed') is False:
            scope['formal_prediction_allowed'] = False
        if current.get('claim_scope'): scope['claim_scope']=current['claim_scope']
        if current.get('schema_version')=='m4-compartment-amount-v1': return current,scope
        current=current.get('result')
    return None,scope


def compartment_series(raw):
    result,scope=unwrap_recorded_result(raw)
    if result is None: return None
    try: recorded=RecordedCompartments.model_validate(result)
    except ValueError as error:
        raise WorkflowError('recorded_compartment_units_or_volume_missing',private_detail=str(error)) from error
    columns={};units={};volumes={}
    for pool_id,pool in recorded.pools.items():
        columns[pool_id]={};units[pool_id]={}
        volumes[pool_id]={'role':pool.role,'volume_L':pool.volume_L,'source':pool.volume_source}
        for quantities,unit,label in ((pool.amounts_umol,'umol','amount'),(pool.concentrations_um,'uM','concentration')):
            for species,values in quantities.items():
                name=f'Compound {species} {label}'
                columns[pool_id][name]=values
                units[pool_id][name]=unit
    return {'schema_version':'m4-compartment-amount-v1','model_kind':'pool_specific_amount_model',
        'formula_version':recorded.formula_version,'time_unit':'h','time':recorded.time_h,
        'concentrations':columns,'column_units':units,'pool_volumes':volumes,**scope}
