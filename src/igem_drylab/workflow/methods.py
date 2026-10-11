"""Read-only presentation registry, transcribed from the reviewed contracts.

This is NOT a formula evaluator. The linked production functions remain the
only calculators. Regime candidates, source discrepancies and extensions are
kept separate; rendering a method never grants evidence or parameter approval.
"""
from typing import Literal
from pydantic import Field
from .models import Contract
from .custom_formula import FormulaSpec, expression_latex


class MethodFormula(Contract):
    id: str
    title: str
    latex: str
    assumptions: list[str]
    implementation: list[str]
    status: Literal['implemented', 'conditional', 'undefined_in_source', 'source_discrepancy'] = 'implemented'


class MethodStep(Contract):
    id: str
    title: str
    description: str


class MethodDefinition(Contract):
    id: str
    version: str
    title: str
    scope: str
    source_reference: str
    source_version: str
    steps: list[MethodStep]
    formulas: list[MethodFormula]
    symbols: dict[str,str]
    tools: list[str]
    discrepancies: list[str] = Field(default_factory=list)
    formal_formula_editable: Literal[False] = False


class ModuleTool(Contract):
    id: str
    name: str
    version: str
    description: str
    runtime: str
    status: Literal['registered_not_tested'] = 'registered_not_tested'
    license: str
    input_names: list[str]
    output_scope: str


class ModuleMethodView(Contract):
    project_id: str
    project_revision: int
    methods: list[MethodDefinition]
    tool: ModuleTool
    configured_mode: str | None
    limitations: list[str]
    parameter_records: list[dict] = Field(default_factory=list)
    parameter_requirements: list[dict] = Field(default_factory=list)
    parameter_source_options: dict[str,list[str]] = Field(default_factory=dict)


class ToolCatalogPage(Contract):
    items: list[ModuleTool]
    has_more: bool


class MethodDraftInput(Contract):
    base_method_id: str
    base_version: str
    title: str = Field(min_length=1,max_length=200)
    formula_id: str
    latex: str = Field(min_length=1,max_length=8000)
    reason: str = Field(min_length=1,max_length=4000)
    source_reference: str = Field(min_length=1,max_length=2000)
    previous_id: str | None = None
    expected_project_revision: int
    execution_spec: FormulaSpec | None = None


class MethodDraftView(Contract):
    id: str
    project_id: str
    project_revision: int
    version: int
    base_method_id: str
    base_version: str
    title: str
    formula_id: str
    original_latex: str
    latex: str
    reason: str
    source_reference: str
    previous_id: str | None
    validation_status: Literal['unvalidated'] = 'unvalidated'
    executable: bool = False
    execution_spec: FormulaSpec | None = None


class MethodDraftPage(Contract):
    items: list[MethodDraftView]
    has_more: bool


class MethodDrafts:
    """Immutable proposed versions; original formulas/solvers are untouched.

    Scalar execution is separate and unvalidated; originals are never replaced.
    """
    def __init__(self,store,boundary):
        self.store,self.boundary=store,boundary
        with store.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS method_drafts(id TEXT PRIMARY KEY,project_id TEXT NOT NULL,payload TEXT NOT NULL)')

    def list(self,project_id,offset=0):
        import json
        self.store.project(project_id)
        with self.store.connection() as db:
            rows=db.execute('SELECT payload FROM method_drafts WHERE project_id=? ORDER BY rowid DESC LIMIT 21 OFFSET ?',(project_id,offset)).fetchall()
        return MethodDraftPage(items=[MethodDraftView.model_validate(json.loads(row[0])) for row in rows[:20]],has_more=len(rows)>20)

    def save(self,project_id,request):
        import json
        from uuid import uuid4
        from .store import canonical
        from .models import WorkflowError
        self.boundary.check(request.model_dump(mode='json'))
        method=METHODS.get(request.base_method_id)
        if method is None or method.version!=request.base_version:
            raise WorkflowError('method_source_version_changed',status_code=409)
        original=next((formula for formula in method.formulas if formula.id==request.formula_id),None)
        if original is None: raise WorkflowError('unknown_method_formula')
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            # Project revision and parent ownership are checked in this write.
            project=db.execute('SELECT payload FROM projects WHERE id=?',(project_id,)).fetchone()
            if project is None: raise KeyError(project_id)
            revision=json.loads(project[0])['revision']
            if revision!=request.expected_project_revision:
                raise WorkflowError('project_revision_changed',status_code=409)
            version=1
            if request.previous_id:
                row=db.execute('SELECT payload FROM method_drafts WHERE id=? AND project_id=?',(request.previous_id,project_id)).fetchone()
                if row is None: raise WorkflowError('method_draft_parent_not_owned',status_code=403)
                previous=MethodDraftView.model_validate_json(row[0])
                if previous.base_method_id!=method.id or previous.formula_id!=original.id:
                    raise WorkflowError('method_draft_parent_mismatch')
                version=previous.version+1
            fields=request.model_dump(exclude={'expected_project_revision'})
            if request.execution_spec is not None:
                fields['latex']=expression_latex(request.execution_spec.expression)
            result=MethodDraftView(id=str(uuid4()),project_id=project_id,project_revision=revision,version=version,
                original_latex=original.latex,executable=request.execution_spec is not None,
                **fields)
            db.execute('INSERT INTO method_drafts VALUES(?,?,?)',(result.id,project_id,canonical(result.model_dump(mode='json'))))
        return result

    def workflow(self,project_id,draft_id):
        from .models import Workflow, WorkflowNode, LiteralInput, WorkflowError
        from .custom_formula import FormulaExecution
        self.store.project(project_id)
        with self.store.connection() as db:
            row=db.execute('SELECT payload FROM method_drafts WHERE id=? AND project_id=?',(draft_id,project_id)).fetchone()
        if row is None: raise WorkflowError('method_draft_not_owned',status_code=403)
        draft=MethodDraftView.model_validate_json(row[0])
        if draft.execution_spec is None: raise WorkflowError('method_draft_has_no_execution_spec')
        payload=FormulaExecution(method_id=draft.id,method_version=draft.version,title=draft.title,
            base_method_id=draft.base_method_id,base_version=draft.base_version,latex=expression_latex(draft.execution_spec.expression),
            reason=draft.reason,source_reference=draft.source_reference,spec=draft.execution_spec)
        return Workflow(id='custom-formula-'+draft.id,name=draft.title,
            description='Separate unvalidated exploratory formula. Review the frozen expression, all values, units and sources; Accept then Start. Not formal M1–M4 evidence.',
            nodes=[WorkflowNode(id='formula',label=draft.title,tool_id='workflow.custom_formula',
                inputs={name:LiteralInput(value=value) for name,value in payload.model_dump(mode='json').items()})])


