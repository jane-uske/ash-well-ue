from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];out=R/'SourceAssets/Chapter01/Signs';out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype(str(R/'Content/AshWell/Intro/Fonts/NotoSansSC-Regular.otf'),76);small=ImageFont.truetype(str(R/'Content/AshWell/Intro/Fonts/NotoSansSC-Regular.otf'),34)
labels={'water':('下层街区 · 配水窗口','请自备容器    今日供水待检修'),'departure':('七号检修站  →','井下作业通道    凭工单通行'),'station':('07  /  七号检修站','升降设备停运    请先恢复本地供电')}
for name,(title,sub) in labels.items():
 im=Image.new('RGB',(1280,320),(19,26,29));d=ImageDraw.Draw(im);d.rectangle((10,10,1270,310),outline=(116,93,60),width=5);d.text((640,115),title,font=font,fill=(215,202,170),anchor='mm');d.text((640,232),sub,font=small,fill=(148,161,158),anchor='mm');im.save(out/(name+'.png'))
