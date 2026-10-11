"""Human/JSON CLI for the same durable application used by the Web workbench."""
from pathlib import Path
import json
import time
import typer
from .application import ApplicationService
from .web import default_workspace, serve_local

app=typer.Typer(help='FusionLab projects, approved workflows and local browser workspace.',no_args_is_help=True)
projects=typer.Typer(); workflows=typer.Typer(); jobs=typer.Typer(); results=typer.Typer()
app.add_typer(projects,name='project'); app.add_typer(workflows,name='workflow')
app.add_typer(jobs,name='jobs'); app.add_typer(results,name='results')


@app.callback()
def options(ctx: typer.Context,data_dir: Path=typer.Option(default_workspace(),'--data-dir'),
            json_output: bool=typer.Option(False,'--json')):
    ctx.obj={'data_dir':data_dir,'json':json_output}


def service(ctx):
    if 'application' not in ctx.obj: ctx.obj['application']=ApplicationService(ctx.obj['data_dir'])
    return ctx.obj['application']


def output(ctx,value):
    if hasattr(value,'model_dump'): value=value.model_dump(mode='json')
    if ctx.obj['json']: typer.echo(json.dumps(value,ensure_ascii=False,allow_nan=False)); return
    if isinstance(value,dict):
        for key in ('name','id','project_id','status','objective','rationale'):
            if key in value: typer.echo(f'{key.replace("_"," ").capitalize()}: {value[key]}')
        missing=value.get('missing',value.get('missing_inputs',[]))
        for item in missing:
            if isinstance(item,dict): typer.echo(f'Missing {item["field_path"]}: {item["source_kind"]}')
            else: typer.echo('Missing: '+str(item))
        if 'missing' in value and not missing: typer.echo('Declared inputs checked; final scientific gates still apply.')
        for item in value.get('items',[]):
            typer.echo(f"{item['filename']}: {item['detected_format']} / {item['semantic_type']}")
            for issue in item['issues']: typer.echo(f"{issue['severity'].capitalize()}: {issue['message']}"+(f" Field: {issue['field']}" if issue['field'] else ''))
        if value.get('state')=='preview': typer.echo('Import preview retained. Confirm roles with import-review, then publish using import-commit. No job has started.')
    else: typer.echo(str(value))


def execute(ctx,operation):
    try: return operation(service(ctx))
    except (ValueError,KeyError,OSError) as error:
        from igem_drylab.workflow.models import WorkflowError
        code=error.code if isinstance(error,WorkflowError) else 'invalid_or_missing_input'
        output(ctx,{'status':'blocked','missing_inputs':[code],'rationale':'Check the input field, file, project revision or approval. No calculation was silently substituted.'})
        raise typer.Exit(2)


@projects.command('create')
def create(ctx: typer.Context,name: str=typer.Option(...,'--name')):
    output(ctx,execute(ctx,lambda application:application.create_project(name)))


@app.command('import')
def import_files(ctx: typer.Context,paths: list[Path]=typer.Argument(...),project: str=typer.Option(...,'--project'),
                 input_kind: str=typer.Option('auto','--input-kind'),preview_only: bool=typer.Option(False,'--preview'),
                 into: str|None=typer.Option(None,'--into',help='Add missing files to an existing saved import; review before committing.')):
    files=[]
    for path in paths:
        if path.is_dir(): files.extend(sorted(p for p in path.rglob('*') if p.is_file()))
        else: files.append(path)
    preview=execute(ctx,lambda application:application.preview_files(project,files,input_kind,into))
    if preview_only or into:
        output(ctx,preview);return
    if any(item.duplicate_file_id or any(i.severity in {'error','confirmation'} for i in item.issues) for item in preview.items):
        output(ctx,preview);raise typer.Exit(2)
    output(ctx,execute(ctx,lambda application:application.imports.commit(project,preview.id)))


@app.command('import-review')
def review_import(ctx: typer.Context,transaction_id: str,project: str=typer.Option(...,'--project'),options: Path|None=typer.Option(None,'--options'),
                  filename: str|None=typer.Option(None,'--file'),molecule_type: str|None=typer.Option(None,'--molecule-type')):
    if bool(filename)!=bool(molecule_type): raise typer.BadParameter('Use --file and --molecule-type together.')
    selections=json.loads(options.read_text()) if options else {}
    if filename: selections[filename]={**selections.get(filename,{}),'molecule_type':molecule_type}
    value=execute(ctx,lambda application:application.imports.revise(project,transaction_id,selections)
        if selections else application.imports.inspect(project,transaction_id))
    output(ctx,value)


