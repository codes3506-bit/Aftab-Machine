import numpy as np,json
from scipy.ndimage import gaussian_filter1d
from geo import *
A=json.load(open(f'{R}/work/analysis.json')); d=json.load(open(f'{R}/sera.json')); s2=json.load(open(f'{R}/work/slide2_geo.json'))
CH=np.array(A['CH']);E=np.array(A['E']);N=np.array(A['N']);Z=np.array(A['Z']);g=np.array(A['g'])
TYP={'level':0,'cutfill':1,'nullah':2}
typ=[TYP[t] for t in A['typ']]
# 50 m grade for display
k=5; Zs=gaussian_filter1d(Z,2); g50=np.gradient(Zs,5.0)
g50=np.convolve(g50,np.ones(10)/10,mode='same')
sc={'track':{'ch':CH.tolist(),'e':E.tolist(),'n':N.tolist(),'z':Z.tolist(),'typ':typ,'g':g50.tolist()}}
def pt(lon,lat): e,n=en(lon,lat); return [float(e),float(n)]
labels=[]
for nm,key in [('B-3 Post','B-3 Post'),('Haryan BOO','Haryan VP')]:
    labels.append({'id':nm,'p':pt(*d[key][:2]),'kind':'post'})
for nm in ['B-1','B5','Keisher','Darband']:
    labels.append({'id':nm,'p':pt(*s2['pts'][nm]),'kind':'place'})
for nm in ['Maneji K','Haryan K','Hatti K']:
    labels.append({'id':nm,'p':pt(*s2['pts'][nm]),'kind':'khor'})
labels.append({'id':'CHW (N10)','p':pt(*s2['pts']['CHW']),'kind':'road'})
for c,p in d['ch']:
    if abs(c-round(c))<1e-6: labels.append({'id':f'Ch {int(round(c))}','p':pt(*p[:2]),'kind':'km','ch':c})
for nm,p in d['nullahs']:
    c=float(nm.split('Ch ')[1]); labels.append({'id':nm.replace('nullah','N xing'),'p':pt(*p[:2]),'kind':'nx','ch':c,'med':nm.startswith('Medium')})
i=int(np.argmax(Z)); labels.append({'id':'Ridge crest','p':[E[i],N[i]],'kind':'crest','ch':CH[i],'z':Z[i]})
sc['labels']=labels
sc['hy']=[[pt(p[0],p[1]) for p in poly] for poly in d['hy']]
sc['crest_ch']=float(CH[i])
json.dump(sc,open(f'{R}/work/scene.json','w'))
print(len(labels),'crest',CH[i],Z[i])
