"""PS-v3 independent synthetic runner; never executes a script from an upload.

Canonical changes regenerate kernel inputs, not hand-written endpoints. This
uses the existing M3 and competitive amount-model kernels without new solvers.
"""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile,BadZipFile

from .models import Contract,WorkflowError

SET_ID='PS-v3-SYNTHETIC'


def reject_synthetic_formal_input(value):
    if isinstance(value,dict):
        if (value.get('source_type') in {'synthetic','derived_from_synthetic','synthetic_forward'}
            or value.get('formal_prediction_allowed') is False or value.get('parameter_set_id')==SET_ID):
            raise WorkflowError('synthetic_input_not_formal_evidence')
        for child in value.values(): reject_synthetic_formal_input(child)
    elif isinstance(value,list):
        for child in value: reject_synthetic_formal_input(child)


def read_ps_archive(raw):
    if len(raw)>20_000_000: raise WorkflowError('scientific_upload_budget_exceeded')
    try:
        with ZipFile(BytesIO(raw)) as archive:
            infos=archive.infolist()
            names=[item.filename for item in infos]
            from .binary_import import validate_archive_members
            validate_archive_members(infos)
            roots=[name[:-len('canonical_parameters.json')] for name in names if name.endswith('canonical_parameters.json')]
            if len(roots)!=1: raise WorkflowError('synthetic_ps_canonical_missing_or_ambiguous')
            root=roots[0]
            canonical=json.loads(archive.read(root+'canonical_parameters.json'))
            if (canonical.get('parameter_set_id')!=SET_ID or canonical.get('source_type')!='synthetic'
                or canonical.get('formal_prediction_allowed') is not False or canonical.get('watermark')!='SYNTHETIC_PIPELINE_TEST'):
                raise WorkflowError('synthetic_ps_scope_cannot_be_promoted')
            inputs={}
            for case in ('C1','C2','E1','E2'):
                inputs[case]={'m4':json.loads(archive.read(root+'solver_inputs/'+case+'_m4.json'))}
                if case.startswith('E'): inputs[case]['m3']=json.loads(archive.read(root+'solver_inputs/'+case+'_m3.json'))
            # Explicit named members only: no extraction, arbitrary paths or code execution.
            return canonical,inputs
    except (BadZipFile,KeyError,json.JSONDecodeError,UnicodeError) as error:
        raise WorkflowError('invalid_synthetic_ps_package') from error


def preview_ps_archive(application,filename,raw):
    canonical,_=read_ps_archive(raw)
    application.boundary.check(canonical)
    application.boundary.check_bytes(raw)
    root=application.data_dir/'imports';root.mkdir(parents=True,exist_ok=True)
    path=root/(sha256(raw).hexdigest()+'.zip');path.write_bytes(raw)
    file=application.boundary.asset(path,fresh=True,logical_name=filename)
    dataset={'id':file['id'],'file_id':file['id'],'name':filename,'kind':'synthetic_ps_v3',
        'parameter_set_id':SET_ID,'source_type':'synthetic','formal_prediction_allowed':False,
        'canonical_parameters':canonical,'supported_scope':'Closed reference demonstration; not fermentation, M2 validation or ER advantage'}
    return {'kind':'synthetic_ps_v3','file':file,'patch':{'datasets':[dataset]}}


