import math,os,sys,urllib.request,concurrent.futures as cf
def t(lon,lat,z):
    n=2**z; x=(lon+180)/360*n; y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n; return x,y
def job(z,W,E_,S,N,d):
    x0,y1=t(W,S,z); x1,y0=t(E_,N,z)
    xs=range(int(x0),int(x1)+1); ys=range(int(y0),int(y1)+1)
    os.makedirs(d,exist_ok=True)
    def get(xy):
        x,y=xy; f=f'{d}/{z}_{x}_{y}.jpg'
        if os.path.exists(f) and os.path.getsize(f)>0: return
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        for k in range(4):
            try:
                r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'terrain-render/1.0'}),timeout=30).read(); open(f,'wb').write(r); return
            except Exception as e: err=e
        print('fail',xy,err)
    with cf.ThreadPoolExecutor(12) as ex: list(ex.map(get,[(x,y) for x in xs for y in ys]))
    print(z,len(xs),len(ys),xs[0],ys[0])
# wide area z16 (includes Keisher..B-1), mid z17, detail z18 round track
job(16,65.04,65.30,25.40,25.56,'/home/user/recce/tiles/z16')
job(17,65.10,65.26,25.43,25.52,'/home/user/recce/tiles/z17')
job(18,65.160,65.226,25.455,25.493,'/home/user/recce/tiles/z18')
