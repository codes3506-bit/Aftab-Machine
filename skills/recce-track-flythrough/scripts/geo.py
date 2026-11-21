import math,glob,os,numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
R='/home/user/recce'
LAT0,LON0=25.4746,65.1930   # local origin (centre of track)
MLAT=110950.0; MLON=111320*math.cos(math.radians(LAT0))
def en(lon,lat): return (np.asarray(lon)-LON0)*MLON,(np.asarray(lat)-LAT0)*MLAT
def ll(e,n): return LON0+np.asarray(e)/MLON, LAT0+np.asarray(n)/MLAT
def tile_xy(lon,lat,z):
    n=2**z; x=(lon+180)/360*n; y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n; return x,y
def tile_ll(x,y,z):
    n=2**z; lon=x/n*360-180; lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n)))); return lon,lat
def mosaic(z):
    fs=glob.glob(f'{R}/tiles/z{z}/*.jpg'); xy=[tuple(map(int,os.path.basename(f)[:-4].split('_')[1:])) for f in fs]
    xs=[a for a,b in xy]; ys=[b for a,b in xy]; x0,y0=min(xs),min(ys); W=(max(xs)-x0+1)*256; H=(max(ys)-y0+1)*256
    im=Image.new('RGB',(W,H))
    for f,(x,y) in zip(fs,xy):
        try: im.paste(Image.open(f).convert('RGB'),((x-x0)*256,(y-y0)*256))
        except Exception: pass
    return im,x0,y0
