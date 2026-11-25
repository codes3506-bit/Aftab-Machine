from geo import *; import numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter
W,E,S,N=63.405,63.465,25.395,25.445
lo=np.linspace(W,E,800); la=np.linspace(N,S,700); LO,LA=np.meshgrid(lo,la); Z=dem(LO,LA)
dx=(lo[1]-lo[0])*MLON; dy=(la[0]-la[1])*MLAT
gy,gx=np.gradient(Z,dy,dx); sl=np.degrees(np.arctan(np.hypot(gx,gy)))
hs=np.clip(np.cos(np.radians(45))*np.cos(np.arctan(np.hypot(gx,gy)))+np.sin(np.radians(45))*np.sin(np.arctan(np.hypot(gx,gy)))*np.cos(np.radians(315)-np.arctan2(gx,gy)),0,1)
fig,ax=plt.subplots(figsize=(16,14)); ax.imshow(hs,cmap='gray',extent=[W,E,S,N],aspect=1/np.cos(np.radians(25.4)))
cs=ax.contour(LO,LA,Z,levels=np.arange(0,400,20),colors='orange',linewidths=.5,origin='upper'); ax.clabel(cs,fontsize=7,fmt='%d')
for p in kml():
    a=np.array(p['pts'])
    if p['kind']=='line': ax.plot(a[:,0],a[:,1],lw=2.5)
    elif p['kind']=='point': ax.plot(*a[0],'wo'); ax.text(a[0,0],a[0,1],' '+p['name'][:20],color='w',fontsize=8)
    else: ax.plot(*a[0],'c*',ms=15)
pk=(Z==maximum_filter(Z,size=60))&(Z>60)
for i,j in zip(*np.where(pk)): ax.plot(lo[j],la[i],'r^'); ax.text(lo[j],la[i],f' {Z[i,j]:.0f}',color='r',fontsize=9,weight='bold'); print('peak',round(lo[j],4),round(la[i],4),round(Z[i,j]))
ax.grid(alpha=.3); plt.savefig('/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/scratchpad/hs.png',dpi=100,bbox_inches='tight')
