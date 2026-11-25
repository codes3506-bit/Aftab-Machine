import json,numpy as np
from scipy.ndimage import gaussian_filter1d,maximum_filter,map_coordinates
from geo import *
POST=(63.43978,25.42739)
G=np.load(f'{R}/work/grid.npz'); gx0,gy0,ST=float(G['x0']),float(G['y0']),float(G['st']); ACC=G['ACC']
def acc_at(e,n): return map_coordinates(ACC,[(np.asarray(n)-gy0)/ST,(np.asarray(e)-gx0)/ST],order=0,mode='nearest')
L=[p for p in kml() if p['kind']=='line']
def line_en(pts): e,n=en(*np.array(pts).T); return np.c_[e,n]
EX=line_en(L[0]['pts']); NEW=line_en(L[1]['pts']); KAC=line_en(L[2]['pts'])
def resample(P,ds=5.0):
    s=np.r_[0,np.cumsum(np.hypot(*np.diff(P,axis=0).T))]; S=np.arange(0,s[-1],ds); S=np.r_[S,s[-1]]
    return np.c_[np.interp(S,s,P[:,0]),np.interp(S,s,P[:,1])],S
def smooth(P,sig=2):
    Q,_=resample(P,5); Q[:,0]=gaussian_filter1d(Q[:,0],sig,mode='nearest'); Q[:,1]=gaussian_filter1d(Q[:,1],sig,mode='nearest'); Q[0]=P[0];Q[-1]=P[-1]; return Q
def chain_to(P_line,pt):
    s=np.r_[0,np.cumsum(np.hypot(*np.diff(P_line,axis=0).T))]; k=np.argmin(np.hypot(*(P_line-pt).T)); return s[k],k
# observers
lo=np.linspace(63.40,63.48,321); la=np.linspace(25.39,25.46,281); LO,LA=np.meshgrid(lo,la); Zr=dem(LO,LA)
pe,pn=en(*POST); Ee,Nn=en(LO,LA); rr=np.hypot(Ee-pe,Nn-pn)
pk=(Zr==maximum_filter(Zr,size=7))&(Zr>160)&(rr<4000)&(rr>300)
OPA=[(float(Ee[i,j]),float(Nn[i,j]),float(Zr[i,j])) for i,j in zip(*np.where(pk))]
road=[(63.4262,25.4158),(63.4250,25.4200),(63.4240,25.4240),(63.4232,25.4282),(63.4215,25.4330),(63.4200,25.4380)]
plain=[(63.4300,25.4360),(63.4250,25.4420),(63.4350,25.4380),(63.4400,25.4400),(63.4150,25.4250)]
OPB=[(*en(*p),float(dem(np.array([p[0]]),np.array([p[1]]))[0])) for p in road+plain]
VE=np.load(f'{R}/work/grid.npz')
def visible(e,n,z,ops,h_o=2.0,h_t=3.0):
    vis=np.zeros(len(e),bool); t=np.linspace(0,1,120)[1:-1][:,None]
    for oe,on,oz in ops:
        se=oe+t*(e[None]-oe); sn=on+t*(n[None]-on); zz=dem(*ll(se,sn))
        line=oz+h_o+t*(z[None]+h_t-oz-h_o); vis|=np.all(zz<line,axis=0)
    return vis
