import numpy as np,json
from scipy.ndimage import map_coordinates,gaussian_filter1d
from geo import *
a=np.load(f'{R}/work/dem_full.npy'); H,W=a.shape
def dem(lon,lat): return map_coordinates(a,[(26.0-np.asarray(lat))*H-0.5,(np.asarray(lon)-65.0)*W-0.5],order=3,mode='nearest')
d=json.load(open(f'{R}/sera.json')); t=np.array(d['track'])
e,n=en(t[:,0],t[:,1]); s=np.r_[0,np.cumsum(np.hypot(np.diff(e),np.diff(n)))]
L=s[-1]; K=9.0/(L/1000)          # recce chainage scale (9 km LU recce vs 7.86 km on imagery)
ds=5.0; S=np.arange(0,L,ds); E=np.interp(S,s,e); N=np.interp(S,s,n)
lo,la=ll(E,N); Z=dem(lo,la); CH=S/1000*K
tx=np.gradient(gaussian_filter1d(E,3)); ty=np.gradient(gaussian_filter1d(N,3)); nn=np.hypot(tx,ty); tx/=nn; ty/=nn
# longitudinal grade over 30 m (true ground distance)
g=np.gradient(gaussian_filter1d(Z,2),ds)
# cross slope: plane fit across +-15..30 m
off=np.array([-30,-20,-10,10,20,30.])
Zc=np.stack([dem(*ll(E-ty*o,N+tx*o)) for o in off],1)
cs=np.polyfit(off,Zc.T,1)[0]; cross=np.degrees(np.arctan(np.abs(cs)))
Wd=14/3.28   # 14 ft tr
# section types from KMZ
secs=[]
import re
for nm,p in d['sections']:
    m=re.search(r'Ch ([\d.]+)–([\d.]+)',nm); typ='cutfill' if nm.startswith('Cut') else ('nullah' if nm.startswith('Nullah') else 'level')
    secs.append((float(m.group(1)),float(m.group(2)),typ))
typ=np.array(['level']*len(CH),dtype=object)
for a0,a1,tp in secs: typ[(CH>=a0)&(CH<a1)]=tp
# 1) bench (side-hill) cut on cut & fill (rock) stretches
th=np.radians(np.clip(cross,0,60)); A=np.where(cross>30,Wd**2*np.tan(th)/2,np.where(cross>12,Wd**2*np.tan(th)/8,0))
A=np.where(typ=='cutfill',A,0)
# 2) grade cutting: design profile <= ground with |grade| <= gmax (cut-only, rock)
def env(Z,gmax):
    D=Z.copy()
    for i in range(1,len(D)): D[i]=min(D[i],D[i-1]+gmax*ds)
    for i in range(len(D)-2,-1,-1): D[i]=min(D[i],D[i+1]+gmax*ds)
    return D
gmax=0.14
Dz=env(Z,gmax); depth=Z-Dz
Ag=depth*(Wd+1.0)+depth**2*0.27   # trapezoid, side slopes 1:0.27 (75 deg rock face)
dsr=ds*K  # chainage-scaled length per sample
Vb=(A*dsr).sum(); Vg=(Ag*dsr).sum()
res={'len_img_km':L/1000,'len_recce_km':9.0,'elev_min':float(Z.min()),'elev_max':float(Z.max()),'ch_max':float(CH[Z.argmax()]),
 'grade_max_pct':float(np.abs(g).max()*100),'len_gt10_km':float((np.abs(g)>0.10).sum()*dsr/1000),'len_gt14_km':float((np.abs(g)>0.14).sum()*dsr/1000),
 'len_gt20_km':float((np.abs(g)>0.20).sum()*dsr/1000),'cross_gt30_km':float((cross>30).sum()*dsr/1000),'cross_gt20_km':float((cross>20).sum()*dsr/1000),
 'cross_max':float(cross.max()),'bench_m3':float(Vb),'grade_m3':float(Vg),'grade_cut_max_m':float(depth.max()),'grade_cut_len_km':float((depth>0.3).sum()*dsr/1000),
 'climb_m':float(np.clip(np.diff(Z),0,None).sum()),'descent_m':float(np.clip(-np.diff(Z),0,None).sum())}
for k,v in res.items(): print(k,round(v,2))
# per-km table
for c in range(9):
    m=(CH>=c)&(CH<c+1)
    print(f'Ch {c}-{c+1}: z {Z[m].min():.0f}-{Z[m].max():.0f}  maxgrade {np.abs(g[m]).max()*100:4.1f}%  cross {cross[m].mean():4.1f}deg max {cross[m].max():4.1f}  bench {(A[m]*dsr).sum():7.0f} grade {(Ag[m]*dsr).sum():7.0f} m3')
json.dump({'res':res,'CH':CH.tolist(),'Z':Z.tolist(),'g':g.tolist(),'cross':cross.tolist(),'typ':list(typ),'E':E.tolist(),'N':N.tolist(),'depth':depth.tolist(),'secs':secs},open(f'{R}/work/analysis.json','w'))
