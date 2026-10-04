"""Read-only diagnostics: execute on air-lab, never a production correction."""
import argparse
import builtins
import copy
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import load_workbook
from scipy.optimize import curve_fit
arguments = argparse.ArgumentParser(description=__doc__)
arguments.add_argument('--sources', type=Path, default=Path('/mnt/data/dyx/glabridin-reproduction/raw'))
arguments.add_argument('--repository', type=Path, default=Path('/mnt/data/dyx/drylab-m1m4-runtime'))
arguments.add_argument('--compact', action='store_true')
args = arguments.parse_args()
sys.path.insert(0, str(args.repository / 'src'))
from igem_drylab.published_reference import load_author_native_parameters, run_published_reference

raw = args.sources.resolve()
root = args.repository.resolve()
spec = importlib.util.spec_from_file_location('author_readonly_diagnostic', raw / 'simulation-network-glabridin-final.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
original_open = builtins.open

def mapped_open(filename, *args, **kwargs):
    # Only translate the author's mismatched published filename, in memory.
    if str(filename) == str(raw / 'data.txt'):
        filename = raw / 'simulation-data.txt'
    return original_open(filename, *args, **kwargs)

builtins.open = mapped_open
try:
    native = author.DataLoader()
finally:
    builtins.open = original_open

values = load_author_native_parameters(raw / 'simulation-data.txt')
assert all(getattr(native, name) == value for name, value in values.items())
captured = {}
original_solver = author.solve_ivp

def capture_solver(*args, **kwargs):
    solved = original_solver(*args, **kwargs)
    captured['solution'] = solved
    captured['params'] = kwargs['args'][0]
    return solved

author.solve_ivp = capture_solver
native_arrays = np.asarray(author.one_step(native))
plt.close('all')
adapter = run_published_reference(root)
solved = captured['solution']
report = {
    'execution_environment': {'python': sys.version, 'platform': platform.platform(),
                              'numpy': np.__version__, 'scipy': __import__('scipy').__version__,
                              'source_directory': str(raw), 'repository': str(root)},
    'raw_md5': {name: hashlib.md5((raw / name).read_bytes()).hexdigest() for name in
                ['simulation-network-glabridin-final.py', 'simulation-data.txt', 'Source Data_V2.xlsx']},
    'author_DataLoader_vs_project_parser_all_parameters_equal': True,
    'author_one_step_vs_project_adapter_max_state_error': float(np.max(np.abs(solved.y-adapter.state))),
    'minimum_author_state': float(solved.y.min()),
}
idx = np.unravel_index(np.argmin(solved.y), solved.y.shape)
report['minimum_state_location'] = {'compound': int(8+idx[0]%8), 'pool': 'intracellular' if idx[0]<8 else 'extracellular', 'time_days': float(solved.t[idx[1]])}

wb = load_workbook(raw / 'Source Data_V2.xlsx', data_only=True, read_only=True)
find_sheet = lambda token: next(wb[name] for name in wb.sheetnames if name.replace(' ','').replace('.','') == token.replace(' ','').replace('.',''))
ws = find_sheet('Fig4h')
published = []
for row in list(ws.values)[3:]:
    try:
        converted = [float(v) for v in row[1:11]]
    except (ValueError, TypeError):
        continue
    published.append(converted)
published = np.asarray(published)
assert published.shape == (1000,10), published.shape
report['independent_author_loader_vs_Fig4h_max_concentration_error'] = float(np.max(np.abs(native_arrays.T[:,1:]-published[:,1:])))
tight = original_solver(author.reaction_kinetics, (0.,native.total_time), [7.4e-5]+[0.]*15,
                        args=(captured['params'],), t_eval=solved.t, method='LSODA', rtol=1e-8, atol=1e-12)
assert tight.success
report['independent_tighter_tolerance_minimum_state'] = float(tight.y.min())
report['independent_tighter_tolerance_final_product_relative_change_percent'] = float(
    100*((tight.y[7,-1]+tight.y[15,-1])/(solved.y[7,-1]+solved.y[15,-1])-1))

# Compare only the gating branch, using unchanged RHS and identical trial state.
trial = np.zeros(16)
trial[1:4] = 1e-5
gating = []
for t in [0., .5, 1., 2.]:
    rates = []
    for ratio in [0., -1.]:
        params = copy.deepcopy(captured['params'])
        params['disable_times'] = {i: ratio*native.total_time for i in range(4,8)}
        rhs = np.asarray(author.reaction_kinetics(t, trial, params))
        rates.append(rhs[5:8])  # In this trial state, these derivatives equal v5,v6,v7.
    gating.append({'time_days': t, 'zero_flag_over_negative_flag_DMT_flux': (rates[0]/rates[1]).tolist()})
report['gating_trial'] = gating

ws = find_sheet('Fig4f')
rows = list(ws.values)
transport = []
for col in range(1,7):
    numeric = [row[col] for row in rows[3:] if isinstance(row[col], (int,float))]
    compound = int(str(rows[2][col]).strip('() '))
    k = getattr(native, 'K'+str(compound))
    transport.append({'header_cell': ws.cell(3,col+1).coordinate, 'compound': compound,
                      'n': len(numeric), 'source_mean_percent': float(np.mean(numeric)),
                      'author_K_as_percent_equal_pool_basis': float(100*k/(1+k))})
report['transport'] = transport

rows = list(find_sheet('SupplementaryFig5').values)
paper_km = [32.78,46.54,17.38,186.53,41.68,42.37,30.23,14.27,33.82,21.17,13.814,23.33]
paper_km_error = [4.26,5.20,1.51,47.10,3.42,6.04,4.30,2.81,6.05,4.68,1.84,4.54]
fits = []
def mm(s,vmax,km):
    return vmax*s/(km+s)
def fit(x,y):
    return curve_fit(mm, np.asarray(x), np.asarray(y), p0=[max(y),max(x)/10], bounds=(0,np.inf), maxfev=20000,
                     ftol=1e-12,xtol=1e-12,gtol=1e-12)
for index,(header,end,col) in enumerate((h,e,c) for h,e in [(2,13),(16,27),(30,40),(43,52)] for c in [2,7,12]):
    x,ys = [],[]
    for row in rows[header+1:end]:
        if isinstance(row[col-1],(int,float)):
            assert all(isinstance(v,(int,float)) for v in row[col:col+3])
            x.append(row[col-1]);ys.append(row[col:col+3])
    x,ys = np.asarray(x),np.asarray(ys)
    point_params,point_cov = fit(x,ys.mean(axis=1))
    all_params,all_cov = fit(np.repeat(x,3),ys.ravel())
    replicate_params = np.asarray([fit(x,ys[:,i])[0] for i in range(3)])
    fits.append({'panel':chr(97+index),'source_unit':rows[header-1][col],
                 'paper_Km':paper_km[index], 'paper_plusminus_Km':paper_km_error[index],
                 'point_means_Km':float(point_params[1]), 'all_replicates_fit_SE_Km':float(np.sqrt(all_cov[1,1])),
                 'individual_replicate_Km':replicate_params[:,1].tolist(),
                 'replicate_fit_mean_Km':float(replicate_params[:,1].mean()),
                 'replicate_fit_SD_Km':float(replicate_params[:,1].std(ddof=1)),
                 'point_means_Vmax_native':float(point_params[0]),
                 'replicate_fit_mean_Vmax_native':float(replicate_params[:,0].mean()),
                 'replicate_fit_SD_Vmax_native':float(replicate_params[:,0].std(ddof=1))})
report['kinetic_method_diagnostic'] = fits
report['stored_numerical_diagnostics'] = json.loads((raw.parent/'results'/'solver_diagnostics.json').read_text())
wb.close()
if args.compact:
    report['kinetic_method_diagnostic'] = [f for f in fits if f['panel'] in ['a','d','f','g','i','j']]
print(json.dumps(report,ensure_ascii=False,indent=2))


