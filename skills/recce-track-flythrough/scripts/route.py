import numpy as np,json,sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import zoom, gaussian_filter, map_coordinates
from geo import *
M=json.load(open('meta.json')); hm=np.load('hm.npy'); H=M['hm']
RES=12.0; x0,x1,y0,y1=-6500,4200,-3600,3400
f=RES/6; i0=int((x0-H['x0'])/6); j0=int((y0-H['y0'])/6); nx=int((x1-x0)/RES); ny=int((y1-y0)/RES)
Z=hm[j0:j0+int(ny*f), i0:i0+int(nx*f)][::2,::2].astype(np.float64)[:ny,:nx]
gy,gx=np.gradient(Z,RES)
# --- flow accumulation (D8) on depression-filled DEM (priority flood)
import heapq
Zs=gaussian_filter(Z,1.0); Fz=Zs.copy(); done=np.zeros(Z.shape,bool); hq=[]
for j in range(ny):
    for i in (0,nx-1): heapq.heappush(hq,(Fz[j,i],j,i)); done[j,i]=True
for i in range(nx):
    for j in (0,ny-1):
        if not done[j,i]: heapq.heappush(hq,(Fz[j,i],j,i)); done[j,i]=True
while hq:
    z_,j,i=heapq.heappop(hq)
    for dj,di in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
        jj,ii=j+dj,i+di
        if 0<=jj<ny and 0<=ii<nx and not done[jj,ii]:
            done[jj,ii]=True; Fz[jj,ii]=max(Fz[jj,ii],z_+1e-4); heapq.heappush(hq,(Fz[jj,ii],jj,ii))
Zflow=Fz
order=np.argsort(Zflow,axis=None)[::-1]; acc=np.ones(Z.size); Zf=Z.ravel()
nb=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
J,I=np.unravel_index(order,Z.shape)
best=np.full(Z.size,-1); bestd=np.zeros(Z.size)
for dj,di in nb:
    jj=np.clip(np.arange(ny)[:,None]+dj,0,ny-1); ii=np.clip(np.arange(nx)[None,:]+di,0,nx-1)
    d=(Zflow-Zflow[jj,ii])/np.hypot(dj,di); idx=(jj*nx+ii).ravel(); d=d.ravel()
    m=d>bestd; best[m]=idx[m]; bestd[m]=d[m]
for k in order:
    b=best[k]
    if b>=0: acc[b]+=acc[k]
