from pathlib import Path
import argparse,sys
import numpy as np,pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

P=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--audit-root');args=ap.parse_args()
if args.audit_root:
 sys.path.insert(0,args.audit_root)
 from audit_panel_alignment import require_matplotlib_panel_alignment
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'none','legend.frameon':False})
F=P/'figures';F.mkdir(exist_ok=True)
cols={'B':'#777777','B-G':'#CE8A30','B-Z':'#007F73'}
maps=pd.read_csv(P/'evidence/v1_1_all_mapping_paired_comparisons.csv')
points=maps[maps.alternative.isin(['B-G','B-Z'])].copy()
assert len(points)==80 and points.valid_pairs.eq(4344).all() and points.unresolved_pairs.eq(0).all()
points.to_csv(F/'Figure1_source.csv',index=False)
fig=plt.figure(figsize=(180/25.4,85/25.4))
gs=fig.add_gridspec(1,2,left=.09,right=.98,bottom=.23,top=.81,wspace=.18)
axes=[fig.add_subplot(gs[0,i]) for i in range(2)]
for ax,f,letter,title in zip(axes,['case33bw.m','case69.m'],['a','b'],['33-bus feeder','69-bus feeder']):
 for rep,marker,offset in [('B-G','o',-.13),('B-Z','^',.13)]:
  g=points[(points.feeder==f)&(points.alternative==rep)].sort_values('mapping_id')
  assert g.mapping_id.tolist()==list(range(1,21))
  ax.scatter(g.mapping_id.to_numpy()+offset,100*g.disagreement_rate_lower.to_numpy(),s=18,marker=marker,color=cols[rep],linewidths=.35,edgecolors='white',zorder=3,label=rep)
 ax.axhline(0,color='#BBBBBB',lw=.6,zorder=1)
 ax.set(xlim=(.3,20.7),ylim=(-1.1,40),xticks=[1,5,10,15,20],yticks=[0,10,20,30,40],xlabel='Mapping ID',title=title)
 ax.tick_params(direction='out',length=3,width=.6)
 ax.text(-.16,1.14,letter,transform=ax.transAxes,fontsize=10,fontweight='bold',va='top')
axes[0].set_ylabel('Paired disagreement (%)')
handles=[Line2D([],[],marker=m,color=cols[r],linestyle='None',markersize=4,label='A vs '+r) for r,m in [('B-G','o'),('B-Z','^')]]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.56,.99),ncol=2,handletextpad=.4,columnspacing=2)
fig.canvas.draw()
if args.audit_root:
 require_matplotlib_panel_alignment(fig,json_out=str(P/'evidence/Figure1_alignment.json'),overlay_svg=str(P/'evidence/Figure1_alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,require_panel_labels=True,strict=True)
fig.savefig(F/'Figure1_mapping.pdf')
fig.savefig(F/'Figure1_mapping.svg')
fig.savefig(F/'Figure1_mapping.png',dpi=600)
fig.savefig(F/'Figure1_mapping.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
plt.close(fig)

b=pd.read_csv(P/'evidence/v1_conditional_temporal_resampling.csv');b=b[b.metric=='disagreement_rate'].copy()
assert len(b)==6 and b.draws.eq(2000).all() and b.block_days.eq(7).all()
b.to_csv(F/'FigureS1_source.csv',index=False)
fig,ax=plt.subplots(figsize=(180/25.4,70/25.4))
fig.subplots_adjust(left=.19,right=.97,bottom=.25,top=.83)
for j,rep in enumerate(['B','B-G','B-Z']):
 for f,marker,dy in [('case33bw.m','o',-.13),('case69.m','s',.13)]:
  r=b[(b.feeder==f)&(b.alternative==rep)].iloc[0]
  x=100*r.estimate;lo=100*r.temporal_resampling_percentile_2p5;hi=100*r.temporal_resampling_percentile_97p5
  assert lo<=x<=hi
  ax.errorbar(x,j+dy,xerr=[[x-lo],[hi-x]],fmt=marker,ms=4,color=cols[rep],capsize=2,lw=.9)
ax.set(yticks=[0,1,2],yticklabels=['A vs B','A vs B-G','A vs B-Z'],ylim=(2.5,-.5),xlim=(0,100),xticks=[0,20,40,60,80,100],xlabel='Paired disagreement (%)')
ax.tick_params(direction='out',length=3,width=.6)
ax.legend(handles=[Line2D([],[],marker=m,linestyle='None',color='#333333',markersize=4,label=l) for m,l in [('o','33-bus feeder'),('s','69-bus feeder')]],loc='lower left',bbox_to_anchor=(0,1.03),ncol=2,borderaxespad=0,columnspacing=2)
fig.canvas.draw()
if args.audit_root:
 require_matplotlib_panel_alignment(fig,json_out=str(P/'evidence/FigureS1_alignment.json'),overlay_svg=str(P/'evidence/FigureS1_alignment.svg'),strict=True)
fig.savefig(F/'FigureS1_fixed_mapping.pdf')
fig.savefig(F/'FigureS1_fixed_mapping.svg')
fig.savefig(F/'FigureS1_fixed_mapping.png',dpi=600)
fig.savefig(F/'FigureS1_fixed_mapping.tiff',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
plt.close(fig)
