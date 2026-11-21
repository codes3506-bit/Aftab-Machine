import numpy as np,json
from scipy.ndimage import map_coordinates
from geo import *
W_,E_,S_,N_=65.085,65.262,25.425,25.520
meta={'dom':[W_,E_,S_,N_]}
for z in (16,17,18):
    im,x0,y0=mosaic(z); w,h=im.size
    lonW,latN=tile_ll(x0,y0,z); lonE,latS=tile_ll(x0+w/256,y0+h/256,z)
    im.save(f'{R}/work/tex{z}.png',compress_level=1)
    meta[f'z{z}']={'x0':x0,'y0':y0,'w':w,'h':h,'lonW':lonW,'lonE':lonE,'latN':latN,'latS':latS}
    print(z,w,h,lonW,lonE,latS,latN)
a=np.load(f'{R}/work/dem_full.npy'); H,W=a.shape
x0,y0=en(W_,S_); x1,y1=en(E_,N_); step=6.0
xs=np.arange(x0,x1,step); ys=np.arange(y0,y1,step)
X,Y=np.meshgrid(xs,ys); lo,la=ll(X,Y)
hm=map_coordinates(a,[(26.0-la)*H-0.5,(lo-65.0)*W-0.5],order=3,mode='nearest').astype(np.float32)
np.save(f'{R}/work/hm.npy',hm); meta['hm']={'x0':float(x0),'y0':float(y0),'step':step,'nx':len(xs),'ny':len(ys),'min':float(hm.min()),'max':float(hm.max())}
json.dump(meta,open(f'{R}/work/meta.json','w'),indent=1); print(meta['hm'])
