import json,sys,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from geo import *
d=json.load(open(f'{R}/work/lcp.json')); W,E,S,N=63.426,63.456,25.414,25.437
m=Mos(17); x0,y0=m.px(W,N); x1,y1=m.px(E,S); im=m.im.crop((int(x0),int(y0),int(x1),int(y1)))
lo=np.linspace(W,E,500); la=np.linspace(N,S,400); LO,LA=np.meshgrid(lo,la); Z=dem(LO,LA)
fig,ax=plt.subplots(figsize=(16,12.5)); ax.imshow(im,extent=[W,E,S,N],aspect=1/np.cos(np.radians(25.42)))
cs=ax.contour(LO,LA,Z,levels=np.arange(20,400,20),colors='w',linewidths=.4,alpha=.6); ax.clabel(cs,fontsize=6,fmt='%d')
for p in kml():
    a=np.array(p['pts'])
    if p['kind']=='line': ax.plot(a[:,0],a[:,1],color='orange',lw=2)
cols=dict(zip(d.keys(),['w','tab:red','tab:cyan','gold','tab:green','m','k']))
for k,v in d.items():
    if v: a=np.array(v['ll']); ax.plot(a[:,0],a[:,1],color=cols[k],lw=2.2,label=f"{k} cost {v['cost']:.0f}")
ax.plot(63.43978,25.42739,'w*',ms=18,mec='k'); ax.legend(loc='lower right',fontsize=9); ax.set_xlim(W,E); ax.set_ylim(S,N)
plt.savefig(sys.argv[1],dpi=90,bbox_inches='tight')
