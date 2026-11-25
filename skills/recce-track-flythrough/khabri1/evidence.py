import json,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
from geo import *
O='/home/user/Aftab-Machine/output'; WA='/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/scratchpad/wa1'
PR=json.load(open(f'{R}/work/profiles.json')); L=json.load(open(f'{R}/work/lcp.json'))
COL={'T1':'#9aa0aa','T2':'#5b8def','T3':'#3fb8af','T4':'#c77dff','T5':'#f5b700'}
fig=plt.figure(figsize=(24,15),facecolor='#0b1220')
def sty(ax,t): ax.set_facecolor('#0b1220'); ax.tick_params(colors='#aab'); ax.set_title(t,color='w',fontsize=13,weight='bold',loc='left')
# A: sector-forced LCP runs on imagery
ax=fig.add_axes([0.02,0.40,0.47,0.56]); W,E,S,N=63.428,63.452,25.419,25.4335
m=Mos(18); x0,y0=m.px(W,N); x1,y1=m.px(E,S); ax.imshow(m.im.crop((int(x0),int(y0),int(x1),int(y1))),extent=[W,E,S,N],aspect=1/np.cos(np.radians(25.42)))
lo=np.linspace(W,E,300); la=np.linspace(N,S,200); LO,LA=np.meshgrid(lo,la); cs=ax.contour(LO,LA,dem(LO,LA),levels=np.arange(20,300,20),colors='w',linewidths=.35,alpha=.6); ax.clabel(cs,fontsize=6,fmt='%d')
for k,c,lab in [('LCP_S_1in7','#5b8def','forced S'),('LCP_W_1in7','#3fb8af','forced W'),('LCP_N_1in7','#f5b700','forced N  -> T5'),('LCP_E_1in7','#c77dff','forced E'),('DIRECT_1in5','#9aa0aa','unconstrained 1:5 -> T1'),('LCP_free_1in10','#ff5d5d','free 1:10 -> T4')]:
    a=np.array(L[k]['ll']); ax.plot(a[:,0],a[:,1],color=c,lw=2,label=f'{lab}  (cost {L[k]["cost"]:.0f})')
ax.plot(63.43978,25.42739,'*',color='w',ms=18,mec='k'); ax.legend(loc='lower right',fontsize=9,facecolor='#0b1220',labelcolor='w')
ax.set_xlim(W,E); ax.set_ylim(S,N); sty(ax,'A  LCP (grade <= 1:7, side-hill + nala penalties) forced to arrive from each sector - source 2')
# B: N-S DEM cross-section through post
ax=fig.add_axes([0.53,0.70,0.45,0.25]); pe,pn=en(63.43978,25.42739); d=np.arange(-450,451,10)
for az,c,lab in [(0,'#f5b700','S  <-  post  ->  N'),(330,'#3fb8af','SSE <- post -> NNW')]:
    a=np.radians(az); z=dem(*ll(pe+d*np.sin(a),pn+d*np.cos(a))); ax.plot(d,z,color=c,lw=2.5,label=lab)
ax.axvline(0,color='w',ls=':'); ax.text(5,150,'POST',color='w'); ax.text(150,70,'strike hollow\n(N / rear side)',color='#f5b700'); ax.text(-430,60,'steep S face\n(scarp)',color='#f5b700')
ax.legend(facecolor='#0b1220',labelcolor='w'); ax.grid(alpha=.15); ax.set_xlabel(''); sty(ax,'B  DEM cross-section: steep S face vs gentle N side with hollow (defilade pocket) - source 3')
# C: drone frames
for i,(t,cap) in enumerate([(49,'0:48  BOO / TI Cam ridge - range S face'),(64,'1:03  post ridge S face: bedding outcrops (strike ENE-WSW)'),(67,'1:06  "Khabri I" - Shadi K Nadi plain beyond crest (N side)')]):
    ax=fig.add_axes([0.53+i*0.153,0.40,0.145,0.25]); ax.imshow(Image.open(f'{WA}/f{t:03d}.jpg').crop((0,0,848,400))); ax.axis('off'); ax.set_title(cap,color='w',fontsize=8.5,loc='left',wrap=True)
fig.text(0.53,0.665,'C  Drone clip (WhatsApp 848x480, no telemetry) - geotags ASSESSED by matching ridge to DEM - source 4',color='w',fontsize=13,weight='bold')
# D: metrics table
ax=fig.add_axes([0.02,0.03,0.96,0.32]); ax.axis('off'); M=json.load(open(f'{R}/work/metrics.json'))['tracks']; mc=json.load(open(f'{R}/work/mcda.json'))
cols=['Track','New const (m)','Max grade %','Mean %','>1:10 %','>1:7 %','>1:5 %','Hairpins','Nala xings','Cut m3 (assessed)','Expo dominating %','Expo W-NW low gnd %','MCDA']
rows=[[t['name']+' '+t['desc'].replace(' (old climb)','').replace(' (rear-east)',''),f"{t['new_const_m']:.0f}",f"{t['max_grade_pct']:.1f}",f"{t['mean_grade_pct']:.1f}",f"{t['pct_gt_1in10']:.0f}",f"{t['pct_gt_1in7']:.0f}",f"{t['pct_gt_1in5']:.0f}",t['hairpins'],t['nala_xings'],f"{t['cut_m3']:,.0f}",f"{t['expo_dominating_pct']:.0f}",f"{t['expo_plain_road_pct']:.0f}",f"{s:.2f}"] for t,s in zip(M,mc['total'])]
tb=ax.table(cellText=rows,colLabels=cols,loc='upper center',cellLoc='center'); tb.auto_set_font_size(False); tb.set_fontsize(11); tb.scale(1,2.1)
for (r,c),cell in tb.get_celld().items():
    cell.set_edgecolor('#334'); cell.set_facecolor('#111a2e' if r else '#1d2a45'); cell.get_text().set_color('w')
    if r and c==0: cell.get_text().set_color(COL[M[r-1]['name']]); cell._loc='left'
ax.set_title('D  Metrics (Cop GLO-30, 5 m samples; grades over 50 m)  -  MCDA rank: '+' > '.join(mc['rank'])+'   |   +-20% each weight: '+str(mc['sens_winners']),color='w',fontsize=13,weight='bold',loc='left')
fig.text(0.02,0.975,'TRACK DISCOVERY EVIDENCE  -  KHABRI-1 HILL POST (RL 133)   source 1 = imagery (Esri 0.5 m): no vehicle track to post visible; faint footpath W along ridge spine (unconfirmed)',color='#f5b700',fontsize=15,weight='bold')
plt.savefig(f'{O}/track_discovery_evidence.png',dpi=100,facecolor='#0b1220'); print('ok')
