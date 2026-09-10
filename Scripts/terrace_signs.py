from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'SourceAssets/Terrace/Signs';out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype(str(ROOT/'Content/AshWell/Intro/Fonts/NotoSansSC-Regular.otf'),72)
small=ImageFont.truetype(str(ROOT/'Content/AshWell/Intro/Fonts/NotoSansSC-Regular.otf'),35)
labels={'entry':('断链台  /  井口作业层','WASD 移动    鼠标环顾    E 打开回程侧门'),'routes':('← 上层宽台       下层管廊 →','两条路都通往断吊臂'),'gate':('回程侧门','门闩位于吊臂一侧 · 靠近按 E'),'crane':('断吊臂','回程侧门在脚下的中央通道'),'lower':('下层管廊','维护道上行 → 断吊臂'),'home':('冠炉城 · 家园','高岩台 / 远景提案')}
for name,(title,sub) in labels.items():
 im=Image.new('RGB',(1280,320),(22,35,43));d=ImageDraw.Draw(im);d.rectangle((9,9,1270,310),outline=(164,132,91),width=5);d.text((640,112),title,font=font,fill=(231,211,172),anchor='mm');d.text((640,235),sub,font=small,fill=(169,187,191),anchor='mm');im.save(out/(name+'.png'))
print('Six local Chinese signs prepared.')
