import cv2,numpy as np,json
from geo import *
im,x0,y0=mosaic(16); big=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2GRAY)
sl=cv2.imread(f'{R}/photos/img02.webp',0)[125:1090,15:1975]
clahe=cv2.createCLAHE(2.0,(8,8)); g1=clahe.apply(sl)
sift=cv2.SIFT_create(30000); k1,d1=sift.detectAndCompute(g1,None)
best=None
for f in [0.25,0.3,0.36,0.45]:
    g2=clahe.apply(cv2.resize(big,None,fx=f,fy=f,interpolation=cv2.INTER_AREA))
    k2,d2=sift.detectAndCompute(g2,None)
    m=cv2.BFMatcher().knnMatch(d1,d2,k=2); good=[a for a,b in m if a.distance<0.8*b.distance]
    p1=np.float32([k1[a.queryIdx].pt for a in good]); p2=np.float32([k2[a.trainIdx].pt for a in good])/f
    A,mask=cv2.estimateAffinePartial2D(p1,p2,method=cv2.RANSAC,ransacReprojThreshold=12/f*0.33,maxIters=20000)
    n=int(mask.sum()); s=np.hypot(A[0,0],A[1,0]); print(f,len(good),n,'scale',s,'rot',np.degrees(np.arctan2(A[1,0],A[0,0])))
    if best is None or n>best[0]: best=(n,A)
n,A=best
def s2ll(px,py):
    q=A@np.array([px-15,py-125,1.0]); return [float(v) for v in tile_ll(x0+q[0]/256,y0+q[1]/256,16)]
pts={'Haryan':(988,757),'B-3':(1385,1025),'B-1':(1763,1066),'B5':(160,990),'Keisher':(236,820),'Darband':(392,462),
 'Maneji K':(115,718),'Haryan K':(1305,683),'Hatti K':(1210,355),'CHW':(908,983),'Altn':(1560,830),'NineKm':(1640,845)}
out={k:s2ll(*v) for k,v in pts.items()}
for k,v in out.items(): print(k,'%.5f %.5f'%tuple(v))
json.dump({'A':A.tolist(),'pts':out,'inl':n},open(f'{R}/work/slide2_geo.json','w'))
