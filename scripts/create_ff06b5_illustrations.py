#!/usr/bin/env python3
"""Create ten original, scene-specific cyberpunk illustrations for FF:06:B5.
These are original editorial recreations, not screenshots or official game assets.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets/images/ff06b5"
W,H=1920,1080
random.seed(6065)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def f(sz,b=False):
    p=BOLD if b else FONT
    try:return ImageFont.truetype(p,sz)
    except:return ImageFont.load_default()

def base(label,seed):
    random.seed(seed)
    im=Image.new("RGB",(W,H),(5,10,22)); px=im.load()
    for y in range(H):
        t=y/H
        c=(int(5+9*t),int(12+9*t),int(27+16*t))
        for x in range(W): px[x,y]=c
    d=ImageDraw.Draw(im,"RGBA")
    # distant neon skyline
    x=0
    while x<W:
        bw=random.randint(65,155); bh=random.randint(180,570)
        d.rectangle((x,H-180-bh,x+bw,H-180),fill=(8,22,40,255),outline=(30,105,130,150),width=3)
        for wy in range(H-160-bh,H-200,42):
            for wx in range(x+12,x+bw-8,25):
                if random.random()>.35:d.rectangle((wx,wy,wx+8,wy+13),fill=(45,190,205,130))
        x+=bw+random.randint(8,24)
    # horizon and wet street
    d.rectangle((0,H-180,W,H),fill=(4,9,20,255))
    for k in range(28):
        xx=random.randint(0,W); yy=random.randint(H-160,H-12)
        d.line((xx,yy,xx+random.randint(20,170),yy),fill=(random.choice([(30,180,205,70),(190,40,145,75)])),width=random.randint(2,7))
    # corner frame
    d.rounded_rectangle((38,35,W-38,H-35),radius=24,outline=(65,190,215,105),width=3)
    d.text((75,65),label.upper(),font=f(25,True),fill=(130,230,240,230))
    return im

def glow_line(d,pts,fill=(255,50,180,255),w=10):
    d.line(pts,fill=(*fill[:3],70),width=w*5,joint="curve")
    d.line(pts,fill=fill,width=w,joint="curve")

def statue(im):
    d=ImageDraw.Draw(im,"RGBA")
    # monumental pedestal
    d.polygon([(650,850),(1270,850),(1190,970),(730,970)],fill=(18,32,48,255),outline=(70,200,220,255))
    d.text((800,885),"FF:06:B5",font=f(58,True),fill=(255,65,190,255))
    # orb/head
    d.ellipse((825,180,1095,450),fill=(18,34,50,255),outline=(130,225,235,255),width=12)
    d.ellipse((895,250,1025,380),outline=(255,45,180,255),width=9)
    # body + six arms
    glow_line(d,[(960,445),(960,770)],(150,220,230,255),24)
    for pts in [[(950,520),(700,390),(590,230)],[(970,520),(1210,390),(1330,230)],[(950,600),(680,650),(540,790)],[(970,600),(1240,650),(1380,790)]]:
        glow_line(d,pts,(110,205,220,255),17)
    glow_line(d,[(930,755),(820,850)],(170,220,230,255),20);glow_line(d,[(990,755),(1100,850)],(170,220,230,255),20)
    d.line((960,165,960,95),fill=(255,60,190,255),width=7)
    d.ellipse((930,65,990,125),outline=(255,60,190,255),width=7)

def monks(im):
    d=ImageDraw.Draw(im,"RGBA")
    # statue smaller behind
    statue(im); d=ImageDraw.Draw(im,"RGBA")
    for x in (350,1510):
        d.ellipse((x-48,420,x+48,516),fill=(8,12,22,255),outline=(120,200,215,180),width=5)
        d.polygon([(x-85,530),(x+85,530),(x+145,900),(x-145,900)],fill=(12,20,34,255),outline=(70,190,205,190))
        d.line((x-25,650,x+20,650),fill=(240,190,130,180),width=8)
    d.text((670,180),"OBSERVAR  •  MEDITAR  •  DESCIFRAR",font=f(32,True),fill=(235,220,245,240))

def ouroboros(im):
    d=ImageDraw.Draw(im,"RGBA")
    # ruined stone arch
    d.polygon([(300,900),(360,330),(560,180),(1360,180),(1560,330),(1620,900)],fill=(15,25,38,255),outline=(80,150,165,255))
    d.arc((570,250,1350,900),180,540,fill=(255,50,185,255),width=26)
    # serpent head
    d.polygon([(930,260),(1080,300),(1010,390),(900,355)],fill=(255,60,185,255))
    d.ellipse((1000,300,1025,325),fill=(255,255,255,255))
    d.text((650,930),"OUROBOROS  /  EL CICLO",font=f(42,True),fill=(210,230,240,255))

def church(im):
    d=ImageDraw.Draw(im,"RGBA")
    d.polygon([(380,820),(520,390),(960,160),(1400,390),(1540,820)],fill=(9,22,38,255),outline=(70,205,220,255))
    d.rectangle((470,700,1450,900),fill=(10,20,35,255),outline=(70,205,220,255),width=6)
    d.rectangle((830,580,1090,900),fill=(5,12,25,255),outline=(255,50,185,220),width=6)
    # server racks
    for x in (520,650,1180,1310):
        d.rounded_rectangle((x,560,x+95,850),radius=8,fill=(12,30,48,255),outline=(70,220,235,255),width=5)
        for y in range(590,820,55):
            d.rectangle((x+15,y,x+80,y+35),outline=(110,220,235,220),width=3)
            d.ellipse((x+25,y+12,x+38,y+25),fill=(255,50,180,255))
    # laptop foreground
    d.rounded_rectangle((790,760,1130,925),radius=14,fill=(10,20,34,255),outline=(255,60,185,255),width=6)
    d.rectangle((820,785,1100,880),fill=(15,45,62,255))
    d.text((840,810),"POLYHISTOR",font=f(26,True),fill=(150,245,245,255))

def arcade(im):
    d=ImageDraw.Draw(im,"RGBA")
    # arcade cabinet
    d.polygon([(610,180),(1290,180),(1370,900),(550,900)],fill=(10,16,30,255),outline=(255,50,185,255))
    d.rounded_rectangle((675,260,1225,640),radius=20,fill=(3,8,18,255),outline=(90,220,240,255),width=9)
    # pixel tower scene in screen
    for x,bh in [(720,170),(810,230),(930,140),(1050,260),(1140,190)]:
        d.rectangle((x,590-bh,x+70,590),fill=(12,40,62,255),outline=(60,200,220,255),width=3)
    d.text((760,330),"ARASAKA",font=f(62,True),fill=(255,65,185,255))
    d.text((790,420),"TOWER 3D",font=f(55,True),fill=(170,240,245,255))
    d.ellipse((800,700,900,800),outline=(100,220,235,255),width=12)
    d.ellipse((1030,700,1130,800),outline=(255,60,185,255),width=12)
    d.line((960,680,960,820),fill=(120,220,230,255),width=10)

def maze(im):
    d=ImageDraw.Draw(im,"RGBA")
    # perspective corridor
    d.polygon([(0,0),(700,300),(700,850),(0,1080)],fill=(7,18,32,255),outline=(40,160,185,255))
    d.polygon([(1920,0),(1220,300),(1220,850),(1920,1080)],fill=(7,18,32,255),outline=(40,160,185,255))
    d.polygon([(700,300),(1220,300),(1920,0),(0,0)],fill=(12,24,40,255),outline=(60,190,210,255))
    d.polygon([(700,850),(1220,850),(1920,1080),(0,1080)],fill=(10,15,28,255),outline=(60,190,210,255))
    # maze grid map overlay
    ox,oy=790,385
    for i in range(5):
        d.line((ox+i*75,oy,ox+i*75,oy+300),fill=(75,210,225,220),width=8)
    for j in range(5):
        d.line((ox,oy+j*75,ox+300,oy+j*75),fill=(75,210,225,220),width=8)
    d.line((ox+35,oy+260,ox+35,oy+185,ox+110,oy+185,ox+110,oy+35,ox+260,oy+35),fill=(255,55,185,255),width=14)
    d.text((830,735),"PISO -10  /  RUTA OCULTA",font=f(32,True),fill=(255,90,200,255))

def dump_laptop(im):
    d=ImageDraw.Draw(im,"RGBA")
    # landfill silhouettes
    for pts in [[(0,850),(280,450),(520,850)],[(350,900),(700,390),(990,900)],[(1100,900),(1450,440),(1760,900)]]:
        d.polygon(pts,fill=(30,38,48,255),outline=(90,130,145,220))
    # laptop
    d.rounded_rectangle((600,350,1320,790),radius=25,fill=(8,16,28,255),outline=(85,220,230,255),width=10)
    d.rectangle((650,400,1270,700),fill=(13,32,50,255))
    d.arc((780,450,1130,680),0,350,fill=(255,50,185,255),width=16)
    d.polygon([(1050,450),(1170,485),(1110,560),(1010,535)],fill=(255,50,185,255))
    d.text((780,620),"00255  00006  00181",font=f(31,True),fill=(180,240,245,255))
    d.polygon([(520,800),(1400,800),(1280,880),(650,880)],fill=(15,28,42,255),outline=(90,220,230,255))

def badlands(im):
    d=ImageDraw.Draw(im,"RGBA")
    d.ellipse((1390,180,1600,390),fill=(255,150,90,70),outline=(255,170,110,200),width=5)
    d.polygon([(0,800),(250,500),(510,760),(820,390),(1130,780),(1450,480),(1920,820),(1920,1080),(0,1080)],fill=(45,37,38,255),outline=(185,110,90,190))
    # mattress
    d.polygon([(420,740),(1050,740),(1170,860),(510,860)],fill=(170,180,185,255),outline=(255,70,185,255),width=7)
    d.line((480,790,1090,790),fill=(90,110,125,255),width=7)
    # truck
    d.rectangle((1240,670,1660,820),fill=(20,35,48,255),outline=(80,220,230,255),width=7)
    d.rectangle((1450,570,1600,680),fill=(20,35,48,255),outline=(80,220,230,255),width=7)
    for x in (1320,1570):d.ellipse((x-65,780,x+65,910),fill=(5,10,18,255),outline=(255,60,185,255),width=10)

def cube(im):
    d=ImageDraw.Draw(im,"RGBA")
    # shadowy figure
    d.ellipse((380,300,540,460),fill=(5,12,25,255),outline=(90,200,220,180),width=5)
    d.polygon([(330,480),(590,480),(700,930),(220,930)],fill=(8,18,32,255),outline=(80,180,205,190))
    # floating cube
    d.polygon([(1120,250),(1390,400),(1120,550),(850,400)],fill=(22,55,75,245),outline=(255,55,185,255))
    d.polygon([(850,400),(1120,550),(1120,850),(850,700)],fill=(12,30,48,255),outline=(90,220,235,255))
    d.polygon([(1120,550),(1390,400),(1390,700),(1120,850)],fill=(16,42,62,255),outline=(90,220,235,255))
    glow_line(d,[(1120,250),(1120,850)],(255,60,185,255),5)
    d.text((880,920),"¿PISTA, SIMBOLO O METÁFORA?",font=f(34,True),fill=(220,235,245,255))

def city(im):
    d=ImageDraw.Draw(im,"RGBA")
    # giant skyline, magenta beam to statue silhouette
    d.polygon([(850,950),(960,260),(1070,950)],fill=(10,25,42,255),outline=(70,200,220,255))
    d.ellipse((900,170,1020,290),outline=(255,55,185,255),width=10)
    glow_line(d,[(960,160),(960,40)],(255,60,185,255),6)
    d.text((620,820),"NIGHT CITY",font=f(78,True),fill=(220,245,250,255))
    d.text((640,910),"UN MISTERIO, MUCHAS PISTAS",font=f(30,True),fill=(255,80,195,255))

SCENES=[
 ("01 · CORPO PLAZA / FF:06:B5",statue),
 ("02 · LOS MONJES Y LAS PRIMERAS PISTAS",monks),
 ("03 · THE WITCHER 3 / OUROBOROS",ouroboros),
 ("04 · IGLESIA DE BIOTECHNICA / SERVIDORES",church),
 ("05 · ARASAKA TOWER 3D / SALAS SECRETAS",arcade),
 ("06 · LABERINTO DEL PISO -10",maze),
 ("07 · EL PORTÁTIL DEL VERTEDERO",dump_laptop),
 ("08 · BADLANDS / POLYHISTOR Y EL CAMIÓN",badlands),
 ("09 · EL CUBO Y EL DESTINO DE POLYHISTOR",cube),
 ("10 · NIGHT CITY / EL MISTERIO CONTINÚA",city),
]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for i,(label,draw_scene) in enumerate(SCENES,1):
        im=base(label,i*31); draw_scene(im)
        # subtle vignette and grain-free clean illustration finish
        vign=Image.new("L",(W,H),0); vd=ImageDraw.Draw(vign)
        vd.ellipse((-250,-250,W+250,H+250),fill=210)
        vign=vign.filter(ImageFilter.GaussianBlur(120))
        shade=Image.new("RGB",(W,H),(0,0,0))
        im=Image.composite(im,shade,vign)
        path=OUT/f"scene_{i:02d}.png"
        im.save(path,optimize=True)
        print(path.relative_to(ROOT))
    print(f"CREATED={len(SCENES)}")
if __name__=="__main__":main()