def module_method(project, definition):
    from .scientific_project import ScientificProject
    science = ScientificProject.model_validate(project.scientific_project) if project.scientific_project else None
    method = method_for_tool(definition.id)
    configured_mode = None
    methods = [method] if method else []
    if science:
        config = science.config
        if definition.id == 'project.m3':
            configured_mode = config.stages.m3_concentration.recruitment_mode
        if definition.id == 'project.m4':
            configured_mode = config.stages.m4_reaction.network_mode
        if definition.id in {'project.m1','project.m2','project.m3','project.m4'}:
            from igem_drylab.compartments import scenario_for_construct
            if any(scenario_for_construct(config, item.id) == 'er_anchored' for item in config.inputs.constructs):
                methods.append(ER)
    from igem_drylab.parameters.requirements import requirements_for_stage
    requirements=requirements_for_stage(science.config,definition.id.removeprefix('project.')) if science and definition.id in {'project.m3','project.m4'} else []
    names={requirement.name for requirement in requirements}
    source_options={}
    if science:
        from igem_drylab.parameters import ParameterRegistry
        from igem_drylab.parameters.registry import resolve_requirement
        for original in science.config.parameters:
            requirement=next((item for item in requirements if item.name==original.name),None)
            if requirement is None: continue
            compatible=[]
            for source in science.config.parameters:
                if (source.parameter_id==original.parameter_id or source.name!=original.name
                        or source.construct_id!=original.construct_id or source.condition_id!=original.condition_id):
                    continue
                result=resolve_requirement(ParameterRegistry([source.model_copy(update={'supersedes':None})]),
                    requirement,science.config.experimental_context,allow_assumptions=science.config.execution.allow_assumptions,
                    construct_id=original.construct_id,condition_id=original.condition_id,
                    require_provenance=science.config.execution.mode=='real')
                if result.status=='resolved': compatible.append(source.parameter_id)
            source_options[original.parameter_id]=compatible
    return ModuleMethodView(project_id=project.id,project_revision=project.revision,methods=methods,
        tool=ModuleTool(id=definition.id,name=definition.name,version=definition.version,description=definition.description,
            runtime=definition.runtime,license='Apache-2.0' if definition.runtime == 'builtin' else 'See the registered tool/plugin license; third-party licensing is independent.',
            input_names=list(definition.input_model.model_fields),output_scope='Registered output contract; scientific readiness is assessed separately.'),
        configured_mode=configured_mode,limitations=[
            'Registration/configuration is not a real successful tool job. External tool evidence and license gates remain authoritative.',
            'The original method is shown for review. A differently configured historical/dynamic mode is not relabeled as this method.',
            'Custom scalar formulas use a separate unit-checked exploratory tool, not an original method or approved scientific evidence. LaTeX alone is not executable.'],
        parameter_source_options=source_options,
        parameter_requirements=[requirement.model_dump(mode='json') for requirement in requirements],
        parameter_records=[record.model_dump(mode='json') for record in science.config.parameters if record.name in names] if science else [])


def formula(id, title, latex, function, *assumptions, status='implemented'):
    return MethodFormula(id=id,title=title,latex=latex,implementation=[function],assumptions=list(assumptions),status=status)


def steps(rows):
    return [MethodStep(id=id,title=title,description=description) for id,title,description in rows]


M1_FUNCTION = 'igem_drylab.constructs.linker_features.compute_sequence_features'
M2_FUNCTION = 'igem_drylab.structure_metrics.aligned_ca_rmsds'
M3_FUNCTION = 'igem_drylab.m3_equilibrium.solve_m3_equilibrium'
M4_FUNCTION = 'igem_drylab.m4_steady_state.steady_state_evaluator'

