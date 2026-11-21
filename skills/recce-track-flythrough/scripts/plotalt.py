import numpy as np,json,sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from geo import *
M=json.load(open('meta.json')); hm=np.load('hm.npy'); H=M['hm']
import os
x0,x1,y0,y1=[float(v) for v in os.environ.get("WIN","-5500,4000,-3200,3200").split(",")]
i0=int((x0-H['x0'])/6); i1=int((x1-H['x0'])/6); j0=int((y0-H['y0'])/6); j1=int((y1-H['y0'])/6)
z=hm[j0:j1,i0:i1]; gy,gx=np.gradient(z,6); sl=np.hypot(gx,gy)*100
fig=plt.figure(figsize=(15.8,10.7),dpi=100); ax=fig.add_axes([0,0,1,1])
ax.imshow(np.clip(sl,0,60),origin='lower',extent=[x0,x1,y0,y1],cmap='magma_r',vmin=0,vmax=60,alpha=0.85)
cs=ax.contour(np.linspace(x0,x1,z.shape[1]),np.linspace(y0,y1,z.shape[0]),z,levels=np.arange(50,500,25),colors='k',linewidths=0.35,alpha=0.6)
acc=np.load('acc.npy'); g=json.load(open('alt_raw.json'))['grid']
ax.contour(g[0]+(np.arange(acc.shape[1])+.5)*g[2], g[1]+(np.arange(acc.shape[0])+.5)*g[2], acc, levels=[0.5], colors='cyan', linewidths=0.6)
A=json.load(open('analysis.json')); ax.plot(A['E'],A['N'],color='blue',lw=3,label='Current')
for f,c in zip(sys.argv[1:],['lime','yellow','orange']):
    d=json.load(open(f)); ax.plot(d['E'],d['N'],color=c,lw=3,label=f)
sc=json.load(open('scene.json'))
for l in sc['labels']:
    if l['kind'] in ('post','km','place','khor'): ax.text(*l['p'],l['id'],fontsize=9,weight='bold',color='w',bbox=dict(fc='k',alpha=.5,pad=1))
ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.legend(loc='lower left'); ax.grid(alpha=.3)
fig.savefig('/home/user/recce/stills/alt.png',dpi=100)
