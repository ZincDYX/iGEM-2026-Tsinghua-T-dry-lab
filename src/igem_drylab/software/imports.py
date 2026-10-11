"""Compatibility preview for old clients; semantic parsing uses one registry.

New Web/CLI imports use persisted project-scoped transactions. This endpoint
does not resolve an ambiguous molecule type without explicit confirmation.
"""
from hashlib import sha256
from pathlib import Path
from .parsers import ParserRegistry


def preview_import(data_dir,boundary,filename,content,input_kind='auto'):
    from igem_drylab.workflow.disclosure import check_import_content
    raw=content.encode('utf-8')
    check_import_content(filename,raw)
    boundary.check_bytes(raw)
    root=data_dir/'imports'
    root.mkdir(parents=True,exist_ok=True)
    source=root/(sha256(raw).hexdigest()+Path(filename).suffix.lower())
    source.write_bytes(raw)
    parsed=ParserRegistry().parse(source,{} if input_kind=='auto' else {'role':input_kind})
    file=boundary.asset(source,fresh=True,logical_name=filename)
    patch=parsed.patch
    kind={'SequenceCollection':'sequences','DesignRecord':'genbank_design',
        'MeasurementTable':'wetlab' if input_kind=='wetlab' else 'dataset',
        'ReactionModel':'pathway','UnclassifiedConfiguration':'configuration_display_only'}.get(parsed.semantic_type,parsed.semantic_type)
    if kind=='genbank_design':
        from igem_drylab.workflow.genbank_design import GenBankDesign
        records=parsed.records[0]
        patch['datasets']=[GenBankDesign(id=file['id'],file_id=file['id'],name=filename,
            records=records['records'],cds_proteins=records['cds_proteins']).model_dump(mode='json')]
    elif kind=='wetlab':
        from igem_drylab.wetlab import quality_control
        from igem_drylab.wetlab.models import WetLabResult
        qc=quality_control([WetLabResult.model_validate(r) for r in parsed.records])
        patch['datasets']=[{'id':file['id'],'file_id':file['id'],'name':filename,'kind':'wetlab',
            'records':parsed.records,'qc':[r.model_dump(mode='json') for r in qc]}]
    else:
        patch['datasets']=[{'id':file['id'],'file_id':file['id'],'name':filename,'kind':parsed.semantic_type,
            'supported_scope':parsed.supported_scope,'records':[],
            'unresolved_inputs':[i.model_dump(mode='json') for i in parsed.issues]}]
    result={'kind':kind,'file':file,'patch':patch}
    boundary.check(result)
    return result