M1 = MethodDefinition(id='m1-v3',version='m1-v3-2026-09-27',title='M1 V3 — sequence negative screen',
    scope='Sequence statistics and three veto levels, risk tiers and reviewed ranking. No LLPS, activity or expression probability.',
    source_reference='docs/m1_v3_implementation_contract.md',source_version='2026-09-27, original specification §4 and appendix A',
    steps=steps([('0','Actual sequences','Candidate and fixed backbone sequences, explicit topology and segment roles.'),
        ('1','First veto','Frozen residue definitions, length, hydrophobicity and runs; no invented algorithms.'),
        ('2','Second veto','Exact-sequence real predictor evidence: disorder, secondary structure, targeting, membrane and aggregation.'),
        ('3','Fusion veto','Assemble declared parts and check full-length predictor evidence and junction risks.'),
        ('4','Risk tier','Count reviewed high-risk hits: zero low, one medium, at least two high.'),
        ('5','Reviewed ranking','Only surviving low/medium candidates; requires sourced normalization, directions and weights.')]),
    formulas=[
        formula('length','Length',r'L=|s|',M1_FUNCTION,'Nonempty normalized amino-acid sequence.'),
        formula('fraction','Residue-set fractions',r'f_A=\frac{1}{L}\sum_{j=1}^{L}\mathbf{1}\{s_j\in A\}',M1_FUNCTION,'A is a source-fixed residue set, not chosen for a candidate.'),
        formula('charge','Net charge proxy',r'q=\frac{n_K+n_R-n_D-n_E}{L}',M1_FUNCTION,'Not measured net charge at pH; histidine is not added.'),
        formula('entropy','Shannon entropy',r'H=-\sum_{a:p_a>0}p_a\log_2p_a,\quad p_a=\frac{n_a}{L}',M1_FUNCTION),
        formula('top2','Top-two residue fraction',r'f_{top2}=\frac{n_{(1)}+n_{(2)}}{L}',M1_FUNCTION),
        formula('run','Longest hydrophobic run',r'h_{max}=\max\{|I|:I\text{ contiguous},\ s_j\in A_{hydro}\ \forall j\in I\}',M1_FUNCTION,'Frozen hydrophobic residue set.'),
        formula('hydropathy','Mean hydropathy',r'\bar h=\frac{1}{L}\sum_{j=1}^{L}h(s_j)',M1_FUNCTION,'Frozen Kyte–Doolittle scale and definition version.'),
        formula('disorder','Disorder mean and fraction',r'\bar d=\frac{1}{L}\sum_j d_j,\quad f_d=\frac{1}{L}\sum_j\mathbf1\{d_j\ge d_{tool}\}',
            'igem_drylab.constructs.linker_features.parse_iupred2a_output','Actual IUPred evidence and its declared boundary, not a fabricated profile.'),
        formula('secondary','Secondary-structure fraction',r'f_{ss}=\frac{1}{L}\sum_j\mathbf1\{SS_j\in\{\alpha,\beta\}\}',
            'igem_drylab.constructs.linker_features.parse_secondary_structure_output','Real PSIPRED/JPred output; rigid-linker secondary structure is reviewed, not treated as flexible-linker failure.'),
        formula('risk','Reviewed risk tiers',r'tier(h)=\begin{cases}\text{low}&h=0\\\text{medium}&h=1\\\text{high}&h\ge2\end{cases}',
            'igem_drylab.m1_prioritization.prioritize_m1','h counts reviewed high-risk hits after all vetoes.'),
        formula('ranking','Reviewed weighted ranking',r'score=\frac{\sum_i w_i\tilde s_i}{\sum_i w_i}',
            'igem_drylab.m1_prioritization.prioritize_m1','Only with reviewed normalization, direction, weights and ranking reference; otherwise unavailable.',status='conditional'),
        formula('undefined','Undefined source algorithms',r'charge\_blockiness,\ multivalency\_density:\ \text{unavailable}',M1_FUNCTION,
            'The source does not define reviewed algorithms; no numerical substitute.',status='undefined_in_source')],
    symbols={'s':'Actual amino-acid sequence','L,n_a':'Residue counts (1)','A':'Frozen residue set','h':'Hydropathy scale; risk hit count in the tier formula',
        'd_j':'Actual predictor disorder score (1)','SS_j':'Actual secondary-structure state','w_i, tilde s_i':'Reviewed weight and normalized score (1)'},
    tools=['IUPred2A','PSIPRED / JPred','SignalP','DeepTMHMM','TANGO / PASTA','SEG','ProtParam','Reviewed consensus predictors'])