@app.command('import-commit')
def commit_import(ctx: typer.Context,transaction_id: str,project: str=typer.Option(...,'--project'),choices: Path|None=typer.Option(None,'--choices')):
    output(ctx,execute(ctx,lambda application:application.imports.commit(project,transaction_id,
        json.loads(choices.read_text()) if choices else {})))


@app.command('check-inputs')
def check(ctx: typer.Context,project: str=typer.Option(...,'--project'),through: str=typer.Option('M2','--through')):
    if through.lower() not in {'m1','m2','m3','m4','m5'}: raise typer.BadParameter('Choose M1 through M5.')
    value=execute(ctx,lambda application:application.check_inputs(project,through.lower()))
    output(ctx,value)
    if value['missing']: raise typer.Exit(2)


@app.command('plan')
def plan(ctx: typer.Context,project: str=typer.Option(...,'--project'),method: str=typer.Option('sequence-properties','--method')):
    output(ctx,execute(ctx,lambda application:application.plan(project,method)))


@workflows.command('inspect')
def inspect(ctx: typer.Context,plan_id: str):
    value=execute(ctx,lambda application:application.planning.get(plan_id))
    output(ctx,value)
    if not ctx.obj['json'] and value.workflow:
        for node in value.workflow.nodes: typer.echo(f'{node.label}: {node.tool_id}; requires {", ".join(sorted(node.dependencies())) or "project inputs"}')


@workflows.command('decide')
def decide(ctx: typer.Context,plan_id: str,accept: bool=typer.Option(False,'--accept'),reject: bool=typer.Option(False,'--reject')):
    if accept==reject: raise typer.BadParameter('Choose exactly one of --accept or --reject after inspecting the plan.')
    output(ctx,execute(ctx,lambda application:application.planning.decide(plan_id,'accept' if accept else 'reject')))


@workflows.command('run')
def run(ctx: typer.Context,approved_plan_id: str):
    value=execute(ctx,lambda application:application.run_approved(approved_plan_id))
    output(ctx,value)
    if value['status']!='succeeded': raise typer.Exit(3)


@jobs.command('watch')
def watch(ctx: typer.Context,run_id: str,interval: float=typer.Option(1.,min=.2,max=60.)):
    previous=None
    while True:
        value=execute(ctx,lambda application:application.boundary.run(application.store.run(run_id)))
        if value['status']!=previous: output(ctx,value); previous=value['status']
        if value['status'] in {'succeeded','failed','cancelled','paused','interrupted'}:
            if value['status'] in {'failed','interrupted'}: raise typer.Exit(3)
            return
        time.sleep(interval)


@results.command('export')
def export(ctx: typer.Context,run_id: str,format: str=typer.Option('json','--format'),
           destination: Path=typer.Option(...,'--output')):
    kinds=set(format.split(','))
    if kinds-{'json','csv'}: raise typer.BadParameter('Supported export formats: csv,json.')
    if destination.exists(): raise typer.BadParameter('Choose a new output directory; existing results are preserved.')
    application=service(ctx)
    value=execute(ctx,lambda application:application.boundary.run(application.store.run(run_id)))
    destination.mkdir(parents=True)
    if 'json' in kinds: (destination/'run.json').write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    if 'csv' in kinds:
        import csv
        with (destination/'nodes.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream);writer.writerow(['Node','Job status','Attempt','Scientific output (JSON; original precision)'])
            for node in value['nodes']: writer.writerow([node['id'],node['status'],node['attempts'],json.dumps(node.get('output'),ensure_ascii=False,allow_nan=False)])
    output(ctx,{'status':'exported','name':destination.name})


@app.command('serve')
def serve(ctx: typer.Context,open_browser: bool=typer.Option(False,'--open'),port: int=typer.Option(8780,'--port',min=0,max=65535)):
    try: serve_local(data_dir=ctx.obj['data_dir'],port=port,open_browser=open_browser)
    except (OSError,RuntimeError,ValueError) as error:
        typer.echo(str(error),err=True);raise typer.Exit(3)


if __name__=='__main__': app()
