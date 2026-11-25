# grade-constrained least-cost path to the hill post, per approach sector
import json,numpy as np,scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import gaussian_filter
from geo import *
POST=(63.43978,25.42739)
W,E,S,N=63.424,63.458,25.410,25.440; ST=10.0
x0,y0=en(W,S); x1,y1=en(E,N)
xs=np.arange(x0,x1,ST); ys=np.arange(y0,y1,ST); X,Y=np.meshgrid(xs,ys); LO,LA=ll(X,Y)
Z=dem(LO,LA).astype(np.float64); ny,nx=Z.shape
gy,gx=np.gradient(Z,ST); slope=np.degrees(np.arctan(np.hypot(gx,gy)))
# D8 flow accumulation on priority-flood filled DEM
import heapq
def fill(z):
    f=np.full(z.shape,np.inf); seen=np.zeros(z.shape,bool); h=[]
    for i in range(ny):
        for j in (0,nx-1): heapq.heappush(h,(z[i,j],i,j)); seen[i,j]=True
    for j in range(nx):
        for i in (0,ny-1):
            if not seen[i,j]: heapq.heappush(h,(z[i,j],i,j)); seen[i,j]=True
    while h:
        v,i,j=heapq.heappop(h); f[i,j]=v
        for di in(-1,0,1):
            for dj in(-1,0,1):
                a,b=i+di,j+dj
                if 0<=a<ny and 0<=b<nx and not seen[a,b]: seen[a,b]=True; heapq.heappush(h,(max(z[a,b],v+1e-3),a,b))
    return f
F=fill(Z); order=np.argsort(-F,axis=None); acc=np.ones(Z.size)
Ff=F.ravel()
for k in order:
    i,j=divmod(k,nx); best=None;bd=0
    for di in(-1,0,1):
        for dj in(-1,0,1):
            if di==dj==0: continue
            a,b=i+di,j+dj
            if 0<=a<ny and 0<=b<nx:
                d=(Ff[k]-F[a,b])/np.hypot(di,dj)
                if d>bd: bd=d;best=a*nx+b
    if best is not None: acc[best]+=acc[k]
ACC=acc.reshape(Z.shape)*ST*ST/1e4   # catchment ha
def tracks_kml():
    L=[p for p in kml() if p['kind']=='line']; return L
def rasterize(pts):
    e,n=en(*np.array(pts).T); out=set()
    for k in range(len(e)-1):
        L=np.hypot(e[k+1]-e[k],n[k+1]-n[k]); m=max(2,int(L/3))
        for t in np.linspace(0,1,m):
            i=int(round((n[k]+t*(n[k+1]-n[k])-y0)/ST)); j=int(round((e[k]+t*(e[k+1]-e[k])-x0)/ST))
            if 0<=i<ny and 0<=j<nx: out.add(i*nx+j)
    return out
src={}
L=tracks_kml(); chw_len=[0,3920,5230]
for li,p in enumerate(L):
    for c in rasterize(p['pts']): src[c]=min(src.get(c,1e9),0.0)
pi=int(round((en(*POST)[1]-y0)/ST)); pj=int(round((en(*POST)[0]-x0)/ST)); tgt=pi*nx+pj
def graph(gmax,cfg,block=None):
    R=3; offs=[(di,dj) for di in range(-R,R+1) for dj in range(-R,R+1) if (di,dj)!=(0,0) and np.gcd(abs(di),abs(dj))==1]
    I=[];J=[];C=[]
    ii,jj=np.mgrid[0:ny,0:nx]
    for di,dj in offs:
        a=ii+di;b=jj+dj; ok=(a>=0)&(a<ny)&(b>=0)&(b<nx)
        u=(ii*nx+jj)[ok]; v=(a*nx+b)[ok]; Lg=np.hypot(di,dj)*ST
        dz=np.abs(Z.ravel()[v]-Z.ravel()[u]); g=dz/Lg
        mid_s=(slope.ravel()[u]+slope.ravel()[v])/2; mid_a=np.maximum(ACC.ravel()[u],ACC.ravel()[v])
        keep=g<=gmax
        cost=Lg*(1+cfg['gp']*np.clip(g-0.10,0,None)/0.04)            # grade above 1:10
        cost*= 1+cfg['side']*np.clip(mid_s-12,0,None)/10              # side-hill cut
        cost+= cfg['nala']*(mid_a>5)*Lg*0.5                           # crossing/running in a nala >5 ha
        if block is not None: keep&=~(block[u]|block[v])
        I.append(u[keep]);J.append(v[keep]);C.append(cost[keep])
    return sp.csr_matrix((np.concatenate(C),(np.concatenate(I),np.concatenate(J))),shape=(Z.size,Z.size))
def run(gmax,cfg,sector=None):
    block=None
    if sector:
        ang=(np.degrees(np.arctan2(X-xs[pj],Y-ys[pi]))+360)%360; r=np.hypot(X-xs[pj],Y-ys[pi])
        lo,hi=sector; ins=((ang-lo)%360)<((hi-lo)%360)
        block=((r>40)&(r<300)&~ins).ravel()
    G=graph(gmax,cfg,block); srcs=list(src.keys())
    D,P=dijkstra(G,directed=False,indices=tgt,return_predecessors=True)
    best=min(srcs,key=lambda c:D[c])
    if not np.isfinite(D[best]): return None
    path=[best]
    while path[-1]!=tgt: path.append(P[path[-1]])
    pts=[[float(xs[c%nx]),float(ys[c//nx])] for c in path]
    lo_,la_=ll(*np.array(pts).T); return {'cost':float(D[best]),'ll':np.c_[lo_,la_].tolist()}
if __name__=='__main__':
    std={'gp':3.0,'side':0.6,'nala':1.0}
    out={}
    for nm,g,cfg,sec in [('LCP_free_1in7',1/7,std,None),('LCP_S_1in7',1/7,std,(135,225)),('LCP_W_1in7',1/7,std,(225,315)),
                         ('LCP_N_1in7',1/7,std,(315,45)),('LCP_E_1in7',1/7,std,(45,135)),('DIRECT_1in5',1/5,{'gp':0.3,'side':0.1,'nala':0.2},None),
                         ('LCP_free_1in10',0.105,std,None)]:
        r=run(g,cfg,sec); out[nm]=r; print(nm, None if r is None else (round(r['cost']), len(r['ll'])))
    np.savez(f'{R}/work/grid.npz',Z=Z,ACC=ACC,slope=slope,x0=x0,y0=y0,st=ST)
    json.dump(out,open(f'{R}/work/lcp.json','w'))