def analyse(name,P,junction):  # P: new-construction polyline (en) from junction to post
    Q=smooth(P); Q,S=resample(Q,5); lo_,la_=ll(*Q.T); Z=dem(lo_,la_)
    Zs=gaussian_filter1d(Z,2); g=np.gradient(Zs,5.0); g50=np.convolve(g,np.ones(10)/10,'same'); ag=np.abs(g50)
    hd=np.degrees(np.arctan2(*np.gradient(Q,axis=0).T[::-1])); 
    turn=np.abs((np.roll(hd,-8)-np.roll(hd,8)+180)%360-180)[8:-8]; hp=0; k=0
    while k<len(turn):
        if turn[k]>110: hp+=1; k+=12
        else: k+=1
    # cross slope -> bench cut for 4.3 m (14 ft) formation
    tx,ty=np.gradient(Q[:,0]),np.gradient(Q[:,1]); nn=np.hypot(tx,ty); tx/=nn; ty/=nn
    off=np.array([-15,-7.5,7.5,15.]); Zc=np.stack([dem(*ll(Q[:,0]-ty*o,Q[:,1]+tx*o)) for o in off],1)
    cs=np.abs(np.polyfit(off,Zc.T,1)[0]); Wd=4.3
    th=np.arctan(cs); cut_side=np.where(cs>0.05,Wd**2*np.tan(th)/(2*(1-np.tan(th)*0.5).clip(0.2)),0)*0.5
    # grade cutting to 1:10 envelope (cut-only)
    def env(Z,gm,ds=5.0):
        D=Z.copy()
        for i in range(1,len(D)): D[i]=min(D[i],D[i-1]+gm*ds)
        for i in range(len(D)-2,-1,-1): D[i]=min(D[i],D[i+1]+gm*ds)
        return D
    dep=Zs-env(Zs,1/7); Ag=dep*(Wd+1)+dep**2*0.5
    cut=float((cut_side*5).sum()+(Ag*5).sum()); fill=0.45*float((cut_side*5).sum())
    a=acc_at(*Q.T); xing=0; inn=False
    for v in a>5:
        if v and not inn: xing+=1
        inn=v
    nala_len=float((a>5).sum()*5)
    visA=visible(Q[:,0],Q[:,1],Z,OPA); visB=visible(Q[:,0],Q[:,1],Z,OPB)
    side_len=float((cs>0.36).sum()*5)  # cross slope >20 deg
    r=dict(name=name,len_new_m=float(S[-1]),junction_ch_km=junction,total_from_chw_km=junction+S[-1]/1000,
      z_start=float(Z[0]),z_end=float(Z[-1]),gain_m=float(np.clip(np.diff(Zs),0,None).sum()),loss_m=float(np.clip(-np.diff(Zs),0,None).sum()),
      max_grade_pct=float(ag.max()*100),mean_grade_pct=float(ag.mean()*100),
      pct_gt_1in10=float((ag>0.10).mean()*100),pct_gt_1in7=float((ag>1/7).mean()*100),pct_gt_1in5=float((ag>0.2).mean()*100),
      hairpins=hp,nala_xings=xing,nala_len_m=nala_len,cut_m3=cut,fill_m3=fill,sidehill_gt20deg_m=side_len,
      expo_dominating_pct=float(visA.mean()*100),expo_plain_road_pct=float(visB.mean()*100),expo_any_pct=float((visA|visB).mean()*100))
    prof=dict(s=S.tolist(),z=Z.tolist(),g=g50.tolist(),visA=visA.tolist(),visB=visB.tolist(),ll=np.c_[lo_,la_].tolist())
    return r,prof
if __name__=='__main__':
    d=json.load(open(f'{R}/work/lcp.json'))
    newlen=np.r_[0,np.cumsum(np.hypot(*np.diff(NEW,axis=0).T))]
    defs={'T1':('DIRECT_1in5','Direct climb – S spur (old climb)'),'T2':('LCP_S_1in7','Graded S spur 1:7'),
          'T3':('LCP_W_1in7','W spur / ridge'),'T4':('LCP_free_1in10','E flank (rear-east)'),'T5':('LCP_N_1in7','Rear / N foothill')}
    res=[];profs={}
    for tid,(k,desc) in defs.items():
        P=line_en(d[k]['ll'])   # LCP path runs junction -> post
        # junction chainage: on existing tr or KMZ new tr
        sE,kE=chain_to(EX,P[0]); sN,kN=chain_to(NEW,P[0]); dE=np.hypot(*(EX[kE]-P[0])); dN=np.hypot(*(NEW[kN]-P[0]))
        if dE<=dN: jch=sE/1000*3.92/ (np.r_[0,np.cumsum(np.hypot(*np.diff(EX,axis=0).T))][-1]/1000); pre_new=0.0
        else: jch=3.92+sN/1000; pre_new=sN
        r,pr=analyse(tid,P,jch); r['desc']=desc; r['src']=k; r['kmz_newtr_used_m']=float(pre_new)
        r['new_const_m']=r['len_new_m']+pre_new
        res.append(r); profs[tid]=pr; print(tid,desc,{a:(round(b,1) if isinstance(b,float) else b) for a,b in r.items() if a not in('name','desc','src')})
    json.dump({'tracks':res,'OPA':OPA,'OPB':OPB},open(f'{R}/work/metrics.json','w'),indent=1); json.dump(profs,open(f'{R}/work/profiles.json','w'))
    print('OPA',len(OPA),'OPB',len(OPB))
