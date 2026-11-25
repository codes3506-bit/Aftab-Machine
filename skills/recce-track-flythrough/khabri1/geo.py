import math,glob,os,json,re,numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
R='/home/user/khabri'
LAT0,LON0=25.415,63.435
MLAT=110850.0; MLON=111320*math.cos(math.radians(LAT0))
def en(lon,lat): return (np.asarray(lon)-LON0)*MLON,(np.asarray(lat)-LAT0)*MLAT
def ll(e,n): return LON0+np.asarray(e)/MLON, LAT0+np.asarray(n)/MLAT
def tile_xy(lon,lat,z):
    n=2**z; return (lon+180)/360*n,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
def tile_ll(x,y,z):
    n=2**z; return x/n*360-180, math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))))
def mosaic(z):
    fs=glob.glob(f'{R}/tiles/z{z}/*.jpg'); xy=[tuple(map(int,os.path.basename(f)[:-4].split('_')[1:])) for f in fs]
    x0=min(a for a,b in xy); y0=min(b for a,b in xy); W=(max(a for a,b in xy)-x0+1)*256; H=(max(b for a,b in xy)-y0+1)*256
    im=Image.new('RGB',(W,H))
    for f,(x,y) in zip(fs,xy):
        try: im.paste(Image.open(f).convert('RGB'),((x-x0)*256,(y-y0)*256))
        except Exception: pass
    return im,x0,y0
class Mos:
    def __init__(s,z):
        s.z=z; s.im,s.x0,s.y0=mosaic(z)
    def px(s,lon,lat):
        x,y=tile_xy(lon,lat,s.z); return (x-s.x0)*256,(y-s.y0)*256
    def lonlat(s,px,py): return tile_ll(s.x0+px/256,s.y0+py/256,s.z)
DEMA=None
def dem(lon,lat):
    global DEMA
    from scipy.ndimage import map_coordinates
    if DEMA is None:
        import tifffile; DEMA=tifffile.imread(f'{R}/tiles/cop_N25E063.tif').astype(np.float32)
    H,W=DEMA.shape
    return map_coordinates(DEMA,[(26.0-np.asarray(lat))*H-0.5,(np.asarray(lon)-63.0)*W-0.5],order=3,mode='nearest')
def kml():
    s=open('/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/scratchpad/kmz/doc.kml').read()
    out=[]
    for pm in re.findall(r'<Placemark>(.*?)</Placemark>',s,re.S):
        nm=re.search(r'<name>(.*?)</name>',pm).group(1); de=(re.search(r'<description>(.*?)</description>',pm,re.S) or [None,''])[1]
        c=re.search(r'<coordinates>(.*?)</coordinates>',pm,re.S).group(1).split()
        pts=[tuple(map(float,p.split(',')[:2])) for p in c]
        kind='line' if '<LineString>' in pm else ('poly' if '<Polygon>' in pm else 'point')
        out.append({'name':nm,'desc':de,'kind':kind,'pts':pts})
    return out
