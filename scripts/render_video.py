#!/usr/bin/env python3
"""Render a narrated 1080p slideshow from episode JSON using Edge TTS + FFmpeg."""
import asyncio, json, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
VOICE="es-MX-DaliaNeural"

def run(cmd): subprocess.run(cmd,check=True)
def font(size,bold=False):
    names=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
           "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for n in names:
        if Path(n).exists(): return ImageFont.truetype(n,size)
    return ImageFont.load_default()

def make_card(scene,index,total,out):
    src=scene.get("image")
    if src and (ROOT/src).is_file():
        base=Image.open(ROOT/src).convert("RGB").resize((W,H)).convert("RGBA")
        base=Image.alpha_composite(base,Image.new("RGBA",(W,H),(0,0,0,125)))
    else:
        base=Image.new("RGBA",(W,H),(12,18,32,255))
        d=ImageDraw.Draw(base)
        for y in range(H):
            shade=int(22+35*y/H); d.line((0,y,W,y),fill=(8,shade,shade+25,255))
    d=ImageDraw.Draw(base)
    d.rounded_rectangle((90,90,W-90,H-90),radius=30,outline=(90,180,220,190),width=4)
    d.text((145,145),"GAMEPLAYS CON J  •  MISTERIOS Y SECRETOS",font=font(30,True),fill=(120,220,240,255))
    d.text((145,240),str(scene.get("heading") or f"Parte {index+1}")[:90],font=font(64,True),fill="white")
    y=370
    for line in textwrap.wrap(str(scene["narration"]),width=58)[:8]:
        d.text((150,y),line,font=font(32),fill=(235,240,248,255),stroke_width=1,stroke_fill=(0,0,0,150)); y+=56
    d.text((145,H-160),f"{index+1:02d} / {total:02d}",font=font(28,True),fill=(170,210,225,255))
    base.convert("RGB").save(out,quality=94)

async def speak(text,path):
    await edge_tts.Communicate(text,VOICE).save(str(path))

def main():
    episode=Path(sys.argv[1]) if len(sys.argv)>1 else Path("episodes/demo.json")
    if not episode.is_absolute(): episode=ROOT/episode
    data=json.loads(episode.read_text(encoding="utf-8"))
    scenes=data.get("scenes",[])
    if not scenes: raise SystemExit("El episodio necesita al menos una escena.")
    work=ROOT/"work/scenes"; work.mkdir(parents=True,exist_ok=True)
    clips=[]
    for i,s in enumerate(scenes):
        if not str(s.get("narration","")).strip(): raise SystemExit(f"Escena {i+1}: falta narration.")
        audio=work/f"voice_{i:03d}.mp3"; card=work/f"card_{i:03d}.jpg"; clip=work/f"clip_{i:03d}.mp4"
        asyncio.run(speak(s["narration"],audio)); make_card(s,i,len(scenes),card)
        run(["ffmpeg","-y","-loop","1","-i",str(card),"-i",str(audio),"-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p","-c:v","libx264","-preset","veryfast","-tune","stillimage","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(clip)])
        clips.append(clip)
    concat=ROOT/"work/concat.txt"
    concat.write_text("".join("file '"+p.as_posix()+"'\n" for p in clips),encoding="utf-8")
    out=ROOT/"output/final.mp4"; out.parent.mkdir(exist_ok=True)
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(out)])
    meta={"title":str(data.get("title","Video de Gameplays con J"))[:100],"description":str(data.get("description",""))[:5000],"tags":data.get("tags",["videojuegos","misterios"]),"categoryId":"20","privacyStatus":"private"}
    (ROOT/"output/metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("VIDEO_READY="+str(out))
    print("Borrador generado. Revisa duración, fuentes y derechos del material visual antes de publicar.")

if __name__=="__main__": main()