M2 = MethodDefinition(id='m2-v2',version='m2-v2-2026-09-27',title='M2 V2 — confidence-gated structure and geometry',
    scope='L1 enzyme fusion, L2 scaffold subunit, L3 template placement/assembly; Q1–Q4 are negative screens, not enzyme activity or channeling proof.',
    source_reference='docs/m2_v2_implementation_contract.md',source_version='2026-09-27, original specification §5 and appendix B',
    steps=steps([('L1','Fusion enzymes','Actual full-length OC/DMT fusion models and confidence.'),('L2','Scaffold subunits','Actual scaffold subunit models and declared domain boundaries.'),
        ('L3','Assembly and placement','Registered reference assembly and complexes; multiple template placements, not de novo whole-cage certainty.'),
        ('Q1','Fold and functional pocket','Mapped core alignment, pocket SASA, distance/clashes and optional same-configuration docking.'),
        ('Q2','Recruitment accessibility','Ligand and SH3/PDZ site exposure; accessibility is not Kd.'),
        ('Q3','Scaffold topology','FTH1 interface, disorder and actual stoichiometry; flexible-linker uncertainty retained.'),
        ('Q4','Joint occupancy','Concrete site conflict graph, separate OC/DMT ranges and Pareto combinations.')]),
    formulas=[formula('core','Aligned core Cα RMSD',r'RMSD_C=\sqrt{\frac{1}{|C|}\sum_{j\in C}\|Rx_j+t-y_j\|^2}',M2_FUNCTION,'Kabsch fit on the declared mapped core C. All mapped Cα atoms must exist.'),
        formula('pocket','Pocket Cα RMSD after core fit',r'RMSD_P=\sqrt{\frac{1}{|P|}\sum_{j\in P}\|Rx_j+t-y_j\|^2}',M2_FUNCTION,'Same core transform; not a separate fit to the pocket.'),
        formula('sasa','Same-site SASA retention',r'\eta_{SASA}=\frac{SASA(\text{fusion or assembly, site})}{SASA(\text{reference or isolated, same site})}',
            'igem_drylab.structure_metrics.residue_sasa','Identical FreeSASA configuration and residue set. SASA does not produce affinity.'),
        formula('distance','Introduced tail to pocket distance',r'd_{min}=\min_{a\in tail,b\in pocket}\|a-b\|','igem_drylab.structure_metrics.tail_pocket_min_distance','Declared heavy-atom selections.'),
        formula('clashes','Heavy-atom clashes',r'N_{clash}=\sum_{a\in A,b\in B}\mathbf1\{\|a-b\|<d_{cut}\}',
            'igem_drylab.structure_metrics.count_inter_module_clashes','Disjoint selections and explicitly reviewed cutoff; rigid-model clash alone requires review.'),
        formula('docking','Same-configuration docking difference',r'\Delta dock=score_{fusion}-score_{reference}',
            'igem_drylab.mcp.tools.scoring_docking_penalty','Same ligand identity and configuration; never converted to Kd, kcat or activity.'),
        formula('nominal','Confirmed assembly nominal site counts',r'n_{SH3}^{nom}=24m,\quad n_{PDZ}^{nom}=24n',
            'igem_drylab.scoring.m2_site_geometry.analyse_site_cooccupancy','Only confirmed applicable FTH1 24-mer with concrete sites; counts withheld otherwise.'),
        formula('occupancy','Conflict graph occupancy constraint',r'z_i\in\{0,1\},\quad z_i+z_j\le1\quad\forall(i,j)\in E(G)',
            'igem_drylab.scoring.m2_site_geometry.analyse_site_cooccupancy','Separate species-specific ranges/Pareto combinations, not one multiplier for both enzymes.'),
        formula('confidence','Folded-region confidence gate',r'g=\begin{cases}\text{high}&pLDDT>70\\\text{reference only}&50\le pLDDT\le70\\\text{blocked}&pLDDT<50\end{cases}',
            'igem_drylab.scoring.m2_structure.score_m2_structure','Registered pLDDT, not the PDB B-factor by assumption.'),
        formula('veto','High-confidence numerical risk rules',r'RMSD_C>4\ \mathring A\quad\text{or}\quad\eta_{SASA}<0.70',
            'igem_drylab.scoring.m2_structure.score_m2_structure','Only high-confidence folded domains. Persistent severe direct pocket occlusion also requires reviewed independent conformations.')],
    symbols={'C,P':'Mapped core and manually reviewed pocket residue sets','x,y':'Model/reference Cα coordinates (Å)','R,t':'Recorded Kabsch rotation (1), translation (Å)',
        'SASA':'Solvent-accessible area (Å²)','d_cut':'Reviewed heavy-atom cutoff (Å)','m,n':'Actual sites per scaffold subunit (1)',
        'G,z_i':'Concrete conflict graph; binary occupation (1)','pLDDT':'Source-registered confidence (0–100)'},
    tools=['ColabFold / AlphaFold2 / ESMFold','FreeSASA','AutoDock Vina','Kabsch / contact scripts','IUPred2A','Mpipi / CALVADOS','Site mixed-integer optimizer'],
    discrepancies=['No composite geometry score, no docking-to-kinetics multiplier. Whole-graph independent-set fraction is not assigned to both species.'])

