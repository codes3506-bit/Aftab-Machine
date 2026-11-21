import numpy as np,json
from scipy.ndimage import map_coordinates,gaussian_filter1d
from geo import *
a=np.load(f'{R}/work/dem_full.npy'); H,W=a.shape
def dem(lon,lat): return map_coordinates(a,[(26.0-np.asarray(lat))*H-0.5,(np.asarray(lon)-65.0)*W-0.5],order=3,mode='nearest')
import sys
raw=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'alt_raw.json')); OUTF=sys.argv[2] if len(sys.argv)>2 else 'analysis_alt.json'; x0,y0,RES,nx,ny=raw['grid']; acc=np.load('acc.npy')
e=np.array(raw['E']);n=np.array(raw['N'])
s=np.r_[0,np.cumsum(np.hypot(np.diff(e),np.diff(n)))]
ds=5.0; S=np.arange(0,s[-1],ds); E=gaussian_filter1d(np.interp(S,s,e),5,mode='nearest'); N=gaussian_filter1d(np.interp(S,s,n),5,mode='nearest')
E[0],N[0],E[-1],N[-1]=e[0],n[0],e[-1],n[-1]
s2=np.r_[0,np.cumsum(np.hypot(np.diff(E),np.diff(N)))]; S=np.arange(0,s2[-1],ds); E=np.interp(S,s2,E); N=np.interp(S,s2,N)
L=S[-1]; K=9.0/7.862   # same imagery->ground factor as the recced tr
CH=S/1000*K; lo,la=ll(E,N); Z=dem(lo,la)
tx=np.gradient(gaussian_filter1d(E,3)); ty=np.gradient(gaussian_filter1d(N,3)); nn=np.hypot(tx,ty); tx/=nn; ty/=nn
g=np.gradient(gaussian_filter1d(Z,2),ds)
off=np.array([-30,-20,-10,10,20,30.]); Zc=np.stack([dem(*ll(E-ty*o,N+tx*o)) for o in off],1)
cs=np.polyfit(off,Zc.T,1)[0]; cross=np.degrees(np.arctan(np.abs(cs)))
def accat(x,y): return acc[np.clip(((y-y0)/RES).astype(int),0,ny-1),np.clip(((x-x0)/RES).astype(int),0,nx-1)]
ac=np.max(np.stack([accat(E-ty*o,N+tx*o) for o in (-12,0,12)]),0)
Wd=14/3.28
from scipy.ndimage import distance_transform_edt
_c=json.load(open('chw.json')); CE,CN=np.array(_c['E']),np.array(_c['N'])
dro=np.array([np.min(np.hypot(CE-e_,CN-n_)) for e_,n_ in zip(E,N)]); onroad=dro<25
# work type per sample
g50=np.convolve(g,np.ones(10)/10,mode='same')
typ=np.where((np.tan(np.radians(cross))>0.15)|(np.abs(g50)>0.10),'cutfill','level').astype(object)
typ[onroad]='road'
# nullah xings: local maxima of catchment > 0.25 km2
xing=[]
i=0
while i<len(ac):
    if ac[i]>0.25:
        j=i
        while j<len(ac) and ac[j]>0.25: j+=1
        k=i+int(np.argmax(ac[i:j])); xing.append((float(CH[k]),float(ac[k]),k))
        if not onroad[k]: typ[max(0,i-3):min(len(typ),j+3)]='nullah'
        else: xing.pop()
        i=j
    else: i+=1
# merge runs shorter than 60 m into previous
def runs(t):
    out=[];i=0
    while i<len(t):
        j=i
        while j<len(t) and t[j]==t[i]: j+=1
        out.append([t[i],i,j]); i=j
    return out
for _ in range(3):
    rr=runs(typ)
    for k,(t,i,j) in enumerate(rr):
        if (j-i)*ds<60 and t not in ('nullah','road') and k>0 and rr[k-1][0]!='road': typ[i:j]=rr[k-1][0]
th=np.radians(np.clip(cross,0,60)); Ab=np.where(cross>30,Wd**2*np.tan(th)/2,np.where(cross>12,Wd**2*np.tan(th)/8,0)); Ab=np.where(typ=='cutfill',Ab,0)
def env(Z,gmax):
    D=Z.copy()
    for i in range(1,len(D)): D[i]=min(D[i],D[i-1]+gmax*ds)
    for i in range(len(D)-2,-1,-1): D[i]=min(D[i],D[i+1]+gmax*ds)
    return D
depth=Z-env(Z,0.14); depth[onroad]=0; Ag=depth*(Wd+1)+depth**2*0.27
dsr=ds*K; Vb=(Ab*dsr).sum(); Vg=(Ag*dsr).sum()
secs=[[round(CH[i],2),round(CH[min(j,len(CH)-1)],2),t] for t,i,j in runs(typ)]
km={t:sum(b-a for a,b,tt in secs if tt==t) for t in ('level','cutfill','nullah','road')}
def gwin(w):
    k=int(w/ds); gg=(Z[k:]-Z[:-k])/w; return float(np.abs(gg).max()*100)
res={'len_img_km':L/1000,'len_est_km':float(CH[-1]),'elev_min':float(Z.min()),'elev_max':float(Z.max()),'ch_max':float(CH[Z.argmax()]),
 'grade100':gwin(100),'grade50':gwin(50),'onroad':onroad.tolist(),'len_gt10_km':float((np.abs(g50)>0.10).sum()*dsr/1000),'len_gt14_km':float((np.abs(g50)>0.14).sum()*dsr/1000),
 'len_gt20_km':float((np.abs(g50)>0.20).sum()*dsr/1000),'cross_max':float(cross.max()),'bench_m3':float(Vb),'grade_m3':float(Vg),'grade_cut_max_m':float(depth.max()),
 'climb_m':float(np.clip(np.diff(Z),0,None).sum()),'descent_m':float(np.clip(-np.diff(Z),0,None).sum()),'km':km,'nx':len(xing),
 'nx_med':sum(1 for x in xing if x[1]>1.0),'nx_major':sum(1 for x in xing if x[1]>5.0)}
rock=Vb+Vg; pol=(km['level']*8+km['cutfill']*80+km['nullah']*80)*0.7*27*1.1 + rock*(20/34+27/95)*1.1
print(OUTF,'road %.2f'%km['road'],'len %.2f est %.2f maxz %.0f g100 %.1f g50 %.1f rock %.0f nx %d  level %.2f cut %.2f null %.2f  POLplant~%.0f'%(L/1000,CH[-1],Z.max(),res['grade100'],res['grade50'],rock,len(xing),km['level'],km['cutfill'],km['nullah'],pol))
json.dump({'res':res,'CH':CH.tolist(),'Z':Z.tolist(),'g':g.tolist(),'cross':cross.tolist(),'typ':list(typ),'E':E.tolist(),'N':N.tolist(),'depth':depth.tolist(),'secs':secs,'xing':xing},open(OUTF,'w'))
