"""validation host actual FreeSASA/MCP smoke, explicitly not fusion biological evidence."""
import asyncio
import argparse
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from igem_drylab.external_tools import audit_deployment
from igem_drylab.parsers.freesasa import parse_freesasa_json


async def main(run_name,root,pdb,tool_config,roots):
    root.mkdir(parents=True,exist_ok=True)
    if not run_name.replace("-","").isalnum():
        raise ValueError("run_name_must_be_single_alphanumeric_directory")
    output = root/run_name
    if output.exists():
        raise RuntimeError('preserve_prior_smoke_use_new_output_path')
    params = StdioServerParameters(command=sys.executable,args=['-m','igem_drylab.mcp.server'],cwd=Path.cwd())
    async with Client(params,read_timeout_seconds=60) as client:
        response = await client.call_tool('igem.compute.run_tool', {
            'config_path':str(tool_config),
            'tool_name':'freesasa','output_dir':str(output),'dry_run':False,'timeout_seconds':60,
            'context':{'pdb_file':str(pdb),'input_files':{'structure':str(pdb)},
                       'expected_outputs':{'freesasa':str(output/'freesasa.json')}}})
        if response.is_error:
            raise RuntimeError(str(response))
        result = response.structured_content
        if result['run']['status']!='succeeded' or result['run']['return_code']!=0:
            raise RuntimeError('actual_FreeSASA_job_failed')
    raw = (output/'freesasa.json').read_bytes()
    parsed = json.loads(raw)
    areas = parse_freesasa_json(output/'freesasa.json')
    if not parsed or not areas:
        raise RuntimeError('actual_FreeSASA_output_empty')
    audit = audit_deployment(roots)
    if not audit.within_budget:
        raise RuntimeError('external_deployment_exceeds_15GB')
    summary = {'scope':'real_external_tool_smoke_not_project_fusion_ORF_or_biological_validation',
        'input_pdb_sha256':sha256(pdb.read_bytes()).hexdigest(),'output_sha256':sha256(raw).hexdigest(),
        'FreeSASA_python_version':version('freesasa'),'deployment_audit':audit.model_dump(),
        'production_parser_residue_count':len(areas),
        'execution':result,'this_smoke_installs_packages':False,
        'licensed_predictor_new_jobs':'not_executed_or_claimed'}
    (root/(run_name+'-evidence.json')).write_text(json.dumps(summary,indent=2,allow_nan=False))
    print(json.dumps({'actual_FreeSASA_MCP':'succeeded','used_bytes':audit.used_bytes,'within_15GB':audit.within_budget}))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name',default='actual-freesasa-mcp-final')
    parser.add_argument('--results-root',type=Path,required=True)
    parser.add_argument('--pdb',type=Path,required=True)
    parser.add_argument('--tool-config',type=Path,required=True)
    parser.add_argument('--deployment-root',type=Path,action='append',required=True)
    args=parser.parse_args()
    asyncio.run(main(args.run_name,args.results_root,args.pdb,args.tool_config,args.deployment_root))
