import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
from geo import *
m=Mos(18); L=[p for p in kml() if p['kind']=='line']; ex=np.array(L[0]['pts']); PR=json.load(open(f'{R}/work/profiles.json'))
COL={'T1':(154,160,170),'T2':(91,141,239),'T3':(63,184,175),'T4':(199,125,255),'T5':(245,183,0)}
idx=np.linspace(5,len(ex)-6,6).astype(int); samples=[('KMZ existing tr',ex[i]) for i in idx]+[(k,np.array(PR[k]['ll'])[len(PR[k]['ll'])//2]) for k in ('T2','T4','T5')]+[('T5 foothill',np.array(PR['T5']['ll'])[len(PR['T5']['ll'])//4])]
f=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf',22); tiles=[]
for nm,(lo,la) in samples:
    cx,cy=m.px(lo,la); box=(int(cx-200),int(cy-200),int(cx+200),int(cy+200)); im=m.im.crop(box).copy(); d=ImageDraw.Draw(im)
    for line,c in [(ex,(255,255,255))]+[(np.array(PR[k]['ll']),COL[k]) for k in PR]:
        q=[(m.px(a,b)[0]-box[0],m.px(a,b)[1]-box[1]) for a,b in line]; d.line(q,fill=c,width=2)
    d.text((8,8),nm,font=f,fill=(255,255,0),stroke_width=2,stroke_fill=(0,0,0)); d.text((8,370),'~240 m across',font=f,fill=(255,255,255),stroke_width=2,stroke_fill=(0,0,0)); tiles.append(im)
sh=Image.new('RGB',(2000,800))
for i,t in enumerate(tiles): sh.paste(t,((i%5)*400,(i//5)*400))
sh.save('/home/user/Aftab-Machine/output/terrain_maps/qa_overlay_check.jpg',quality=88)
