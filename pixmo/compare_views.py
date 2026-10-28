"""Create a labeled reference/render contact sheet using existing Pillow/ffmpeg."""
import argparse
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--renders',type=Path,required=True)
args=parser.parse_args()
ref=root/'references/pixmo'
frames=[(0,'establishing'),(8,'approach'),(12,'pickup'),(16,'transfer'),
        (24,'pallet-side'),(40,'partial-stack'),(64,'base-movement'),(88,'placement')]
for timestamp,name in frames:
    target=ref/'frames'/f'{timestamp:03d}-{name}.jpg'
    if not target.exists():
        subprocess.run(['ffmpeg','-loglevel','error','-ss',str(timestamp),'-i',str(ref/'reference.mp4'),
                        '-frames:v','1','-y',str(target)],check=True)
rows=[('024-pallet-side.jpg','profile.png','Robot proportions / pallet adjacency'),
      ('000-establishing.jpg','wide.png','Warehouse and conveyor layout'),
      ('012-pickup.jpg','pick_01.png','Top-face suction / lift'),
      ('016-transfer.jpg','placed_01.png','Conveyor transfer / release')]
sheet=Image.new('RGB',(1440,4*460),(24,29,36))
draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
for i,(frame,render,label) in enumerate(rows):
    for j,path in enumerate([ref/'frames'/frame,args.renders/render]):
        picture=Image.open(path).convert('RGB');picture.thumbnail((704,414))
        sheet.paste(picture,(8+j*720,40+i*460))
    draw.text((10,i*460+8),'Reference — '+label,fill='white',font=font)
    draw.text((730,i*460+8),'Isaac Sim — approximate camera match',fill='white',font=font)
sheet.save(args.renders/'reference_comparison.jpg',quality=93)
print(args.renders/'reference_comparison.jpg')
