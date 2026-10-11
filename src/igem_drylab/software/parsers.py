"""Shared semantic parsers. Parsing never runs tools or approves evidence.

Original bytes remain assets. Coordinates retain author and label identifiers;
FASTA needs explicit molecule confirmation when the alphabet is ambiguous.
"""
from io import StringIO
from pathlib import Path
import csv
import json
import math
import re
from typing import Any, Literal

from pydantic import Field
from igem_drylab.workflow.models import Contract, SequenceRecord, WorkflowError


class ImportIssue(Contract):
    code: str
    message: str
    severity: Literal['error','warning','confirmation','info']
    field: str | None = None


class ParsedInput(Contract):
    detected_format: str
    semantic_type: str
    records: list[dict[str,Any]] = Field(default_factory=list)
    issues: list[ImportIssue] = Field(default_factory=list)
    proposed_links: list[dict[str,Any]] = Field(default_factory=list)
    supported_scope: str
    input_roles: list[str] = Field(default_factory=list)
    patch: dict[str,Any] = Field(default_factory=dict)


def issue(code,message,severity='confirmation',field=None):
    return ImportIssue(code=code,message=message,severity=severity,field=field)


class ParserRegistry:
    def __init__(self):
        self.parsers={}
        self.register(('.fa','.fasta','.faa','.fna'),self.fasta)
        self.register(('.gb','.gbk','.genbank'),self.genbank)
        self.register(('.pdb','.cif','.mmcif','.bcif'),self.structure)
        self.register(('.json','.yaml','.yml'),self.configuration)
        self.register(('.csv','.tsv'),self.table)
        self.register(('.sdf','.mol','.smi','.smiles'),self.compound)

    def register(self,extensions,parser):
        for extension in extensions:
            if extension in self.parsers: raise ValueError('duplicate_parser_extension')
            self.parsers[extension]=parser

    def parse(self,path,options=None):
        parser=self.parsers.get(path.suffix.lower())
        if parser: return parser(path,options or {})
        if path.suffix.lower() in {'.txt',''}:
            with path.open(encoding='utf-8-sig') as stream: prefix=stream.read(512).lstrip()
            if prefix.startswith('>'): return self.fasta(path,options or {})
            if prefix.startswith('LOCUS '): return self.genbank(path,options or {})
        # Content recognition is conservative: script extensions never get
        # interpreted as a program, even if their content resembles data.
        return ParsedInput(detected_format=path.suffix.lower().lstrip('.') or 'unknown',
            semantic_type='EvidenceAttachment',supported_scope='Original attachment only; not executable or scientific parameter evidence.',
            input_roles=['evidence_attachment'],issues=[issue('attachment_only','This format is retained as an attachment, not connected to M1–M4.', 'info')])

    def fasta(self,path,options):
        from Bio import SeqIO
        text=path.read_text(encoding='utf-8-sig')
        if not text.lstrip().startswith('>'): raise WorkflowError('invalid_fasta_content')
        raw=list(SeqIO.parse(StringIO(text),'fasta'))
        if not raw or len(raw)>100_000: raise WorkflowError('empty_or_oversized_sequence_collection')
        if len({r.id for r in raw})!=len(raw): raise WorkflowError('duplicate_sequence_id')
        declared=options.get('molecule_type')
        if declared not in {None,'protein','DNA','RNA'}: raise WorkflowError('invalid_molecule_type')
        if declared is None and path.suffix.lower()=='.faa': declared='protein'
        records=[];issues=[];proteins=[]
        protein=set('ACDEFGHIKLMNPQRSTVWYBXZJUO')
        dna=set('ACGTRYSWKMBDHVN');rna=set('ACGURYSWKMBDHVN')
        for row in raw:
            sequence=str(row.seq).upper()
            alphabet=set(sequence)
            candidates=[kind for kind,letters in (('DNA',dna),('RNA',rna),('protein',protein)) if alphabet and alphabet<=letters]
            if path.suffix.lower()=='.fna': candidates=[c for c in candidates if c!='protein']
            kind=declared or (candidates[0] if len(candidates)==1 else None)
            if kind is not None and kind not in candidates:
                raise WorkflowError('molecule_alphabet_conflicts_with_declared_type')
            if not candidates: raise WorkflowError('unsupported_sequence_alphabet')
            records.append({'id':row.id,'description':row.description,'sequence':sequence,'length':len(sequence),
                'molecule_type':kind,'possible_molecule_types':candidates,'role':options.get('role')})
            if kind=='protein': proteins.append(SequenceRecord(id=row.id,sequence=sequence).model_dump())
        if any(r['molecule_type'] is None for r in records):
            issues.append(issue('molecule_type_required','Confirm protein, DNA or RNA once for this file. No translation or protein screening is inferred.','confirmation','molecule_type'))
        return ParsedInput(detected_format='FASTA',semantic_type='SequenceCollection',records=records,issues=issues,
            supported_scope='Confirmed proteins can run sequence descriptors. Nucleic acids are retained without inferred translation.',
            input_roles=['protein_sequence','DNA_design','RNA_sequence'],patch={'sequences':proteins})

    def genbank(self,path,options):
        from igem_drylab.workflow.genbank_design import import_design
        summaries,bindings,proteins=import_design(path.read_text(encoding='utf-8-sig'))
        return ParsedInput(detected_format='GenBank',semantic_type='DesignRecord',
            records=[{'records':[r.model_dump(mode='json') for r in summaries],
                'cds_proteins':[r.model_dump(mode='json') for r in bindings]}],
            supported_scope='Original annotated DNA and CDS translations; locations/strand/qualifiers preserved. Missing translation is not inferred.',
            input_roles=['annotated_design'],patch={'sequences':[r.model_dump() for r in proteins]})

    def structure(self,path,options):
        from Bio.Data.IUPACData import protein_letters_3to1
        extension=path.suffix.lower()
        atoms=[]
        if extension=='.pdb':
            # Reuse the native model-scope parser. Import previews retain all
            # models/altlocs; scientific metrics still require explicit choice.
            from igem_drylab.structure_metrics import _read_atom_records
            for atom in _read_atom_records(path):
                atoms.append({'model':str(atom.model_id),'auth_chain':atom.chain,'label_chain':None,
                    'auth_number':str(atom.residue),'label_number':None,'insertion':atom.insertion,
                    'residue_name':atom.residue_name,'atom_name':atom.name,'altloc':atom.altloc,
                    'is_hetero':atom.is_hetero,'x':float(atom.coordinate[0]),'y':float(atom.coordinate[1]),'z':float(atom.coordinate[2])})
        else:
            from Bio.PDB.MMCIF2Dict import MMCIF2Dict
            from igem_drylab.workflow.bcif_display import binary_atom_columns
            columns=binary_atom_columns(path,200_000) if extension=='.bcif' else MMCIF2Dict(str(path))
            fields={key[11:]:value for key,value in columns.items() if key.startswith('_atom_site.')}
            count=len(fields.get('Cartn_x',[]))
            if not count or count>200_000 or any(len(v)!=count for v in fields.values()): raise WorkflowError('invalid_structure_source')
            def at(name,i,fallback=None):
                values=fields.get(name)
                value=values[i] if values else fallback
                return None if value in {'.','?'} else value
            for i in range(count):
                atoms.append({'model':at('pdbx_PDB_model_num',i,'1'),'auth_chain':at('auth_asym_id',i),
                    'label_chain':at('label_asym_id',i),'auth_number':at('auth_seq_id',i),'label_number':at('label_seq_id',i),
                    'insertion':at('pdbx_PDB_ins_code',i,''),'residue_name':at('auth_comp_id',i,at('label_comp_id',i)),
                    'atom_name':at('auth_atom_id',i,at('label_atom_id',i)),
                    'altloc':at('label_alt_id',i,''),'is_hetero':at('group_PDB',i)=='HETATM',
                    'x':float(at('Cartn_x',i)),'y':float(at('Cartn_y',i)),'z':float(at('Cartn_z',i))})
        if not atoms or len(atoms)>200_000 or any(not math.isfinite(a[k]) for a in atoms for k in ('x','y','z')):
            raise WorkflowError('invalid_structure_source')
        residues={};chains={}
        for atom in atoms:
            key=tuple(atom[k] for k in ('model','auth_chain','label_chain','auth_number','label_number','insertion'))
            if key not in residues:
                residues[key]={k:v for k,v in atom.items() if k not in {'x','y','z','atom_name'}}
                chain_key=(atom['model'],atom['auth_chain'],atom['label_chain'])
                # Water/ligand residues are retained but not converted into
                # imaginary amino acids in an exact sequence-match proposal.
                amino=protein_letters_3to1.get(atom['residue_name'].title())
                if not atom['is_hetero'] or amino:
                    chains.setdefault(chain_key,[]).append(amino or 'X')
        records=[{'model':key[0],'auth_chain':key[1],'label_chain':key[2],
            'coordinate_sequence':''.join(sequence),'sequence_scope':'observed residues only; missing residues not inferred'} for key,sequence in chains.items()]
        return ParsedInput(detected_format='BCIF' if extension=='.bcif' else 'mmCIF' if extension!='.pdb' else 'PDB',
            semantic_type='StructureRecord',records=[{'chains':records,'atom_count':len(atoms),'residue_count':len(residues),
                'residue_identity_preview':list(residues.values())[:20],'coordinate_preview':atoms[:5],
                'full_coordinates':'original asset','role':options.get('role'),'confidence_semantics':None}],
            issues=[issue('structure_mapping_required','Import a matched sequence/residue mapping and pocket annotation before formal M2. Coordinates alone do not identify an enzyme or confidence.','warning')],
            supported_scope='Parsed coordinates and model/chain identities; original auth/label numbering retained. No inferred pLDDT, pocket or OC/DMT role.',
            input_roles=['reference_structure','fusion_structure','assembly_structure'])

    def configuration(self,path,options):
        import yaml
        raw=json.loads(path.read_text(encoding='utf-8-sig')) if path.suffix.lower()=='.json' else yaml.safe_load(path.read_bytes())
        schema=raw.get('schema_version') if isinstance(raw,dict) else None
        kind=options.get('role')
        if kind=='evidence_attachment':
            return ParsedInput(detected_format='JSON' if path.suffix.lower()=='.json' else 'YAML',semantic_type='EvidenceAttachment',
                records=[{'value':raw}],supported_scope='Parsed attachment only; not a model or scientific parameter.',input_roles=['evidence_attachment'])
        if kind in {'analysis_plan','project_config','parameter_set'} and not isinstance(raw,dict):
            raise WorkflowError('configuration_requires_object')
        if schema=='analysis-plan-v1' or kind=='analysis_plan':
            from igem_drylab.workflow.models import Workflow
            workflow=Workflow.model_validate(raw.get('workflow',raw))
            return ParsedInput(detected_format='JSON' if path.suffix.lower()=='.json' else 'YAML',semantic_type='AnalysisPlan',
                records=[workflow.model_dump(mode='json')],supported_scope='Typed DAG candidate; tools, dependencies and approval checked before execution.',input_roles=['analysis_plan'])
        if schema=='parameter-set-v1' or kind=='parameter_set':
            from igem_drylab.parameters import ParameterRecord
            records=[ParameterRecord.model_validate(row).model_dump(mode='json') for row in raw['records']]
            # Uploaded review claims are not permission. Keep original in the
            # asset and require the existing scientific review flow.
            for record in records: record.update(review_status='extracted',approved_by=None)
            return ParsedInput(detected_format='JSON' if path.suffix.lower()=='.json' else 'YAML',semantic_type='ParameterSet',
                records=records,supported_scope='Typed candidate parameters; units/conditions/source retained, not approved by import.',input_roles=['parameter_set'])
        if schema=='project-config-v1' or kind=='project_config':
            config=raw.get('config',raw)
            if not isinstance(config,dict) or config.get('tools'):
                raise WorkflowError('runtime_settings_not_scientific_input')
            return ParsedInput(detected_format='JSON' if path.suffix.lower()=='.json' else 'YAML',semantic_type='ProjectConfig',
                records=[config],supported_scope='Scientific configuration candidate; same-transaction paths, sources and approvals require binding checks.',input_roles=['project_config'])
        if kind in {'wetlab','pathway'}:
            # No generic JSON is silently promoted to a measurement/pathway.
            if kind=='wetlab':
                from igem_drylab.wetlab.models import WetLabResult
                rows=raw.get('records') if isinstance(raw,dict) else raw
                if not isinstance(rows,list) or not rows: raise WorkflowError('wetlab_requires_nonempty_typed_records')
                records=[WetLabResult.model_validate(r).model_dump(mode='json') for r in rows]
                return ParsedInput(detected_format='JSON',semantic_type='MeasurementTable',records=records,
                    supported_scope='Typed original measurements; quality/applicability still checked.',input_roles=['wetlab'])
            from igem_drylab.workflow.pathway import Pathway
            pathway=Pathway.model_validate(raw)
            return ParsedInput(detected_format='JSON',semantic_type='ReactionModel',records=[pathway.model_dump(mode='json')],
                patch={'pathway':pathway.model_dump(mode='json')},supported_scope='Typed user reaction pathway; not the original ten-reaction method.',input_roles=['pathway'])
        return ParsedInput(detected_format='JSON' if path.suffix.lower()=='.json' else 'YAML',semantic_type='UnclassifiedConfiguration',
            records=[{'value':raw}],issues=[issue('configuration_role_required','Choose the schema/role. Unknown JSON/YAML is not a scientific configuration or approved parameter set.','confirmation','role')],
            supported_scope='Parsed tree only; no values filled or computation authorized.',input_roles=['analysis_plan','project_config','parameter_set','wetlab','pathway','evidence_attachment'])

    def table(self,path,options):
        with path.open(encoding='utf-8-sig',newline='') as source:
            reader=csv.DictReader(source,delimiter='\t' if path.suffix.lower()=='.tsv' else ',')
            columns=reader.fieldnames
            if not columns or len(columns)>128 or len(set(columns))!=len(columns) or any(not c for c in columns):
                raise WorkflowError('table_columns_missing_or_duplicate')
            preview=[];count=0;types={c:set() for c in columns}
            for row in reader:
                if None in row or any(v is None for v in row.values()) or count>=100_000:
                    raise WorkflowError('table_row_budget_or_shape_invalid')
                if count<10: preview.append(row)
                for column,value in row.items():
                    if not value.strip(): types[column].add('missing');continue
                    try:
                        number=float(value)
                        types[column].add('number' if math.isfinite(number) else 'nonfinite')
                    except ValueError: types[column].add('text')
                count+=1
        if not count: raise WorkflowError('empty_table')
        if options.get('role')=='evidence_attachment':
            return ParsedInput(detected_format='TSV' if path.suffix.lower()=='.tsv' else 'CSV',semantic_type='EvidenceAttachment',
                records=[{'columns':columns,'row_count':count,'row_preview':preview,'full_table':'original asset; all rows parsed'}],
                supported_scope='Parsed table attachment only; not a measurement or approved parameter.',input_roles=['evidence_attachment'])
        mapping=options.get('column_mapping',{})
        if any(column not in columns for column in mapping): raise WorkflowError('unknown_measurement_column')
        for specification in mapping.values():
            if not isinstance(specification,dict) or specification.get('role') not in {'time','value','unit','condition','replicate','censoring','construct','source','ignore'}:
                raise WorkflowError('column_mapping_role_required')
        issues=[]
        for column,specification in mapping.items():
            if specification['role'] in {'time','value'}:
                if not specification.get('unit') and not any(s['role']=='unit' for s in mapping.values()):
                    issues.append(issue('measurement_unit_required','Declare the unit for this measured column. Missing units are not supplied by software.','confirmation',column))
                if 'nonfinite' in types[column]:
                    issues.append(issue('nonfinite_measurement_value','Nonfinite values cannot become numerical evidence. Correct the source or explicitly define censoring/missing data.','error',column))
        return ParsedInput(detected_format='TSV' if path.suffix.lower()=='.tsv' else 'CSV',semantic_type='MeasurementTable' if mapping else 'UnmappedTable',
            records=[{'columns':[{'name':c,'observed_types':sorted(types[c]),'mapping':mapping.get(c),
                'header_unit':(re.search(r'\(([^()]+)\)\s*$',c).group(1) if re.search(r'\(([^()]+)\)\s*$',c) else None)} for c in columns],
                'row_count':count,'row_preview':preview,'full_table':'original asset; all rows parsed'}],
            issues=issues if mapping else [issue('column_mapping_required','Map value/unit, condition, replicate and censoring columns before use as measurements. Header units are suggestions, not inferred evidence.','confirmation','column_mapping')],
            supported_scope='Complete shape/type parse and explicit column metadata; not a fitted or approved parameter.',input_roles=['measurement_table','parameter_table','evidence_attachment'])

    def compound(self,path,options):
        try: from rdkit import Chem
        except ImportError:
            return ParsedInput(detected_format=path.suffix.lstrip('.').upper(),semantic_type='CompoundAttachment',
                supported_scope='Original chemical file retained; chemistry parser unavailable in this runtime.',input_roles=['substrate_compound'],
                issues=[issue('chemistry_runtime_unavailable','RDKit is not installed in the selected chemistry profile. Chemical identity/stereochemistry have not been parsed.','warning')])
        extension=path.suffix.lower()
        if extension=='.sdf': molecules=list(Chem.SDMolSupplier(str(path),removeHs=False))
        elif extension=='.mol': molecules=[Chem.MolFromMolFile(str(path),removeHs=False)]
        else: molecules=[Chem.MolFromSmiles(line.split()[0]) for line in path.read_text().splitlines() if line.strip()]
        if not molecules or len(molecules)>10_000 or any(m is None for m in molecules): raise WorkflowError('invalid_chemical_identity')
        identity=options.get('compound_identity');source=options.get('source_reference')
        assigned=isinstance(identity,str) and bool(identity.strip()) and isinstance(source,str) and bool(source.strip())
        return ParsedInput(detected_format=extension.lstrip('.').upper(),semantic_type='CompoundRecord',
            records=[{'name':m.GetProp('_Name') if m.HasProp('_Name') else None,
                'canonical_isomeric_smiles':Chem.MolToSmiles(m,isomericSmiles=True),'atom_count':m.GetNumAtoms(),
                'declared_compound_identity':identity if assigned else None,'source_reference':source if assigned else None,
                'binding_status':'declared_identity_not_scientific_approval' if assigned else 'unassigned_substrate_identity'} for m in molecules],
            issues=[] if assigned else [issue('substrate_identity_confirmation_required','Assign the intended substrate identity and provenance. Do not infer a paper compound from the filename.','confirmation','role')],
            supported_scope='Parsed chemical identity/stereochemistry; docking preparation is a separate real tool job.',input_roles=['substrate_compound'])
