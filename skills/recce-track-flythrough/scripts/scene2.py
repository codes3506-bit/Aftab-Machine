import numpy as np,json
from scipy.ndimage import gaussian_filter1d
from geo import *
A=json.load(open('an_v1.json')); S1=json.load(open('scene.json'))
CH=np.array(A['CH']);E=np.array(A['E']);N=np.array(A['N']);Z=np.array(A['Z'])
TYP={'level':0,'cutfill':1,'nullah':2}
Zs=gaussian_filter1d(Z,2); g50=np.convolve(np.gradient(Zs,5.0),np.ones(10)/10,mode='same')
sc={'track':{'ch':CH.tolist(),'e':E.tolist(),'n':N.tolist(),'z':Z.tolist(),'typ':[TYP[t] for t in A['typ']],'g':g50.tolist()}}
C1=S1['track']; sc['ghost']={'e':C1['e'],'n':C1['n']}
labels=[l for l in S1['labels'] if l['kind'] in ('post','place','khor','road')]
for c in range(1,7):
    i=np.searchsorted(CH,c)
    if i<len(CH): labels.append({'id':f'CH {c}','p':[E[i],N[i]],'kind':'km','ch':float(c)})
# merged nullah xings
xs=sorted(A['xing']); groups=[]
for c,a,k in xs:
    if groups and c-groups[-1][-1][0]<0.15: groups[-1].append((c,a,k))
    else: groups.append([(c,a,k)])
nx=[]
for gr in groups:
    c,a,k=max(gr,key=lambda v:v[1])
    if 3.3<c<4.45: continue     # inside the nullah-bed run (shown as one stretch)
    nx.append((c,a,k)); labels.append({'id':f'NX{len(nx)}','p':[E[k],N[k]],'kind':'nx','ch':c,'med':a>1.0})
i=int(np.argmax(Z)); labels.append({'id':'Saddle','p':[E[i],N[i]],'kind':'crest','ch':float(CH[i]),'z':float(Z[i])})
j=np.searchsorted(CH,3.13); labels.append({'id':'Nullah bed','p':[E[j],N[j]],'kind':'crest','ch':3.13,'z':float(Z[j])})
k1=int(np.argmax(C1['z'])); labels.append({'id':'Opt 1 crest','p':[C1['e'][k1],C1['n'][k1]],'kind':'ghost','ch':-1,'z':float(C1['z'][k1])})
sc['labels']=labels; sc['hy']=[]; sc['crest_ch']=float(CH[i]); sc['nx']=[(c,a) for c,a,k in nx]
json.dump(sc,open('scene2.json','w'))
print('saddle',CH[i],Z[i],'nx',[(round(c,2),round(a,2)) for c,a,k in nx],'len',CH[-1])