acc=acc.reshape(Z.shape)*RES*RES/1e6   # km2
fdx=np.zeros(Z.size); fdy=np.zeros(Z.size); bb=best>=0; fdx[bb]=(best[bb]%nx)-(np.arange(Z.size)[bb]%nx); fdy[bb]=(best[bb]//nx)-(np.arange(Z.size)[bb]//nx)
fn=np.hypot(fdx,fdy)+1e-9; FDX=(fdx/fn).reshape(Z.shape); FDY=(fdy/fn).reshape(Z.shape)
np.save('acc.npy',acc); print('acc max',acc.max(),'cells>0.25',(acc>0.25).sum())
# --- graph
W=4.27
GSOFT=float(sys.argv[1]) if len(sys.argv)>1 else 0.12; GHARD=float(sys.argv[2]) if len(sys.argv)>2 else 0.20; GPEN=float(sys.argv[3]) if len(sys.argv)>3 else 2.0; OUT=sys.argv[4] if len(sys.argv)>4 else 'alt_raw.json'
moves=[(dj,di) for dj in range(-2,3) for di in range(-2,3) if (dj,di)!=(0,0) and np.gcd(abs(dj),abs(di))==1]
rows=[];cols=[];vals=[]
from scipy.ndimage import distance_transform_edt
AV=float(sys.argv[5]) if len(sys.argv)>5 else 0.0
_A=json.load(open('analysis.json')); _m=np.ones(Z.shape,bool)
for _e,_n in zip(_A['E'][60:-60],_A['N'][60:-60]): _m[int((_n-y0)/RES),int((_e-x0)/RES)]=False
_r=np.ones(Z.shape,bool); _c=json.load(open('chw.json'))
for _e,_n in zip(_c['E'],_c['N']):
    _j,_i=int((_n-y0)/RES),int((_e-x0)/RES)
    if 0<=_j<ny and 0<=_i<nx: _r[_j,_i]=False
ROAD=distance_transform_edt(_r)*RES<=18
DCUR=distance_transform_edt(_m)*RES; AVOID=np.where(DCUR<400,AV,0.0)
idx=np.arange(Z.size).reshape(Z.shape)
POL_M3=20/34.0+27/95.0           # excavator rock cut + dozing spoil, lit per cu M
for dj,di in moves:
    a=idx[max(0,-dj):ny-max(0,dj), max(0,-di):nx-max(0,di)]
    b=idx[max(0,dj):ny-max(0,-dj)+(ny if False else 0) if False else None, None] if False else None
    js=slice(max(0,-dj),ny-max(0,dj)); is_=slice(max(0,-di),nx-max(0,di))
    jt=slice(max(0,dj),ny-max(0,-dj)); it=slice(max(0,di),nx-max(0,-di))
    L=RES*np.hypot(dj,di); ux,uy=di/np.hypot(dj,di),dj/np.hypot(dj,di)
    dz=Z[jt,it]-Z[js,is_]; g=np.abs(dz)/L
    gxm=(gx[js,is_]+gx[jt,it])/2; gym=(gy[js,is_]+gy[jt,it])/2
    c=np.abs(-gxm*uy+gym*ux)                      # cross slope (tan)
    cut=np.where(c>0.58,W*W*c/2,np.where(c>0.15,W*W*c/8,0))*L     # bench cut m3
    gr=np.where(g>0.14,(g-0.14)*L*0.5*(W+1)*L/2,0)                 # grade-cut proxy m3
    pol=L*(0.151+np.where(c>0.15,1.36,0)) + (cut+gr)*POL_M3
    pol=pol+np.where(g>GHARD,1e4,0)+np.where(g>GSOFT,GPEN*L,0)
    nacc=np.maximum(acc[js,is_],acc[jt,it]); across=np.abs(FDX[js,is_]*uy-FDY[js,is_]*ux)
    pol+=np.where(nacc>0.25,(across*(25*1.36*0.7+np.minimum(nacc,5)*40)/ (RES/L*0+1))*(L/RES)/np.hypot(1,0)*0+across*(L*1.36*0.7+np.minimum(nacc,5)*30)+(1-across)*L*0.25,0)   # xing cost ~ across-flow; along-bed small flood-risk cost
    pol=pol+AVOID[jt,it]*L
    onr=ROAD[js,is_]&ROAD[jt,it]; pol=np.where(onr,L*0.02,pol)
    rows.append(a.ravel()); cols.append(idx[jt,it].ravel()); vals.append(pol.ravel())
G=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(Z.size,Z.size)).tocsr()
sc=json.load(open('scene.json')); P={l['id']:l['p'] for l in sc['labels']}
def node(p): return int((p[1]-y0)/RES)*nx+int((p[0]-x0)/RES)
s=node(P['B-3 Post']); t=node(P['Haryan BOO'])
dist,pred=dijkstra(G,indices=s,return_predecessors=True)
path=[t]
while path[-1]!=s: path.append(pred[path[-1]])
path=path[::-1]; J,I=np.unravel_index(path,Z.shape)
E_=x0+(I+0.5)*RES; N_=y0+(J+0.5)*RES
print('cost POL proxy',dist[t],'len',np.hypot(np.diff(E_),np.diff(N_)).sum())
# cost of current track under same model for comparison
A=json.load(open('analysis.json'))
json.dump({'E':E_.tolist(),'N':N_.tolist(),'grid':[x0,y0,RES,nx,ny]},open(OUT,'w'))
