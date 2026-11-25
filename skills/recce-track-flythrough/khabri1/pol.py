# POL & work days via the pol-work-days-calculator engine, user's saved standards (userstd.json)
import json,math,numpy as np
from geo import *
from metrics import acc_at
DEF=dict(margin_pct=10,hrs_per_day=8,ft_per_m=3.28,cft_per_m3=35.32,exc_load_min=20,exc_cut_cfthr=1200,exc_dig_m3hr=30,exc_lph=20,doz_lph=27,doz_spread_m3hr=95,
 doz_maint_hr_km=8,doz_level_hr_km=8,doz_cutfill_hr_km=8,doz_nullah_hr_km=8,doz_ref_width_ft=14,doz_vuln_pct=20,doz_vuln_base=0,dmp_cft=400,dmp_kmpl=1,grd_lph=15,
 grd_speed_kmh=4,grd_blade_m=2.6,grd_overlap_m=0.6,grd_eff=0.75,grd_passes=3,jcb_lph=7,jcb_bucket_cft=35,jcb_cycle_s=40,jcb_dig_m3hr=15,fbt_kmpl=0.5,sc_kmpl=8,dc_kmpl=7,civ_kmpl=3)
S={**DEF,**json.load(open('../scripts/userstd.json'))}; M=1+S['margin_pct']/100
PR=json.load(open(f'{R}/work/profiles.json')); MT={t['name']:t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}
KMZ_NEW=[p for p in kml() if p['kind']=='line'][1]
def sections(tid):
    p=PR[tid]; a=np.array(p['ll']); e,n=en(a[:,0],a[:,1]); Q=np.c_[e,n]
    tx,ty=np.gradient(Q[:,0]),np.gradient(Q[:,1]); nn=np.hypot(tx,ty); tx/=nn; ty/=nn
    off=np.array([-15,-7.5,7.5,15.]); Zc=np.stack([dem(*ll(Q[:,0]-ty*o,Q[:,1]+tx*o)) for o in off],1); cs=np.abs(np.polyfit(off,Zc.T,1)[0])
    typ=np.where(acc_at(e,n)>5,'nullah',np.where(cs>0.15,'cutfill','level'))
    km=np.array(p['s'])/1000; secs=[]; i0=0
    for i in range(1,len(typ)+1):
        if i==len(typ) or typ[i]!=typ[i0]: secs.append([km[i0],km[min(i,len(km)-1)],typ[i0]]); i0=i
    pre=MT[tid]['kmz_newtr_used_m']/1000   # KMZ new tr portion used (typed from its own geometry the same way, done coarsely: as cutfill per KMZ desc: cut 3,500/fill 1,600 over 1.31 km)
    return secs,pre
def calc(tid,veh):
    secs,pre=sections(tid); rows=[]; dz=0.0; secrows=[]
    for a,b,t in secs:
        k=b-a; h=k*S[{'level':'doz_level_hr_km','cutfill':'doz_cutfill_hr_km','nullah':'doz_nullah_hr_km'}[t]]; dz+=h; secrows.append((a,b,t,k,h))
    if pre>0: h=pre*S['doz_cutfill_hr_km']; dz+=h; secrows.insert(0,(-pre,0,'cutfill (KMZ new tr portion)',pre,h))
    cut=MT[tid]['cut_m3']+(3500*pre/1.31 if pre>0 else 0)   # KMZ desc: cut 3,500 m3 over 1.31 km new tr
    exc_rate=S['exc_cut_cfthr']/S['cft_per_m3']               # hill cutting std, cu M/hr
    exc_h=math.ceil(cut/exc_rate*M); doz_h=math.ceil(dz*M); dsp_h=math.ceil(cut/S['doz_spread_m3hr']*M)
    L=[('Excavator (hill cutting)','Hrs',exc_h,S['exc_lph'],f'{cut:,.0f} cu M cut (assessed, 30 m DEM) @ {exc_rate:.0f} cu M/hr'),
       ('Dozer','Hrs',doz_h,S['doz_lph'],f'{sum(x[3] for x in secrows):.2f} km lvl / cut & fill / N filling, 14 ft tr'),
       ('Dozer (dozing of cut spoil)','Hrs',dsp_h,S['doz_lph'],f'{cut:,.0f} cu M @ {S["doz_spread_m3hr"]} cu M/hr')]
    for nm,key,trips,km1,rt in [('FBT','fbt_kmpl',*veh['fbt'],True),('Single Cabin','sc_kmpl',*veh['sc'],False),('Civ Trk','civ_kmpl',*veh['civ'],True)]:
        km=trips*km1*(2 if rt else 1); L.append((nm,'Km',round(km*M),S[key],f'{trips} trips x {km1} km'+(' x 2' if rt else '')))
    out=[]; tot=0
    for d,au,q,r,rm in L:
        lit=round(q*r if au=='Hrs' else q/r); tot+=lit; out.append(dict(d=d,au=au,q=q,rate=r,l=lit,rm=rm))
    days={'Excavator':math.ceil(exc_h/S['hrs_per_day']),'Dozer':math.ceil((doz_h+dsp_h)/S['hrs_per_day'])}
    return dict(track=tid,rows=out,total=tot,days=days,dur=max(days.values()),dur_2doz=max(days['Excavator'],math.ceil(days['Dozer']/2)),sections=secrows,cut_total=cut)
veh={'fbt':(2,20),'sc':(10,40),'civ':(2,20)}   # plt mov Pasni-CHW ~20 km one way (assessed); SC 10 trips x 40 km RT
res={t:calc(t,veh) for t in ['T4','T5','T1','T2','T3']}
json.dump(res,open(f'{R}/work/pol.json','w'),indent=1)
for t,r in res.items(): print(t,'POL',r['total'],'lit | days',r['days'],'dur',r['dur'],'| w/2 doz',r['dur_2doz'],'| cut',round(r['cut_total']))
