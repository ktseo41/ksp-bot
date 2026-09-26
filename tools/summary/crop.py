from PIL import Image
import sys
SRC='./runs/craft-%s.png'
OUT='./docs/media/summary/crafts/%s.jpg'
ASPECT=0.552
WIDE={'mun-lander-4','mun-lander-7','sandbox-minmus-test','sandbox-lander-test','duna-1'}
# slug: (cx, top, bottom, craft_width) as fractions
C={
 'hopper-1':(0.472,0.30,0.645,0.10),
 'sounding-2':(0.50,0.22,0.76,0.05),
 'orbiter-1':(0.50,0.175,0.80,0.05),
 'minmus-flyby-1':(0.50,0.075,0.735,0.05),
 'minmus-lander-1':(0.50,0.05,0.735,0.08),
 'mun-lander-1':(0.50,0.03,0.72,0.08),
 'sounding-3':(0.50,0.186,0.75,0.05),
 'pad-lab':(0.497,0.305,0.68,0.10),
 'mun-lander-2':(0.50,0.03,0.72,0.08),
 'mun-lander-3':(0.50,0.078,0.75,0.08),
 'mun-lander-5':(0.50,0.078,0.75,0.08),
 'mun-lander-6':(0.50,0.078,0.75,0.08),
 'mun-lander-4':(0.50,0.078,0.75,0.08),
 'mun-lander-7':(0.50,0.078,0.75,0.08),
 'sandbox-minmus-test':(0.50,0.105,0.68,0.06),
 'sandbox-lander-test':(0.497,0.23,0.86,0.06),
 'duna-1':(0.50,0.084,0.775,0.08),
 'jool-1':(0.495,0.083,0.76,0.07),
 'ike-station-1':(0.495,0.065,0.75,0.075),
 'mun-tanker-1':(0.494,0.028,0.71,0.085),
 'rescue-2':(0.494,0.019,0.71,0.085),
 'salvage-1':(0.494,0.020,0.71,0.085),
 'salvage-2':(0.493,0.022,0.71,0.085),
}
W,H=2560,1440
for s,(cx,t,b,cw) in C.items():
    im=Image.open(SRC%s).convert('RGB')
    A=0.696 if s in WIDE else ASPECT
    h=(b-t)*H*1.12
    w=max(h*A, cw*W*2.2)
    h=w/A
    cy=(t+b)/2*H
    y0=cy-h/2; 
    y0=max(0,min(y0,H-h))
    x0=cx*W-w/2
    box=tuple(int(round(v)) for v in (x0,y0,x0+w,y0+h))
    c=im.crop(box)
    tw=min(480,c.width)
    c=c.resize((tw,int(tw/A)),Image.LANCZOS)
    c.save(OUT%s,quality=84,optimize=True,progressive=True)
    print(s,box,c.size)