def build_case(canonical,template,case):
    from igem_drylab.m3_equilibrium import M3EquilibriumInput,solve_m3_equilibrium
    from igem_drylab.m4_compartments import CompartmentNetworkInput
    from igem_drylab.full_network import COMPOUNDS,REACTIONS
    phi=canonical['phi_LLPS'] if case.startswith('E') else 0.
    total=canonical['high_enzyme_total_uM'] if case.endswith('2') else canonical['low_enzyme_total_uM']
    model=canonical['M4_demo']
    if model['boundaries'] or model['steady_initial_guesses_umol'] or model['partition_model']!='rapid_equilibrium':
        raise WorkflowError('synthetic_ps_closed_transient_scope_required')
    m3_input=None;m3_result=None
    distribution={enzyme:{'dilute':total} for enzyme in ('OC','DMT')}
    if phi:
        data=deepcopy(template['m3'])
        data.update(phi=phi,c_dense_um=(canonical['scaffold_total_monomer_uM']-(1-phi)*canonical['scaffold_dilute_monomer_uM'])/phi,
            c_scaffold_total_um=canonical['scaffold_total_monomer_uM'],c_sat_um=canonical['scaffold_dilute_monomer_uM'],
            s_sh3=canonical['sites_per_scaffold_monomer']['OC'],s_pdz=canonical['sites_per_scaffold_monomer']['DMT'],
            eta_acc_sh3=canonical['ideal_site_accessibility_demo'],eta_acc_pdz=canonical['ideal_site_accessibility_demo'],
            eta_bind_sh3=canonical['ideal_site_binding_efficiency_demo'],eta_bind_pdz=canonical['ideal_site_binding_efficiency_demo'],
            kd_sh3_um=canonical['Kd_uM']['OC'],kd_pdz_um=canonical['Kd_uM']['DMT'],
            k_oc=canonical['free_partition']['OC'],k_dmt=canonical['free_partition']['DMT'],
            c_oc_total_um=total,c_dmt_total_um=total,joint_occupancy_independent=canonical['independent_site_occupancy_demo'])
        if data['m2_geometry_id']!='DEMO_ONLY_NO_M2_GEOMETRY' or data['site_count_basis']!='scaffold_monomer' or data['c_dense_basis']!='scaffold_monomer':
            raise WorkflowError('synthetic_ps_original_ideal_site_scope_required')
        if any(data.get(key) is not None for key in ('v_scaffold_nm3','v_enzyme_nm3','avidity_sh3','avidity_pdz','r_target')):
            raise WorkflowError('synthetic_ps_undefined_capacity_or_avidity_not_allowed')
        m3_input=M3EquilibriumInput.model_validate(data)
        solved=solve_m3_equilibrium(m3_input)
        m3_result=solved.model_dump(mode='json')
        if solved.status!='valid': raise WorkflowError('synthetic_ps_recruitment_not_solved')
        distribution={enzyme:{'dense':getattr(solved,enzyme.lower()).total_dense_um,
            'dilute':getattr(solved,enzyme.lower()).free_dilute_um} for enzyme in ('OC','DMT')}
    data=deepcopy(template['m4'])
    if (data['scenario']!=('cytosolic_LLPS' if phi else 'no_LLPS') or data['evidence_mode']!='conditional_model'
        or data['boundaries']!=model['boundaries'] or data['steady_initial_guesses_umol']!=model['steady_initial_guesses_umol']):
        raise WorkflowError('synthetic_ps_cannot_be_formal_or_ER')
    volume=model['reference_volume_L']
    for pool in data['pools']:
        phase=pool['pool_id']
        if phase not in {'dense','dilute'} or (not phi and phase!='dilute'):
            raise WorkflowError('synthetic_ps_unknown_pool')
        pool_volume=(phi if phase=='dense' else 1-phi)*volume
        pool['volume']['value']=pool_volume
        for enzyme,quantity in pool['enzyme_amounts'].items():
            quantity['value']=distribution[enzyme][phase]*pool_volume if enzyme in distribution else model['PTR_PT_amount_umol']
            pool['enzyme_activity_ratios'][enzyme]['value']=canonical['activity_ratios'][phase][enzyme]
        fraction=(phi*canonical['metabolite_Kp']['10'] if phase=='dense' else 1-phi)/((1-phi)+phi*canonical['metabolite_Kp']['10'])
        for compound in COMPOUNDS:
            data['initial_amounts_umol'][phase][compound]['value']=(model['initial_compound10_reference_uM']*volume*fraction
                if compound=='10' else model['initial_other_compounds_umol'])
    for interface in data['interfaces']:
        for compound in COMPOUNDS: interface['second_over_first_partition'][compound]['value']=canonical['metabolite_Kp'][compound]
    for reaction,identity in zip(data['reactions'],REACTIONS):
        rid,enzyme,substrate,product=identity
        kinetics=canonical['kinetics'][rid]
        if kinetics['enzyme']!=enzyme or kinetics['conversion']!=substrate+'->'+product:
            raise WorkflowError('synthetic_ps_reaction_identity_changed')
        reaction.update(kcat_per_h=kinetics['kcat_per_h'],km_um=kinetics['Km_uM'])
    data.update(time_grid_h=model['time_grid_h'],numerics=model['numerics'])
    return m3_input,m3_result,CompartmentNetworkInput.model_validate(data)


class SyntheticPSInput(Contract):
    package_file: Path


def run_ps_tool(payload,context):
    from igem_drylab.m4_compartments import solve_compartment_network
    canonical,inputs=read_ps_archive(payload.package_file.read_bytes())
    context.work_dir.mkdir(parents=True,exist_ok=True)
    scope={'source_type':'synthetic','parameter_set_id':SET_ID,'formal_prediction_allowed':False,
        'm2_geometry_verified':False,'provided_phi_is_synthetic_not_measured':True,
        'claim_scope':'Synthetic closed reference demonstration; not fermentation, formal M1–M4 or experimental validation'}
    cases={}
    for case,template in inputs.items():
        m3_input,m3_result,m4_input=build_case(canonical,template,case)
        result=solve_compartment_network(m4_input)
        if result['status']!='numerically_solved': raise WorkflowError('synthetic_ps_numerical_admission_failed')
        wrapper={**scope,'result':result}
        destination=context.work_dir/(case+'-amounts.json')
        destination.write_text(json.dumps(wrapper,allow_nan=False,indent=2),encoding='utf-8')
        cases[case]={**scope,'m3':m3_result,'m4':wrapper,'trajectory_artifact':str(destination),
            'solver_inputs':{'m3':m3_input.model_dump(mode='json') if m3_input else None,'m4':m4_input.model_dump(mode='json')}}
    return {**scope,'schema_version':'synthetic-ps-v3-run-v1','canonical_parameters':canonical,'cases':cases,
        'E3':{**scope,'status':'blocked','missing_inputs':canonical['ER_E3_missing'],'result':None}}
