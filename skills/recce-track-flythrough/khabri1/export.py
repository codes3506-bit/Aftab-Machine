import json,csv,zipfile,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from geo import *
O='/home/user/Aftab-Machine/output'
M={t['name']:t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; PR=json.load(open(f'{R}/work/profiles.json'))
rows={r['name']:r for r in csv.DictReader(open(f'{O}/track_comparison.csv'))}
COL={'T1':'#8a8f98','T2':'#5b8def','T3':'#3fb8af','T4':'#c77dff','T5':'#f5b700'}
feats=[]
for tid,p in PR.items():
    a={k:v for k,v in rows[tid].items()}; a['id']=tid; a['status']='LCP-derived alignment (assessed) - not ground-verified'
    feats.append({'type':'Feature','properties':a,'geometry':{'type':'LineString','coordinates':[[round(x,6),round(y,6),round(z,1)] for (x,y),z in zip(p['ll'],p['z'])]}})
for p in kml():
    if p['kind']=='line': feats.append({'type':'Feature','properties':{'id':'KMZ','name':p['name'],'desc':p['desc'],'status':'from user KMZ'},'geometry':{'type':'LineString','coordinates':[list(q) for q in p['pts']]}})
feats.append({'type':'Feature','properties':{'id':'POST','name':'Khabri-1 hill post','RL_m':133,'DEM_m':143,'status':'location from previous brief'},'geometry':{'type':'Point','coordinates':[63.43978,25.42739]}})
json.dump({'type':'FeatureCollection','features':feats},open(f'{O}/tracks.geojson','w'),indent=0)
def kc(h,a='ff'): h=h.lstrip('#'); return a+h[4:6]+h[2:4]+h[0:2]
k=['<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Khabri-1 hill post - tracks T1-T5 (assessed)</name>']
for tid,c in COL.items(): k.append(f'<Style id="{tid}"><LineStyle><color>{kc(c)}</color><width>{6 if tid in("T4","T5") else 4}</width></LineStyle></Style>')
for f in feats:
    pr=f['properties']; g=f['geometry']
    if g['type']=='Point': k.append(f'<Placemark><name>{pr["name"]}</name><Point><coordinates>{g["coordinates"][0]},{g["coordinates"][1]},0</coordinates></Point></Placemark>'); continue
    desc=''.join(f'{kk}: {vv}<br/>' for kk,vv in pr.items() if kk not in('id',)) 
    sty=f'#{pr["id"]}' if pr['id'] in COL else ''
    nm=f'{pr["id"]} {pr.get("desc","")}' if pr['id'] in COL else pr['name']
    k.append(f'<Placemark><name>{nm}</name><description><![CDATA[{desc}]]></description><styleUrl>{sty}</styleUrl><LineString><tessellate>1</tessellate><coordinates>'+' '.join(f'{c[0]},{c[1]},0' for c in g['coordinates'])+'</coordinates></LineString></Placemark>')
k.append('</Document></kml>')
with zipfile.ZipFile(f'{O}/tracks.kmz','w',zipfile.ZIP_DEFLATED) as z: z.writestr('doc.kml','\n'.join(k))
# ---- terrain maps
W,E,S,N=63.424,63.458,25.412,25.438
G=np.load(f'{R}/work/grid.npz'); Z=G['Z']; ACC=G['ACC']; sl=G['slope']; x0,y0,st=float(G['x0']),float(G['y0']),float(G['st'])
ext=[*ll(x0,y0)][0],[*ll(x0+st*Z.shape[1],y0)][0][0] if False else None
lo0,la0=ll(x0,y0); lo1,la1=ll(x0+st*Z.shape[1],y0+st*Z.shape[0]); EXT=[float(lo0),float(lo1),float(la0),float(la1)]
m=Mos(17); px0,py0=m.px(W,N); px1,py1=m.px(E,S); img=m.im.crop((int(px0),int(py0),int(px1),int(py1)))
asp=1/np.cos(np.radians(25.42))
def base(title):
    fig,ax=plt.subplots(figsize=(14,11),facecolor='#0b1220'); ax.set_facecolor('#0b1220')
    ax.imshow(img,extent=[W,E,S,N],aspect=asp); ax.set_xlim(W,E); ax.set_ylim(S,N); ax.tick_params(colors='w'); ax.set_title(title,color='w',fontsize=15,weight='bold')
    # north arrow + scale bar (500 m)
    ax.annotate('N',xy=(E-0.0018,N-0.0015),xytext=(E-0.0018,N-0.0045),color='w',ha='center',fontsize=14,weight='bold',arrowprops=dict(color='w',width=3,headwidth=12))
    d=500/MLON; ax.plot([W+0.0015,W+0.0015+d],[S+0.0012]*2,color='w',lw=4); ax.text(W+0.0015+d/2,S+0.0018,'500 m',color='w',ha='center',weight='bold')
    return fig,ax
def tracks(ax,lw=2.5):
    for tid,p in PR.items():
        a=np.array(p['ll']); ax.plot(a[:,0],a[:,1],color='k',lw=lw+2.5,alpha=.6); ax.plot(a[:,0],a[:,1],color=COL[tid],lw=lw,label=f'{tid} {M[tid]["desc"]}')
    for p in kml():
        if p['kind']=='line': a=np.array(p['pts']); ax.plot(a[:,0],a[:,1],color='#ff8c00',lw=1.6,ls='--')
    ax.plot(63.43978,25.42739,'*',color='w',ms=20,mec='k'); ax.text(63.4400,25.4282,'KHABRI-1 HILL POST  RL 133',color='w',weight='bold',fontsize=10,bbox=dict(fc='#0b1220',ec='#f5b700',alpha=.85))
    ax.legend(loc='lower right',fontsize=9,facecolor='#0b1220',labelcolor='w',edgecolor='#445')
fig,ax=base('SLOPE (Cop GLO-30, 10 m resample) - deg'); cm=LinearSegmentedColormap.from_list('s',['#1a9850','#fee08b','#f46d43','#a50026'])
h=ax.imshow(np.ma.masked_less(sl,6),extent=EXT,origin='lower',cmap=cm,vmin=6,vmax=35,alpha=.55,aspect=asp); tracks(ax); c=plt.colorbar(h,ax=ax,shrink=.6); c.ax.tick_params(colors='w')
plt.savefig(f'{O}/terrain_maps/slope.png',dpi=110,facecolor='#0b1220'); plt.close()
fig,ax=base('DRAINAGE - D8 flow lines (catchment > 2 ha), nala xings'); A=np.ma.masked_less(ACC,2)
h=ax.imshow(np.log10(A),extent=EXT,origin='lower',cmap='Blues',vmin=0,vmax=3,alpha=.9,aspect=asp); tracks(ax); c=plt.colorbar(h,ax=ax,shrink=.6,label='log10 catchment ha'); c.ax.tick_params(colors='w')
plt.savefig(f'{O}/terrain_maps/drainage.png',dpi=110,facecolor='#0b1220'); plt.close()
fig,ax=base('EXPOSURE - track segs visible from dominating ground (red) / W-NW low ground (orange)  [assessed OPs]')
tracks(ax,1.5); MM=json.load(open(f'{R}/work/metrics.json'))
for tid,p in PR.items():
    a=np.array(p['ll']); vA=np.array(p['visA']); vB=np.array(p['visB'])
    ax.scatter(a[vB,0],a[vB,1],s=10,c='#ff9f1c',zorder=5); ax.scatter(a[vA,0],a[vA,1],s=10,c='#ff1e1e',zorder=6)
for oe,on,oz in MM['OPA']:
    lo,la=ll(oe,on); ax.plot(lo,la,'^',color='#ff1e1e',ms=9,mec='w')
for oe,on,oz in MM['OPB']:
    lo,la=ll(oe,on); ax.plot(lo,la,'s',color='#ff9f1c',ms=7,mec='w')
plt.savefig(f'{O}/terrain_maps/viewshed_exposure.png',dpi=110,facecolor='#0b1220'); plt.close()
# profiles
fig,ax=plt.subplots(figsize=(14,6),facecolor='#0b1220'); ax.set_facecolor('#0b1220')
for tid,p in PR.items(): ax.plot(np.array(p['s'])/1000,p['z'],color=COL[tid],lw=3 if tid in('T4','T5') else 1.8,label=f'{tid} {M[tid]["desc"]}  max {M[tid]["max_grade_pct"]:.0f}%')
ax.tick_params(colors='w'); ax.set_xlabel('km from junction',color='w'); ax.set_ylabel('elev m (GLO-30 DSM)',color='w'); ax.grid(alpha=.2); ax.legend(facecolor='#0b1220',labelcolor='w')
ax.set_title('ELEVATION PROFILES - junction to hill post',color='w',weight='bold'); plt.savefig(f'{O}/terrain_maps/profiles.png',dpi=110,facecolor='#0b1220')
print('ok',len(feats))
