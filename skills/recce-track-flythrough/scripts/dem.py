import tifffile,numpy as np,json
from scipy.ndimage import map_coordinates
from geo import *
a=tifffile.imread(f'{R}/tiles/cop_N25E065.tif').astype(np.float32)
print(a.shape,a.min(),a.max())
H,W=a.shape  # 3600x3600 covering lat 25-26 lon 65-66, pixel-centre convention
def dem_at(lon,lat):
    c=(np.asarray(lon)-65.0)*W-0.5+0.5; r=(26.0-np.asarray(lat))*H-0.5+0.5
    return map_coordinates(a,[r,c],order=3,mode='nearest')
d=json.load(open(f'{R}/sera.json')); t=np.array(d['track'])
z=dem_at(t[:,0],t[:,1]); e,n=en(t[:,0],t[:,1])
s=np.r_[0,np.cumsum(np.hypot(np.diff(e),np.diff(n)))]
print('len',s[-1]); print('B3',z[0],'Haryan',z[-1],'max',z.max(),'at',s[z.argmax()],'min',z.min())
k=9.0/ (s[-1]/1000)
for ch in np.arange(0,9.01,0.5):
    i=np.searchsorted(s/1000*k,ch); i=min(i,len(z)-1); print(f'{ch:4.1f} {z[i]:6.1f}')
np.save(f'{R}/work/dem_full.npy',a)
