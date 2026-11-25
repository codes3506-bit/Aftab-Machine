import sys; from geo import *; from PIL import ImageDraw,ImageFont
z=int(sys.argv[1]); W,E,S,N=map(float,sys.argv[2:6]); out=sys.argv[6]
m=Mos(z); x0,y0=m.px(W,N); x1,y1=m.px(E,S); im=m.im.crop((int(x0),int(y0),int(x1),int(y1))).copy(); d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',max(14,int(im.width/90)))
col={'line':[(255,176,0),(255,32,32),(0,255,255)]}; i=0
for p in kml():
    q=[(m.px(*a)[0]-x0,m.px(*a)[1]-y0) for a in p['pts']]
    if p['kind']=='line': d.line(q,fill=col['line'][i%3],width=4); i+=1
    elif p['kind']=='poly': d.polygon(q,outline=(255,255,255))
    else: d.ellipse((q[0][0]-6,q[0][1]-6,q[0][0]+6,q[0][1]+6),outline=(255,255,255),width=3); d.text((q[0][0]+8,q[0][1]-8),p['name'][:24],fill=(255,255,255),font=f,stroke_width=2,stroke_fill=(0,0,0))
# grid ticks every 0.005 deg
import numpy as np
for lo in np.arange(round(W,3),E,0.005):
    x=m.px(lo,N)[0]-x0; d.line([(x,0),(x,12)],fill=(255,255,0),width=2); d.text((x+2,14),f'{lo:.3f}',fill=(255,255,0),font=f,stroke_width=2,stroke_fill=(0,0,0))
for la in np.arange(round(S,3),N,0.005):
    y=m.px(W,la)[1]-y0; d.line([(0,y),(12,y)],fill=(255,255,0),width=2); d.text((14,y-8),f'{la:.3f}',fill=(255,255,0),font=f,stroke_width=2,stroke_fill=(0,0,0))
im.save(out,quality=88); print(im.size)