M3 = MethodDefinition(id='m3-s1-e10',version='m3-s1-e10-2026-09-27',title='M3 — original S1–S5 / E1–E10',
    scope='Conservative cytosolic two-phase finite-site equilibrium. ER uses a different explicit version.',
    source_reference='docs/m3_s1_e10_implementation_contract.md',source_version='2026-09-27, original specification §6 and appendix C',
    steps=steps([(f'S{i}',title,title) for i,title in enumerate(['Effective sites','Excluded volume','Dense capacity','Scaffold lever rule','Affinity preference'],1)]+
        [(f'E{i}',title,title) for i,title in enumerate(['Langmuir occupancy','OC conservation','DMT conservation','Dense total enzyme','Bound fraction of whole-cell total',
            'Dense OC:DMT ratio','Regime-conditional ratio candidates','Low-occupancy target site ratio','Saturation target site ratio','Normalized sensitivities'],1)]),
    formulas=[
        formula('S1','Effective sites',r'n_{SH3}^{eff}=s_{SH3}\eta_{acc,SH3}\eta_{bind,SH3},\quad n_{PDZ}^{eff}=s_{PDZ}\eta_{acc,PDZ}\eta_{bind,PDZ}',M3_FUNCTION,'Scaffold monomer/assembly basis must match c_dense; no implicit factor 24.'),
        formula('S2','Excluded volume',r'f_{occ}=N_Ac_{dense}V_{scaffold}',M3_FUNCTION,'With µM and nm³ inputs the implementation applies the explicit 10⁻³⁰ unit factor.'),
        formula('S3','Dense capacity',r'c_{max}^{dense}=\frac{1-f_{occ}}{N_AV_{enzyme}}',M3_FUNCTION,'Declared single effective enzyme-volume approximation; matching volume and amount units.'),
        formula('S4','Scaffold lever rule',r'\Phi=\frac{c_S^{tot}-c_{sat}}{c_{dense}-c_{sat}}',M3_FUNCTION,'Measured phi may be supplied instead; no invented phase concentrations.'),
        formula('S5','Affinity preference',r'B=\frac{Kd_{SH3}}{Kd_{PDZ}}',M3_FUNCTION,'Matched binding-pair affinities, not docking scores.'),
        formula('E1','Occupancy',r'\theta_{SH3}=\frac{x}{Kd_{SH3}+x},\quad\theta_{PDZ}=\frac{y}{Kd_{PDZ}+y}',M3_FUNCTION,'M2 joint geometry must permit independent-site treatment.'),
        formula('E2','OC conservation',r'c_{OC}^{tot}=\Phi[x+\theta_{SH3}n_{SH3}^{eff}c_{dense}]+(1-\Phi)\frac{x}{K_{OC}}',M3_FUNCTION),
        formula('E3','DMT conservation',r'c_{DMT}^{tot}=\Phi[y+\theta_{PDZ}n_{PDZ}^{eff}c_{dense}]+(1-\Phi)\frac{y}{K_{DMT}}',M3_FUNCTION),
        formula('E4','Dense totals',r'c_{OC}^{dense}=x+\theta_{SH3}n_{SH3}^{eff}c_{dense},\quad c_{DMT}^{dense}=y+\theta_{PDZ}n_{PDZ}^{eff}c_{dense}',M3_FUNCTION),
        formula('E5','Bound fractions, not whole dense fractions',r'f_{OC}=\frac{\Phi\theta_{SH3}n_{SH3}^{eff}c_{dense}}{c_{OC}^{tot}},\quad f_{DMT}=\frac{\Phi\theta_{PDZ}n_{PDZ}^{eff}c_{dense}}{c_{DMT}^{tot}}',M3_FUNCTION,'Dense free enzyme is excluded from these original E5 numerators.'),
        formula('E6','Dense concentration ratio',r'R_{dense}=\frac{c_{OC}^{dense}}{c_{DMT}^{dense}}',M3_FUNCTION,'Undefined when the denominator is zero; never substituted with zero.'),
        formula('E7','Original low-occupancy candidates',r'R_{dense}=\rho E_{ratio}\frac{Kd_{PDZ}}{Kd_{SH3}},\quad\frac{x}{y}=E_{ratio}\frac{\Phi+(1-\Phi)/K_{DMT}}{\Phi+(1-\Phi)/K_{OC}}',M3_FUNCTION,
            'Source candidates only: low occupancy and binding-dominated regime, with appropriate free-ratio approximation; not full-range equalities.',status='conditional'),
        formula('E8','Low-occupancy target site ratio',r'\rho^*=\frac{r_{target}}{E_{ratio}}\frac{Kd_{SH3}}{Kd_{PDZ}}',M3_FUNCTION,'Only when the target is explicitly supplied and the regime is applicable.',status='conditional'),
        formula('E9','Saturation target site ratio',r'\theta\to1:\ R_{dense}=\rho,\quad\rho^*=r_{target}',M3_FUNCTION,'Binding-dominated saturation candidate, not a universal optimum.',status='conditional'),
        formula('E10','Normalized sensitivity',r'S_p=\frac{p}{R_{dense}}\frac{\partial R_{dense}}{\partial p}',
            'igem_drylab.m3_equilibrium._normalized_sensitivities','Implicit conservative derivatives; separate OC/DMT totals, no mRNA-derived E_ratio substitute.'),
        formula('dense-interface','Additional dense fraction interface',r'f_{dense,e}=\frac{\Phi c_e^{dense}}{c_e^{tot}}',M3_FUNCTION,'Explicit derived interface; does not replace E5.'),
        formula('avidity','Reviewed avidity correction',r'Kd^{eff}=Kd/v\ \text{or}\ \alpha Kd,\quad\alpha=\exp\left(\frac{\Delta\Delta G}{RT}\right)',
            'igem_drylab.m3_equilibrium','Explicit supported correction mode and matching measured/calibrated evidence required.',status='conditional'),
        formula('capacity','Capacity consistency gate',r'c_{OC}^{dense}+c_{DMT}^{dense}\le c_{max}^{dense}',M3_FUNCTION,
            'Source proportional compression would violate E2/E3. The implementation reports capacity_conflict without rescaling.',status='source_discrepancy')],
    symbols={'c,x,y,Kd':'Concentrations in µM; x/y are free dense enzyme','K_OC,K_DMT':'Free enzyme dense/dilute partition coefficients (1)',
        'Phi,theta,eta,f':'Volume/occupancy/accessibility/geometry/amount fractions (1)','s,n':'Declared and effective site counts (1)',
        'V_scaffold,V_enzyme':'Geometric volumes (nm³), explicitly converted','N_A':'Avogadro constant (mol⁻¹)',
        'rho':'Effective SH3/PDZ site ratio (1)','E_ratio':'OC/DMT total concentration ratio (1)','R,T,DeltaDeltaG':'Gas constant, absolute temperature and matched molar-energy units'},
    tools=['SciPy brentq','M2 site geometry','Reviewed SPR / binding evidence','Registered geometric volumes'],
    discrepancies=['Original capacity compression is not a conservative postprocessing operation. E7/E9 source equal signs are regime-conditional candidates, not asserted exact equalities.'])

