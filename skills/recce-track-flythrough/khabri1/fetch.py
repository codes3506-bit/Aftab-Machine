import math,os,urllib.request,concurrent.futures as cf
R='/home/user/khabri'
def t(lon,lat,z):
    n=2**z; return (lon+180)/360*n,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
def job(z,W,E_,S,N,d):
    x0,y1=t(W,S,z); x1,y0=t(E_,N,z); xs=range(int(x0),int(x1)+1); ys=range(int(y0),int(y1)+1); os.makedirs(d,exist_ok=True); bad=[]
    def get(xy):
        x,y=xy; f=f'{d}/{z}_{x}_{y}.jpg'
        if os.path.exists(f) and os.path.getsize(f)>0: return
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        for k in range(4):
            try: open(f,'wb').write(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'terrain-render/1.0'}),timeout=30).read()); return
            except Exception as e: err=e
        bad.append((xy,str(err)))
    with cf.ThreadPoolExecutor(12) as ex: list(ex.map(get,[(x,y) for x in xs for y in ys]))
    print(z,len(xs),len(ys),'fail',len(bad),bad[:2])
if __name__=='__main__':
    job(16,63.36,63.51,25.35,25.48,f'{R}/tiles/z16')
    job(17,63.395,63.475,25.38,25.45,f'{R}/tiles/z17')
    job(18,63.410,63.460,25.392,25.438,f'{R}/tiles/z18')
