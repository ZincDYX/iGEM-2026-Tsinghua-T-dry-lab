"""Data-backed figures and derived contrasts; never edit source observations."""
from pathlib import Path
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,TwoSlopeNorm,Normalize

ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
DATA=ROOT/'figure_data';DATA.mkdir(exist_ok=True)
COL={'no_LLPS':'#8A9EB1','cytosolic_LLPS':'#9D92B3','ER_anchored_LLPS':'#648F97'}
LABEL={'no_LLPS':'Free enzymes','cytosolic_LLPS':'Cytosolic LLPS','ER_anchored_LLPS':'ER-near LLPS (hypothesis)'}
SCENARIOS=list(COL)
CMAP=LinearSegmentedColormap.from_list('muted_diverging',['#819EB5','#FAF9F7','#A28CA8'])
SEQ=LinearSegmentedColormap.from_list('muted_sequential',['#FAF9F7','#B9BACB','#7C7297'])
plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.titlesize':10,'axes.labelsize':9,
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'xtick.direction':'out','ytick.direction':'out',
    'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'legend.frameon':False,'pdf.fonttype':42,'svg.fonttype':'none'})
PROVENANCE=[]
def read(name):return pd.read_csv(ROOT/name)
def table(name,data):data.to_csv(DATA/(name+'.csv'),index=False,encoding='utf-8-sig')
def export(fig,name,sources):
    for ext in ('png','svg','pdf'):fig.savefig(FIG/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
    plt.close(fig);PROVENANCE.append({'figure':name,'source_files':sources,'script':'scripts/plot_results.py',
        'formats':['png','svg','pdf'],'data_class':'measured' if name.startswith(('F06','F07')) else 'conditional_simulation_or_historical_audit'})
def panel(ax,text):ax.text(-.16,1.04,text,transform=ax.transAxes,fontweight='bold',fontsize=12,va='bottom')

def contrasts(frame,groupcols):
    rows=[]
    for key,group in frame.groupby(groupcols,dropna=False,sort=False):
        if not isinstance(key,tuple):key=(key,)
        lookup={r.scenario:r for r in group.itertuples()}
        free,cyto,er=[lookup[s].x15_120h_umol for s in SCENARIOS]
        rows.append({**dict(zip(groupcols,key)),'free_x15_120h_umol':free,'cyto_x15_120h_umol':cyto,'ER_x15_120h_umol':er,
            'LLPS_over_free_120h':cyto/free,'ER_over_cyto_120h':er/cyto,'LLPS_minus_free_umol':cyto-free,'ER_minus_cyto_umol':er-cyto})
    return pd.DataFrame(rows)

def main():
    historical=read('historical_scenarios.csv');matched=read('matched_summary.csv');scan=read('sensitivity.csv');ablations=read('ablations.csv')
    config=['scan_family','oc_total','dmt_total','phi','kd_factor','kp_factor','sh3','er_direct_g','reservoir_fraction','er_partition_x10','cyto_exchange_g','reservoir_bulk_g']
    paired=contrasts(scan,config);paired.to_csv(ROOT/'sensitivity_contrasts.csv',index=False,encoding='utf-8-sig')
    ab=contrasts(ablations,['ablation']);ab['display_label']=ab.ablation.replace({'no_recruitment':'No OC recruitment (PDZ retained)',
        'no_reservoir_substrate':'No initial reservoir substrate','no_direct_ER_exchange':'No direct ER exchange',
        'fast_bulk_access':'Fast reservoir–bulk exchange','fast_all_common_exchange':'Fast common exchange'})
    ab.to_csv(ROOT/'ablation_contrasts.csv',index=False,encoding='utf-8-sig')
    matchcontrast=contrasts(matched,['oc_total','dmt_total']);matchcontrast.to_csv(ROOT/'matched_contrasts.csv',index=False,encoding='utf-8-sig')
    table('F01_historical_confounds',historical)
    fig,axes=plt.subplots(1,3,figsize=(10,3.2),gridspec_kw={'width_ratios':[1,1,2]},layout='constrained')
    axes[0].bar(historical.scenario,historical.oc_total_uM,color='#9D92B3');axes[0].set(ylabel='OC or DMT total (µM)',title='Enzyme abundance')
    axes[1].bar(historical.scenario,historical.phi,color='#8A9EB1');axes[1].set(ylabel='Dense-phase volume fraction φ',title='Phase volume')
    values=np.log10(historical[['activity_R3','activity_R6','activity_R7','activity_R10']].to_numpy().T)
    im=axes[2].imshow(values,cmap=CMAP,norm=TwoSlopeNorm(vmin=-5,vcenter=0,vmax=1),aspect='auto')
    axes[2].set(xticks=range(5),xticklabels=historical.scenario,yticks=range(4),yticklabels=['R3','R6','R7','R10'],title='Historical effective-activity calibration')
    for i in range(4):
        for j in range(5):axes[2].text(j,i,f'{10**values[i,j]:.2g}',ha='center',va='center',fontsize=8)
    fig.colorbar(im,ax=axes[2],label=r'$\log_{10}$ (activity multiplier)',shrink=.9)
    for ax,l in zip(axes,'ABC'):panel(ax,l)
    export(fig,'F01_historical_scenarios_are_not_matched',['historical_scenarios.csv'])

    fig,axes=plt.subplots(2,4,figsize=(11.5,5.4),sharex=True,layout='constrained')
    for row,bg in enumerate(('low','high')):
        for s in SCENARIOS:
            curve=read('curves/'+bg+'_'+s+'.csv');table('F02_'+bg+'_'+s,curve)
            for col,(species,title) in enumerate([('10','Input compound 10'),('11','Intermediate 11'),('14','Competing-route intermediate 14'),('15','Target compound 15')]):
                ax=axes[row,col];ax.plot(curve.time_h,curve['x'+species+'_umol'],color=COL[s],label=LABEL[s],lw=1.8)
                if row==0:ax.set_title(title)
                if row==1:ax.set_xlabel('Time (h)')
                if col==0:ax.set_ylabel(('0.10' if row==0 else '1.20')+' µM each enzyme\nAmount (µmol / reference)')
        for col,ax in enumerate(axes[row]):panel(ax,chr(65+row*4+col));ax.set_xlim(0,240);ax.set_ylim(bottom=0)
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc='outside lower center',ncol=3)
    export(fig,'F02_matched_timecourses',['matched_summary.csv','curves/low_*.csv','curves/high_*.csv'])

    fig,axes=plt.subplots(1,3,figsize=(10.8,3.1),layout='constrained')
    llps=matched[matched.scenario=='cytosolic_LLPS'];x=np.arange(2)
    axes[0].bar(x-.16,llps.oc_bound_fraction,width=.3,color='#9D92B3',label='OC');axes[0].bar(x+.16,llps.dmt_bound_fraction,width=.3,color='#8A9EB1',label='DMT')
    axes[0].set(xticks=x,xticklabels=['0.10 µM','1.20 µM'],ylim=(0,1),ylabel='Bound fraction of each enzyme',xlabel='Equal OC and DMT totals',title='Recruitment is finite');axes[0].legend()
    val=scan[(scan.scan_family=='OC_sites')&(scan.oc_total==.1)&(scan.scenario=='cytosolic_LLPS')].sort_values('sh3');table('F03_site_response',val)
    axes[1].plot(val.sh3,val.oc_bound_fraction,'o-',color='#9D92B3',label='OC bound fraction')
    axes[1].plot(val.sh3,val.OC_fraction_of_dense_OC_DMT,'s-',color='#648F97',label='OC share of dense OC+DMT')
    axes[1].set(xlabel='SH3 sites per scaffold (PDZ = 1)',ylabel='Fraction',ylim=(0,1),title='Sites do not set enzyme stoichiometry');axes[1].legend(fontsize=7)
    for s in ('cytosolic_LLPS','ER_anchored_LLPS'):
        selected=scan[(scan.scan_family=='OC_sites')&(scan.oc_total==.1)&(scan.scenario==s)].sort_values('sh3')
        axes[2].plot(selected.sh3,selected.x15_120h_umol,'o-',color=COL[s],label=LABEL[s])
    axes[2].set(xlabel='SH3 sites per scaffold (PDZ = 1)',ylabel='Target at 120 h (µmol / reference)',title='The design ranking depends on access');axes[2].legend(fontsize=7)
    for ax,l in zip(axes,'ABC'):panel(ax,l)
    export(fig,'F03_recruitment_and_site_ratio',['matched_summary.csv','sensitivity.csv','figure_data/F03_site_response.csv'])

    def heat(ax,subset,x,y,metric,title,xlabel,ylabel,cmap=CMAP,limits=None):
        grid=subset.pivot(index=y,columns=x,values=metric).sort_index().sort_index(axis=1)
        arr=grid.to_numpy();norm=TwoSlopeNorm(vmin=limits[0],vcenter=1,vmax=limits[1]) if limits else Normalize(vmin=min(1.,arr.min()),vmax=arr.max())
        image=ax.imshow(arr,origin='lower',aspect='auto',cmap=cmap,norm=norm)
        ax.set(xticks=range(len(grid.columns)),xticklabels=[f'{v:g}' for v in grid.columns],yticks=range(len(grid.index)),yticklabels=[f'{v:g}' for v in grid.index],title=title,xlabel=xlabel,ylabel=ylabel)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):ax.text(j,i,f'{arr[i,j]:.2f}',ha='center',va='center',fontsize=8)
        fig.colorbar(image,ax=ax,label='Target amount ratio at 120 h',shrink=.85)
    fig,axes=plt.subplots(1,3,figsize=(11.4,3.5),layout='constrained')
    grid=paired[paired.scan_family=='Kd_Kp'];table('F04_Kd_Kp',grid)
    heat(axes[0],grid,'kp_factor','kd_factor','LLPS_over_free_120h','Cytosolic LLPS / free','Metabolite Kp multiplier','Both binding Kd multipliers',limits=(.5,1.5))
    heat(axes[1],grid,'kp_factor','kd_factor','ER_over_cyto_120h','ER-near / cytosolic LLPS','Metabolite Kp multiplier','Both binding Kd multipliers',cmap=SEQ)
    grid2=paired[paired.scan_family=='OC_sites'].copy();grid2['OC_DMT_total_ratio']=grid2.oc_total/grid2.dmt_total;table('F04_OC_sites',grid2)
    heat(axes[2],grid2,'sh3','OC_DMT_total_ratio','LLPS_over_free_120h','Cytosolic LLPS / matched free','SH3 sites (PDZ = 1)','Total OC:DMT ratio',limits=(.5,1.5))
    for ax,l in zip(axes,'ABC'):panel(ax,l)
    export(fig,'F04_parameter_sensitivity',['sensitivity.csv','sensitivity_contrasts.csv','figure_data/F04_*.csv'])

    fig,axes=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
    ermap=paired[paired.scan_family=='ER_benefit'];table('F05_ER_benefit',ermap)
    heat(axes[0],ermap,'reservoir_fraction','er_direct_g','ER_over_cyto_120h','ER substrate-access hypothesis','Initial substrate fraction in reservoir','Direct conductance (L/h)',cmap=SEQ)
    axes[0].set_xticklabels(['0','0.2','0.5','0.8','1']);axes[0].set_yticklabels(['0',r'$10^{-4}$',r'$10^{-3}$',r'$10^{-2}$',r'$10^{-1}$'])
    names=['no_direct_ER_exchange','fast_bulk_access','fast_all_common_exchange'];selected=ab.set_index('ablation').loc[names]
    axes[1].barh(np.arange(3),100*(selected.ER_over_cyto_120h-1),color='#648F97')
    axes[1].set(yticks=np.arange(3),yticklabels=['Direct route off','Fast reservoir–bulk','Fast common exchange'],xlabel='ER-near change over cytosolic LLPS (%)',title='The advantage vanishes without a bottleneck');axes[1].axvline(0,color='#777',lw=.7)
    for i,v in enumerate(100*(selected.ER_over_cyto_120h-1)):axes[1].text(v+.1,i,f'{v:.4g}%',va='center',fontsize=8)
    for ax,l in zip(axes,'AB'):panel(ax,l)
    export(fig,'F05_ER_benefit_and_ablations',['sensitivity_contrasts.csv','ablation_contrasts.csv'])

    obs=read('LC_observations.csv');summary=read('LC_summary.csv')
    groups=['normal','normal_llps','normal_er_llps','high_llps','high_er_llps'];short=['Normal\nfree','Normal\nLLPS','Normal\nER–LLPS','High\nLLPS','High\nER–LLPS']
    groupcolors=['#8A9EB1','#9D92B3','#648F97','#B1A1B5','#7E9D99']
    fig,axes=plt.subplots(2,2,figsize=(10.5,6.4),layout='constrained')
    for row,t in enumerate(('D3','D5')):
        for col,analyte in enumerate(('Gla','PreG')):
            ax=axes[row,col]
            for i,g in enumerate(groups):
                records=obs[(obs.group==g)&(obs.time_label==t)&(obs.analyte==analyte)].sort_values('record_index_within_cell')
                sm=summary[(summary.group==g)&(summary.time_label==t)&(summary.analyte==analyte)].iloc[0]
                ax.errorbar(i,sm['mean'],yerr=sm.sample_sd,fmt='_',ms=16,capsize=4,color=groupcolors[i],lw=1.3,zorder=2)
                for j,r in enumerate(records.itertuples()):
                    ax.scatter(i+(j-1)*.13,r.value,s=27,marker='D' if r.peak_shift_flag else 'o',facecolors='white' if r.peak_shift_flag else groupcolors[i],edgecolors=groupcolors[i],lw=1,zorder=3,clip_on=False)
            ax.set(xticks=range(5),xticklabels=short,ylabel=analyte+' sample concentration (µg/mL)',title=t+' · '+analyte,ylim=(0,None));panel(ax,chr(65+row*2+col))
    fig.legend(handles=[plt.Line2D([],[],marker='o',color='#8A9EB1',ls='',label='Unflagged record'),plt.Line2D([],[],marker='D',mfc='white',color='#8A9EB1',ls='',label='Peak-shift record (source *)'),plt.Line2D([],[],marker='_',ms=14,color='#777',ls='',label='Mean ± sample SD')],loc='outside lower center',ncol=3)
    table('F06_measured_records',obs);table('F06_summary',summary)
    export(fig,'F06_LC_individual_records',['LC_observations.csv','LC_summary.csv'])

    fig,axes=plt.subplots(1,3,figsize=(10.8,3.2),layout='constrained')
    held=read('LC_D7_heldout.csv');table('F07_D7_heldout',held)
    for ax,analyte in zip(axes[:2],('Gla','PreG')):
        subset=summary[(summary.group=='normal')&(summary.analyte==analyte)].set_index('time_label').loc[['D3','D5','D7']]
        ax.errorbar([3,5,7],subset['mean'],yerr=subset.sample_sd,fmt='o-',capsize=3,color='#8A9EB1',label='Observed mean ± SD')
        result=held[held.analyte==analyte].iloc[0]
        ax.plot([5,7],[subset.loc['D5','mean'],result.D7_linear_extension_from_D3_D5],'--',color='#9D92B3',label='Early-interval extension')
        ax.set(xlabel='Culture day (provisional D interpretation)',ylabel=analyte+' (µg/mL)',title='Normal free control · '+analyte,xticks=[3,5,7],ylim=(0,None))
    axes[0].legend(fontsize=7)
    for i,g in enumerate(('normal','low_legacy','normal_legacy')):
        sub=obs[(obs.group==g)&(obs.time_label=='D7')&(obs.analyte=='Gla')]
        axes[2].scatter(i+np.linspace(-.1,.1,len(sub)),sub.value,color=groupcolors[i],s=25)
    axes[2].set(xticks=range(3),xticklabels=['Main\nnormal','CEN\nlow','CEN\nold normal'],yscale='log',ylabel='D7 Gla (µg/mL)',title='Legacy controls remain separate')
    for ax,l in zip(axes,'ABC'):panel(ax,l)
    export(fig,'F07_D7_extrapolation_and_legacy_controls',['LC_observations.csv','LC_summary.csv','LC_D7_heldout.csv'])

    geo=read('ER_geometry_recheck.csv');table('F08_saved_geometry',geo)
    fig,axes=plt.subplots(1,2,figsize=(9.5,3.2),layout='constrained')
    x=np.arange(len(geo));labels=[f'{r.product_id.split("_")[0]}\n#{i%5+1}' for i,r in enumerate(geo.itertuples())]
    colors=['#9D92B3' if p=='Q10_P02' else '#8A9EB1' for p in geo.product_id]
    axes[0].bar(x,geo.common_interval_gap_A,color=colors);axes[0].set(ylabel='Saved-coordinate plane gap (Å)',title='No common membrane plane in rigid copies')
    axes[1].scatter(x,geo.max_reach_contour_ratio,c=colors,s=30);axes[1].axhline(1,ls='--',color='#777',lw=.8)
    axes[1].set(ylabel='Maximum reach / contour length',title='A contour bound is not a linker ensemble',ylim=(0,1.05))
    for ax,l in zip(axes,'AB'):ax.set_xticks(x,labels);panel(ax,l)
    export(fig,'F08_ER_static_geometry_limits',['ER_geometry_recheck.csv','inputs/ER_static_audit.json'])

    phi=paired[paired.scan_family=='phi'].sort_values('phi');table('F09_phi_response',phi)
    dose=scan[(scan.scan_family=='OC_sites')&(scan.sh3==3)]
    fig,axes=plt.subplots(1,2,figsize=(8.8,3.1),layout='constrained')
    axes[0].plot(phi.phi,phi.LLPS_over_free_120h,'o-',color='#9D92B3',label='Cytosolic LLPS / free')
    axes[0].plot(phi.phi,phi.ER_over_cyto_120h,'s-',color='#648F97',label='ER-near / cytosolic LLPS')
    axes[0].set(xlabel='φ (fixed scaffold total; lever rule retained)',ylabel='Target amount ratio at 120 h',title='Volume fraction alone is not ER targeting');axes[0].legend(fontsize=7)
    for s in SCENARIOS:
        subset=dose[dose.scenario==s].sort_values('oc_total');axes[1].plot(subset.oc_total/.1,subset.x15_120h_umol,'o-',c=COL[s],label=LABEL[s])
    axes[1].set(xlabel='Total OC:DMT ratio (DMT = 0.10 µM)',ylabel='Target at 120 h (µmol / reference)',title='OC dosage response under stated assumptions')
    for ax,l in zip(axes,'AB'):panel(ax,l)
    export(fig,'F09_phi_and_OC_dose',['sensitivity.csv','sensitivity_contrasts.csv'])

    metrics={'matched':matchcontrast.to_dict('records'),
        'scan_ratio_ranges':{family:{metric:{'min':float(sub[metric].min()),'max':float(sub[metric].max())} for metric in ['LLPS_over_free_120h','ER_over_cyto_120h']} for family,sub in paired.groupby('scan_family')},
        'LLPS_beneficial_cases_at_120h':int((paired.LLPS_over_free_120h>1).sum()),'paired_scan_settings':len(paired),
        'ablations':ab.to_dict('records'),'scope':'Ratios are model outputs, not wet-lab titer changes or statistical significance.'}
    (ROOT/'derived_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'figure_provenance.json').write_text(json.dumps(PROVENANCE,indent=2),encoding='utf8')
    print(json.dumps({'figure_sets':len(PROVENANCE),'formats_each':3,'paired_settings':len(paired),'LLPS_beneficial_settings':metrics['LLPS_beneficial_cases_at_120h']},indent=2))

if __name__=='__main__':main()
