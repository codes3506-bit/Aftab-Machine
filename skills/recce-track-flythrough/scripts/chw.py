import json,numpy as np
from PIL import Image
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import coo_matrix
from scipy.ndimage import gaussian_filter
from geo import *
Image.MAX_IMAGE_PIXELS=None
M=json.load(open('meta.json'))['z17']; im=Image.open('tex17.png')
def px(e,n):
    lon,lat=ll(e,n); x,y=tile_xy(lon,lat,17); return (x-M['x0'])*256,(y-M['y0'])*256
a,b=px(-6200,-500); c,d=px(900,-3000); s=0.5
crop=np.asarray(im.crop((int(a),int(b),int(c),int(d))).resize((int((c-a)*s),int((d-b)*s)))).astype(float)
r,g,bl=crop[...,0],crop[...,1],crop[...,2]; mx=crop.max(2); mn=crop.min(2); sat=(mx-mn)/(mx+1)
v=crop.mean(2)
mm=mx-mn; road=np.exp(-((mm-9)/7)**2)*np.exp(-((v-82)/22)**2)*((r-bl)<16)
road=gaussian_filter(road,0.8)
cost=1/(road+0.02)
ny,nx=cost.shape; idx=np.arange(nx*ny).reshape(ny,nx); R_=[];C_=[];V_=[]
for dj,di in [(0,1),(1,0),(1,1),(1,-1)]:
    js=slice(0,ny-dj); is_=slice(max(0,-di),nx-max(0,di)); jt=slice(dj,ny); it=slice(max(0,di),nx-max(0,-di))
    w=(cost[js,is_]+cost[jt,it])/2*np.hypot(dj,di)
    R_+= [idx[js,is_].ravel(),idx[jt,it].ravel()]; C_+=[idx[jt,it].ravel(),idx[js,is_].ravel()]; V_+=[w.ravel(),w.ravel()]
G=coo_matrix((np.concatenate(V_),(np.concatenate(R_),np.concatenate(C_))),shape=(nx*ny,nx*ny)).tocsr()
sc=json.load(open('scene.json')); B3=[l['p'] for l in sc['labels'] if l['id']=='B-3 Post'][0]
p0=px(*B3); p0=(int((p0[0]-a)*s),int((p0[1]-b)*s))
# snap B-3 to nearest strong road pixel within 40 px
jj,ii=np.mgrid[max(0,p0[1]-40):p0[1]+40, max(0,p0[0]-40):p0[0]+40]; k=np.argmax(road[jj,ii]); src=(jj.ravel()[k],ii.ravel()[k])
# west end: best road pixel on left edge column 3
col=road[:,3]; dst=(int(np.argmax(col)),3)
dist,pred=dijkstra(G,indices=src[0]*nx+src[1],return_predecessors=True)
t=dst[0]*nx+dst[1]; path=[t]
while path[-1]!=src[0]*nx+src[1]: path.append(pred[path[-1]])
J,I=np.unravel_index(path[::-1],(ny,nx))
# pixels -> local metres via inverse tile mapping
X=a+I/s; Y=b+J/s
lon=[]; lat=[]
for x,y in zip(X,Y):
    lo,la=tile_ll(M['x0']+x/256,M['y0']+y/256,17); lon.append(lo); lat.append(la)
E,N=en(np.array(lon),np.array(lat))
from scipy.ndimage import gaussian_filter1d
E=gaussian_filter1d(E,4); N=gaussian_filter1d(N,4)
json.dump({'E':E[::3].tolist(),'N':N[::3].tolist()},open('chw.json','w'))
print('chw pts',len(E), 'len km',np.hypot(np.diff(E),np.diff(N)).sum()/1000, 'mean roadness', road[J,I].mean())
from PIL import ImageDraw
vis=Image.fromarray(crop.astype(np.uint8)); dr=ImageDraw.Draw(vis); dr.line(list(zip(I,J)),fill=(255,0,0),width=2); vis.resize((vis.size[0]//2,vis.size[1]//2)).save('/home/user/recce/stills/chw.jpg')