M4 = MethodDefinition(id='m4-step0-step8',version='m4-step0-step8-2026-09-27',title='M4 — original ten-reaction Step 0–8',
    scope='Original two-phase competitive steady-state method; time-course amount and phase-activity extensions retain separate versions.',
    source_reference='docs/m4_step0_step8_implementation_contract.md',source_version='2026-09-27, original specification §7 and appendix D',
    steps=steps([(str(i),title,description) for i,title,description in [
        (0,'Canonical R1–R10 network','R10 is M14→M15 by OC; identities are checked.'),(1,'Parameter admission','Actual source, identity, condition, unit and approval; missing values stay missing.'),
        (2,'Enzyme recruitment','Actual M3 dense/dilute concentrations, not E5 bound fractions.'),(3,'Metabolite partition','All Kp8–15 from applicable evidence.'),
        (4,'Competitive rates','Competition among substrates sharing the same enzyme, separately in each phase.'),(5,'Eight steady balances','Required outlets, nonnegative root and every declared residual tolerance.'),
        (6,'Raw readouts','Absolute/relative yield and secretion loss with matched baseline.'),(7,'Sensitivity and uncertainty','Real distributions for LHS; Spearman is not a derivative; calibrated descriptor mapping required.'),
        (8,'Built scaffold scan','Only explicit constructed candidates and parameter mappings; no invented scan outputs.')]]),
    formulas=[
        formula('enzyme','Conservative enzyme phase interface',r'C_E^{tot}=\phi C_E^{dense}+(1-\phi)C_E^{dilute},\quad C_E^{dense}=\frac{f_EC_E^{tot}}{\phi},\quad C_E^{dilute}=\frac{(1-f_E)C_E^{tot}}{1-\phi}',M4_FUNCTION,'f_E is entire dense fraction, not M3 E5 bound fraction; phi=0 uses a separate single-phase path.'),
        formula('effective-partition','Effective enzyme partition',r'K_E^{eff}=\frac{f_E}{1-f_E}\frac{1-\phi}{\phi}',M4_FUNCTION,'Only for a defined two-phase ratio.'),
        formula('metabolite','Original lever expression',r'C_i^{dilute}=\frac{C_i^{tot}}{\phi Kp_i+1-\phi},\quad C_i^{dense}=Kp_iC_i^{dilute}',
            'igem_drylab.full_network.phase_partition','No Kp=1 substitute for missing biological inputs.'),
        formula('rates','Original same-enzyme competition',r'v_r^p=\frac{kcat_rC_E^pC_{S_r}^p/Km_r}{1+\sum_{r^\prime\in R(E)}C_{S_{r^\prime}}^p/Km_{r^\prime}}',
            'igem_drylab.full_network.phase_competitive_rates','PTR: 8/12; PT: 9/13; OC: 10/14; DMT: 8/9/10/11. No unreviewed activity multiplier in the original version.'),
        formula('dmt-denominator','DMT competition denominator',r'D_{DMT}^p=1+\frac{C_8^p}{Km_{R4}}+\frac{C_9^p}{Km_{R5}}+\frac{C_{10}^p}{Km_{R6}}+\frac{C_{11}^p}{Km_{R7}}',M4_FUNCTION),
        formula('flux','Volume-weighted reaction flux',r'V_r^{tot}=\phi v_r^{dense}+(1-\phi)v_r^{dilute}',M4_FUNCTION),
        formula('secretion','Original unweighted dilute secretion',r'V_{sec,i}=k_{sec,i}C_i^{dilute}',M4_FUNCTION,'Original normalization retained; does not silently insert 1−phi.'),
        *[formula('balance-'+str(i),'M'+str(i)+' steady balance',latex,M4_FUNCTION,'Positive input requires a reachable actual outlet.') for i,latex in [
            (8,r'0=V_{in}-V_{R1}^{tot}-V_{R4}^{tot}-V_{sec,8}'),(9,r'0=V_{R1}^{tot}-V_{R2}^{tot}-V_{R5}^{tot}-V_{sec,9}'),
            (10,r'0=V_{R2}^{tot}-V_{R3}^{tot}-V_{R6}^{tot}-V_{sec,10}'),(11,r'0=V_{R3}^{tot}-V_{R7}^{tot}-V_{sec,11}'),
            (12,r'0=V_{R4}^{tot}-V_{R8}^{tot}-V_{sec,12}'),(13,r'0=V_{R5}^{tot}+V_{R8}^{tot}-V_{R9}^{tot}-V_{sec,13}'),
            (14,r'0=V_{R6}^{tot}+V_{R9}^{tot}-V_{R10}^{tot}-V_{sec,14}'),(15,r'0=V_{R7}^{tot}+V_{R10}^{tot}-V_{sec,15}')]],
        formula('readouts','Original yield and loss',r'Y_{abs}=\frac{V_{R7}^{tot}+V_{R10}^{tot}}{V_{in}},\quad Y_{rel}=\frac{Y_{abs}}{Y_{abs}(H0)},\quad loss=\frac{\sum_{i=8}^{14}V_{sec,i}}{V_{in}}',
            'igem_drylab.m4_steady_state.solve_m4_steady_state','Relative yield needs independently run condition-matched H0.'),
        formula('invariant','Conditional steady invariant',r'Y_{abs}+loss=1',M4_FUNCTION,'Only single M8 input, actual steady pools and no omitted outlet.'),
        formula('robustness','LHS robustness',r'robustness=\frac{1}{\sigma_{LHS}(Y_{abs})}','igem_drylab.design_analysis','Requires actual justified distributions and declared sampling settings; no manufactured error bars.',status='conditional'),
        formula('spearman','Rank correlation',r'\rho_i=corr_{rank}(Kp_i,Y_{abs})','igem_drylab.design_analysis','Correlation, not dY/dKp.',status='conditional'),
        formula('local','Local numerical derivative',r'\frac{\partial Y}{\partial Kp_i}\approx\frac{Y(Kp_i+\delta)-Y(Kp_i)}{\delta}','igem_drylab.design_analysis','Source suggested 1% is a numerical step, not measured uncertainty.',status='conditional'),
        formula('chain','Descriptor chain sensitivity',r'\frac{dY}{d\theta}=\sum_i\frac{\partial Y}{\partial Kp_i}\frac{\partial Kp_i}{\partial\theta}',
            'igem_drylab.design_analysis','Requires calibrated applicability-matched descriptor mapping.',status='conditional'),
        formula('mapping','Original descriptor mapping',r'\ln Kp_i=a\log P_i+b\theta_{hydro}+c\,n_{aro,i}\theta_{aro}+const',
            'igem_drylab.design_analysis','a,b,c,const must have reviewed calibration; logP is not Kp.',status='conditional'),
        formula('mapping-derivatives','Descriptor mapping derivatives',r'\frac{\partial Kp_i}{\partial\theta_{hydro}}=bKp_i,\quad\frac{\partial Kp_i}{\partial\theta_{aro}}=c\,n_{aro,i}Kp_i',
            'igem_drylab.design_analysis','Same calibrated mapping, not invented coefficients.',status='conditional'),
        formula('scan','Source design-space scan',r'sh3/pdz\in\{1,2,3,4,6\},\quad achievable=\max_{\text{candidate IDR}}\frac{Kp_{14}}{Kp_9}',
            'igem_drylab.m4_workflow','Source proposed design space; only actual supplied constructs may be evaluated.',status='conditional')],
    symbols={'C':'Concentrations in µM, explicit phase/entity basis','kcat,k_sec':'Rates (h⁻¹)','Km':'Substrate concentration (µM)',
        'v,V,V_in':'Phase rates, volume-weighted and input concentration fluxes (µM h⁻¹)','phi,f_E,Kp':'Volume fraction, whole dense enzyme fraction, partition coefficient (1)',
        'Y,loss,robustness,rho':'Dimensionless readouts; rank correlation not a derivative','delta':'Numerical Kp step (1)',
        'theta,a,b,c,const':'Explicit descriptor and calibrated coefficient definitions from the selected source'},
    tools=['Competitive MM kernel','SciPy least_squares','LHS / Spearman analysis','Reviewed M3 output'],
    discrepancies=['Source OC prose mentioned M11 for R10; canonical R10 consumes M14.',
        'Source PTR/PT dilute=tot needs concentration-basis clarification; implementation consumes explicit actual phase concentrations.',
        'Original k_sec normalization is unresolved and preserved, not silently volume-weighted.'])

