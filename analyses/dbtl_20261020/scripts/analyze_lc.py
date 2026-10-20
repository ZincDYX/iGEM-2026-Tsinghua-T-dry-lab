"""Independent read-only workbook parsing and descriptive measured-data feedback."""
from pathlib import Path
import os
from collections import defaultdict
import csv
import json
import statistics as stats
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
GROUPS={3:'normal',4:'normal_llps',5:'normal_er_llps',6:'high_llps',7:'high_er_llps',8:'low_legacy',9:'normal_legacy'}
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def save(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def out(name,rows):
    with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    if (ROOT/'LC_summary.csv').exists():raise ValueError('Do not overwrite a completed analysis')
    with zipfile.ZipFile(ROOT/'inputs/LC.xlsx') as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(t.text or '' for t in si.iterfind('.//s:t',NS)) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        data=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        cells={}
        for cell in data.findall('.//s:sheetData/s:row/s:c',NS):
            value=cell.find('s:v',NS);value=value.text if value is not None else None
            if cell.get('t')=='s':value=strings[int(value)]
            if cell.get('t')=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//s:t',NS))
            if cell.find('s:f',NS) is not None:raise ValueError('Unexpected source formula; do not execute it')
            if value is not None:cells[cell.attrib['r']]=value
        sheet=ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets',NS)[0].attrib['name']
    obs=[];missing=[]
    for row,group in GROUPS.items():
        for col in 'BCDEFG':
            address=col+str(row);token=cells.get(address)
            base={'group':group,'original_group':cells['A'+str(row)],'sheet':sheet,'source_cell':address,
                'time_label':{'B':'D3','C':'D3','D':'D5','E':'D5','F':'D7','G':'D7'}[col],
                'analyte':'Gla' if col in 'BDF' else 'PreG','unit':'ug/mL','data_class':'measured_sample_concentration'}
            if token is None or not token.strip():missing.append({**base,'status':'not_reported'});continue
            for i,item in enumerate(token.split('/'),1):
                obs.append({**base,'record_index_within_cell':i,'raw_token':item,'value':float(item.replace('*','').strip()),'peak_shift_flag':'*' in item})
    previous=list(csv.DictReader((ROOT/'inputs/LC_previous_observations.csv').open(encoding='utf-8-sig')))
    before={(r['source_cell'],int(r['replicate_index'])):(float(r['concentration_ug_ml']),r['peak_shift_flag'].lower()=='true') for r in previous}
    after={(r['source_cell'],r['record_index_within_cell']):(r['value'],r['peak_shift_flag']) for r in obs}
    assert before==after,'Independent workbook extraction disagrees with preserved previous data'
    out('LC_observations.csv',obs);out('LC_missing_cells.csv',missing)
    by=defaultdict(list)
    for r in obs:by[r['group'],r['time_label'],r['analyte']].append(r)
    summaries=[]
    for key,records in by.items():
        values=[r['value'] for r in records];unflagged=[r['value'] for r in records if not r['peak_shift_flag']]
        summaries.append({'group':key[0],'time_label':key[1],'analyte':key[2],'n_records':len(values),'unit':'ug/mL',
            'mean':stats.mean(values),'sample_sd':stats.stdev(values),'starred_records':sum(r['peak_shift_flag'] for r in records),
            'unflagged_n':len(unflagged),'unflagged_mean':stats.mean(unflagged) if unflagged else None})
    out('LC_summary.csv',summaries);index={(r['group'],r['time_label'],r['analyte']):r for r in summaries}
    comparisons=[]
    for time in ('D3','D5'):
        for analyte in ('Gla','PreG'):
            for first,second in [('normal_llps','normal'),('normal_er_llps','normal_llps'),('high_er_llps','high_llps'),('high_llps','normal_llps'),('high_er_llps','normal_er_llps')]:
                a,b=index[first,time,analyte],index[second,time,analyte]
                comparisons.append({'first':first,'reference':second,'time_label':time,'analyte':analyte,'unit':'ug/mL',
                    'mean_first':a['mean'],'mean_reference':b['mean'],'difference':a['mean']-b['mean'],
                    'ratio_of_means':a['mean']/b['mean'] if b['mean'] else None,
                    'SD_first':a['sample_sd'],'SD_reference':b['sample_sd'],'n_first':a['n_records'],'n_reference':b['n_records'],
                    'starred_first':a['starred_records'],'starred_reference':b['starred_records'],
                    'comparison_scope':'descriptive original workbook groups; promoter/construct IDs and repeat pairing unconfirmed'})
    out('LC_comparisons.csv',comparisons)
    rates=[]
    for group in list(GROUPS.values())[:5]:
        for analyte in ('Gla','PreG'):
            a,b=index[group,'D3',analyte],index[group,'D5',analyte]
            rates.append({'group':group,'analyte':analyte,'D3_mean':a['mean'],'D5_mean':b['mean'],
                'D3_to_D5_difference_ug_ml':b['mean']-a['mean'],'net_rate_ug_ml_per_day_assuming_D_is_culture_day':(b['mean']-a['mean'])/2,
                'time_interpretation':'provisional; source only labels D3/D5','repeat_pairing':'not established, unpaired interval means'})
    out('LC_interval_changes.csv',rates)
    held=[]
    for analyte in ('Gla','PreG'):
        a,b,c=[index['normal',t,analyte]['mean'] for t in ('D3','D5','D7')]
        predicted=b+(b-a);held.append({'group':'normal','analyte':analyte,'D7_observed':c,'D7_linear_extension_from_D3_D5':predicted,
            'error_ug_ml':predicted-c,'relative_error_pct':100*(predicted-c)/c if c else None,
            'early_net_change_per_day':(b-a)/2,'late_net_change_per_day':(c-b)/2,'unit':'ug/mL',
            'model':'observation-layer straight-line extension, NOT mechanistic M4 prediction'})
    out('LC_D7_heldout.csv',held)
    mapping=[{'original_group':cells['A'+str(row)],'group':group,
        'engineering_candidate_mapping':{'normal':'S59-free?','normal_llps':'S59-GAL-LG+LLPS?',
        'normal_er_llps':'S59-GAL-LG+ER-LLPS?','high_llps':'S59-TEF-LG+LLPS?',
        'high_er_llps':'S59-TEF-LG+ER-LLPS?','low_legacy':'CEN.PK2-1D low control','normal_legacy':'CEN.PK2-1D old-normal control'}[group],
        'status':'unconfirmed identity; do not assign actual Q IDs or protein fold-change',
        'needed':'wet-lab sample-to-strain/promoter/plasmid/sequence/induction map'} for row,group in GROUPS.items()]
    out('wetlab_group_mapping_pending.csv',mapping)
    save('LC_tests.json',{'status':'PASS','records':len(obs),'starred':sum(r['peak_shift_flag'] for r in obs),
        'missing_cells':len(missing),'source_groups':len(GROUPS),'independent_extraction_matches_previous':before==after,
        'star_definition':'Owner: peak-retention-time-shift data retained when other biological repeats were lost; not statistical significance',
        'record_count_not_independent_biological_replicate_certification':True,
        'unidentified_parameters':['Km','kcat','Kd','Kp','absolute OC/DMT abundance','phi','ER exchange','biomass-specific productivity'],
        'mechanistic_vs_measured_absolute_error':'NOT COMPUTED: normalization, uptake, identities, analyte definitions and sampling metadata do not match',
        'PreG_to_model_compound_ID':'not established by workbook; no forced mapping to x11 or x14',
        'source_zeros':'retained literal zeros, no LOD/LOQ assumption','D7_LLPS':'missing, not extrapolated as observations'})
    print(json.dumps({'status':'PASS','records':len(obs),'stars':sum(r['peak_shift_flag'] for r in obs),'missing_cells':len(missing)}))

if __name__=='__main__':main()
