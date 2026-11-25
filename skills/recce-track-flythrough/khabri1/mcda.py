import json,csv,itertools,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from geo import R
O='/home/user/Aftab-Machine/output'
M=json.load(open(f'{R}/work/metrics.json'))['tracks']; ids=[t['name'] for t in M]
# criteria: (label, function -> raw value, lower_is_better)
C=[('Gradient',lambda t:0.5*t['max_grade_pct']/20+0.5*t['pct_gt_1in10']/50,20),
   ('Length (new const)',lambda t:t['new_const_m'],10),
   ('Constr effort (cut)',lambda t:t['cut_m3'],15),
   ('Drainage / washout',lambda t:t['nala_xings']+t['nala_len_m']/50,10),
   ('Slope stability',lambda t:t['sidehill_gt20deg_m'],10),
   ('Maintenance',lambda t:t['nala_len_m']+t['sidehill_gt20deg_m']+t['pct_gt_1in10']*t['len_new_m']/100,5),
   ('Trafficability',lambda t:t['pct_gt_1in7']+3*t['pct_gt_1in5'],10),
   ('Exposure',lambda t:0.5*t['expo_dominating_pct']+0.5*t['expo_plain_road_pct'],20)]
raw=np.array([[f(t) for _,f,_ in C] for t in M])
sc=(raw.max(0)-raw)/np.where(np.ptp(raw,0)>0,np.ptp(raw,0),1)   # 1 = best
w0=np.array([c[2] for c in C],float); w0/=w0.sum()
tot=sc@w0; rank=np.argsort(-tot)
print('scores',dict(zip(ids,tot.round(3))),'rank',[ids[i] for i in rank])
# sensitivity: each weight +-20 %, renormalised
sens=[];win={}
for k in range(len(C)):
    for f in (0.8,1.2):
        w=w0.copy(); w[k]*=f; w/=w.sum(); s=sc@w; b=ids[int(np.argmax(s))]; win[b]=win.get(b,0)+1
        sens.append((C[k][0],f,b,float(np.sort(s)[-1]-np.sort(s)[-2])))
# extreme: exposure weight doubled / halved, gradient halved
extra=[]
for lab,k,f in [('Exposure x2',7,2.0),('Exposure x0.5',7,0.5),('Gradient x0.5',0,0.5),('Length x2',1,2.0)]:
    w=w0.copy(); w[k]*=f; w/=w.sum(); s=sc@w; extra.append((lab,ids[int(np.argmax(s))],dict(zip(ids,s.round(3)))))
print('winners under +-20%:',win); [print(e) for e in extra]
# csv
with open(f'{O}/track_comparison.csv','w',newline='') as fh:
    keys=['name','desc','new_const_m','kmz_newtr_used_m','len_new_m','total_from_chw_km','z_start','z_end','gain_m','loss_m','max_grade_pct','mean_grade_pct','pct_gt_1in10','pct_gt_1in7','pct_gt_1in5','hairpins','nala_xings','nala_len_m','cut_m3','fill_m3','sidehill_gt20deg_m','expo_dominating_pct','expo_plain_road_pct','expo_any_pct']
    wr=csv.writer(fh); wr.writerow(keys+[f'score_{c[0]}' for c in C]+['MCDA_total','rank'])
    rk={ids[i]:r+1 for r,i in enumerate(rank)}
    for t,s,T in zip(M,sc,tot): wr.writerow([round(t[k],2) if isinstance(t[k],float) else t[k] for k in keys]+list(s.round(3))+[round(float(T),3),rk[t['name']]])
json.dump({'criteria':[c[0] for c in C],'weights_pct':(w0*100).round(1).tolist(),'scores':sc.round(3).tolist(),'total':tot.round(3).tolist(),'ids':ids,
  'rank':[ids[i] for i in rank],'sens':sens,'sens_winners':win,'extra':extra},open(f'{R}/work/mcda.json','w'),indent=1)
# chart: radar + bars
cols={'T1':'#8a8f98','T2':'#5b8def','T3':'#3fb8af','T4':'#c77dff','T5':'#f5b700'}
fig=plt.figure(figsize=(16,7),facecolor='#0b1220'); ax=fig.add_subplot(121,polar=True,facecolor='#0b1220')
ang=np.linspace(0,2*np.pi,len(C),endpoint=False); ang=np.r_[ang,ang[0]]
for i,t in enumerate(ids):
    v=np.r_[sc[i],sc[i,0]]; ax.plot(ang,v,color=cols[t],lw=3 if t==ids[rank[0]] else 1.5,label=t); ax.fill(ang,v,color=cols[t],alpha=.18 if t==ids[rank[0]] else .04)
ax.set_xticks(ang[:-1]); ax.set_xticklabels([c[0] for c in C],color='w',fontsize=10); ax.set_yticklabels([]); ax.spines['polar'].set_color('#445'); ax.grid(color='#334')
ax.legend(loc='upper right',bbox_to_anchor=(1.25,1.1),facecolor='#0b1220',labelcolor='w',edgecolor='#445')
ax2=fig.add_subplot(122,facecolor='#0b1220'); ax2.barh([f"{t} {M[i]['desc']}" for i,t in enumerate(ids)],tot,color=[cols[t] for t in ids])
for i,v in enumerate(tot): ax2.text(v+.01,i,f'{v:.2f}',color='w',va='center')
ax2.invert_yaxis(); ax2.tick_params(colors='w'); [s.set_color('#445') for s in ax2.spines.values()]; ax2.set_title('MCDA weighted score (1 = best on every criterion)',color='w')
plt.tight_layout(); plt.savefig(f'{O}/track_comparison.png',dpi=120,facecolor='#0b1220')