ER = MethodDefinition(id='er-amount-v1',version='ER-explicit-2026-10-10',title='ER — membrane geometry and amount-model extension',
    scope='Separate reviewed extension: explicit topology/body side, conformer/site identity, exact joint binding states and actual pool volumes. Not original cytosolic S1–E10.',
    source_reference='docs/scientific_model_contract.md',source_version='2026-10-10 explicit membrane/ER amount contracts',
    steps=steps([('M1','Anchor identity','Declared anchor retention/truncation, actual predictor topology and fusion sequence.'),
        ('M2','Membrane geometry','Actual frame, body side, tether endpoints, anchor/subunit composition and source-linked conformers.'),
        ('M3','Joint recruitment','Species/ligand/domain identity from actual M2; exact independent-set partition, explicit state budget.'),
        ('M4','Pool-aware kinetics','Amount/volume conversion, declared reaction locations, boundaries and rapid or finite exchange.'),
        ('stability','Steady compatibility and stability','Actual initial conserved class, numerical residual gate and local Jacobian analysis.')]),
    formulas=[formula('membrane','Recorded membrane clearance',r'\min_a[\sigma\hat n\cdot(r_a-o)-r_a^{radius}-d/2]\ge0',
            'igem_drylab.membrane_geometry.calculate_membrane_geometry','Recorded body side determines sigma; unknown side/confidence stays conditional.'),
        formula('tether','Declared tether contour bound',r'\|r_{body,CA}-r_{anchor,CA}\|\le\ell_{contour}',
            'igem_drylab.membrane_geometry.calculate_membrane_geometry','Actual mapped anchor/attachment Cα; necessary static feasibility, not flexibility probability.'),
        formula('partition','Exact independent-set binding partition',r'Z=\sum_{I\in Ind(G)}\prod_{i\in I}\frac{c_{species(i)}^{free}}{Kd_i},\quad\langle n_e\rangle=\frac{\partial\ln Z}{\partial\ln c_e^{free}}',
            'igem_drylab.m3_er.binding_partition','Exact, source-linked concrete conflict graph; state-budget exhaustion blocks instead of approximating.'),
        formula('conversion','Actual pool amount to concentration',r'C_{i,p}=\frac{N_{i,p}}{V_p}',
            'igem_drylab.m4_compartments.compartment_evaluator','N in µmol, V in L gives C in µM. Real volume required.'),
        formula('amount','Pool amount balances',r'\dot N_{i,p}=V_p\sum_r\nu_{ir}v_{r,p}+J_{i,p}^{exchange}+F_{i,p}-L_{i,p}',
            'igem_drylab.m4_compartments.compartment_evaluator','Actual reaction locations, enzyme amounts/activity and declared boundaries; not a scalar cytosolic adapter.'),
        formula('exchange','Finite exchange',r'J_{a\to b,i}=g_i\left(\frac{N_{i,a}}{V_a}-\frac{N_{i,b}}{V_bK_{b/a,i}}\right)',
            'igem_drylab.m4_compartments.compartment_evaluator','Conductance in L/h and actual partition in declared direction; opposite pool amount changes sum to zero.'),
        formula('rapid','Declared rapid equilibrium',r'C_{i,b}=K_{b/a,i}C_{i,a},\quad N_i^{tot}=\sum_pV_pC_{i,p}',
            'igem_drylab.m4_compartments.compartment_evaluator','Explicit applicability evidence, consistent acyclic interfaces; no missing-rate substitution.'),
        formula('compatibility','Conserved initial amount class',r'L^TN^*=L^TN_0,\quad L^TS=0',
            'igem_drylab.m4_compartments.conserved_amount_basis','Actual invariant basis also checks boundary terms; a root with small RHS in another class is rejected.'),
        formula('stability','Local linearized stability',r'J=\frac{\partial\dot N}{\partial N},\quad\max\Re\lambda(J)<-\epsilon_\lambda',
            'igem_drylab.m4_compartments.solve_compartment_network','Declared numerical tolerance. Conserved directions can produce neutral eigenvalues; no global or experimental stability claim.')],
    symbols={'r,o,ell,d':'Coordinates, recorded origin, tether contour length, membrane thickness (Å)','sigma,n_hat':'Declared side sign and unit normal (1)',
        'c,Kd':'Free concentration and matched site affinity (µM)','Z,G':'Partition function (1), actual conflict graph',
        'N,V,C':'Amount (µmol), actual pool volume (L), concentration (µM)','g,K':'Exchange conductance (L/h), directed partition (1)',
        'J,lambda,epsilon_lambda':'Jacobian and eigenvalue numerical tolerance (h⁻¹)','S,L':'Actual stoichiometry and conserved-class basis'},
    tools=['Registered membrane frame/topology','Exact binding partition','SciPy amount ODE / root / Jacobian'],
    discrepancies=['ER is a separately versioned extension; no ER advantage multiplier or invented membrane volume.'])

METHODS = {method.id:method for method in (M1,M2,M3,M4,ER)}


def method_for_tool(tool_id):
    return {'project.m1':M1,'project.m2':M2,'project.m3':M3,'project.m4':M4,
        'fusion.sequence_metrics':M1}.get(tool_id)
