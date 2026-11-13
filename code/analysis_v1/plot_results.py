from pathlib import Path
import argparse, sys
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--audit-root');args=a.parse_args()
out=P/'figures';out.mkdir(exist_ok=True)
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':7.5,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'legend.frameon':False,'xtick.labelsize':7,'ytick.labelsize':7})
d=pd.read_csv(P/'results/all_scenarios.csv');d=d[d.setting=='main']
b=pd.read_csv(P/'results/conditional_temporal_resampling.csv');b=b[b.metric=='disagreement_rate']
d.to_csv(out/'figure1_panel_a_source.csv',index=False);b.to_csv(out/'figure1_panel_b_source.csv',index=False)
fig=plt.figure(figsize=(180/25.4,82/25.4))
gs=fig.add_gridspec(1,2,left=.10,right=.96,bottom=.22,top=.84,wspace=.457142857)
ax1=fig.add_subplot(gs[0,0]);ax2=fig.add_subplot(gs[0,1])
reps=['A','B','B-G','B-Z'];colors=['#0072B2','#999999','#E69F00','#009E73'];grids=['case33bw.m','case69.m']
for j,(r,c) in enumerate(zip(reps,colors)):
 vals=[100*float(d[(d.feeder==f)&(d.representation==r)].iloc[0].voltage_violating_hours)/4344 for f in grids]
 ax1.bar(np.arange(2)+(j-1.5)*.17,vals,width=.16,color=c,label=r)
ax1.set(xticks=[0,1],xticklabels=['33-bus','69-bus'],ylim=(0,100),ylabel='Hours with voltage violations (%)')
ax1.legend(ncol=4,loc='lower left',bbox_to_anchor=(-.06,1.03),columnspacing=.8,handlelength=1,handletextpad=.3,borderaxespad=0,fontsize=7)
for i,(f,m,dy) in enumerate(zip(grids,['o','^'],[-.13,.13])):
 rows=b[b.feeder==f].set_index('alternative').loc[['B','B-G','B-Z']]
 x=100*rows.estimate.to_numpy();lo=100*rows.temporal_resampling_percentile_2p5.to_numpy();hi=100*rows.temporal_resampling_percentile_97p5.to_numpy()
 ax2.errorbar(x,np.arange(3)+dy,xerr=np.vstack([x-lo,hi-x]),fmt=m,ms=4,color=['#333333','#777777'][i],capsize=2,lw=.8,label=['33-bus','69-bus'][i])
ax2.set(yticks=[0,1,2],yticklabels=['A vs B','A vs B-G','A vs B-Z'],ylim=(2.5,-.5),xlim=(0,100),xlabel='Paired decision disagreement (%)')
ax2.legend(ncol=2,loc='lower left',bbox_to_anchor=(0,1.03),columnspacing=1,handletextpad=.4,borderaxespad=0,fontsize=7)
for ax,label in [(ax1,'a'),(ax2,'b')]:
 ax.text(-.20,1.13,label,transform=ax.transAxes,fontsize=9,fontweight='bold',va='top')
 ax.tick_params(direction='out',length=3,width=.6)
fig.canvas.draw()
if args.audit_root:
 sys.path.insert(0,args.audit_root)
 from audit_panel_alignment import require_matplotlib_panel_alignment
 require_matplotlib_panel_alignment(fig,json_out=str(P/'evidence/figure_alignment.json'),overlay_svg=str(P/'evidence/figure_alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
fig.savefig(out/'figure1_energy_matching.pdf')
fig.savefig(out/'figure1_energy_matching.svg')
fig.savefig(out/'figure1_energy_matching.png',dpi=600)
plt.close(fig)
(out/'figure1_caption.txt').write_text('Figure 1. Energy matching and voltage-decision disagreement in two test feeders. (a) Percentage of 4344 hourly cases with any node voltage below 0.95 or above 1.05 p.u. under four charging-energy representations: original A and B, globally energy-matched B-G, and zone-wise energy-matched B-Z. (b) Percentage of paired hours with different violation decisions between A and each alternative. Markers show full-record estimates; bars show 2.5th–97.5th percentiles from 2000 paired moving-block resamples (7-day blocks, seed 20261106). These are conditional temporal-resampling ranges, not population confidence intervals. Main settings: background multiplier 0.5, EV scaling anchor alpha 0.25, EV power factor 1, fixed synthetic zone-to-node mapping. Neither A nor B is measured energy ground truth.\n')
