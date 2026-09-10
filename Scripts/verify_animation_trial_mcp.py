"""Verify imported assets and capture two distinct animation frames through UE MCP."""
import asyncio, base64, json, os, hashlib
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Docs/Verification/AnimationTrial'
os.environ['NO_PROXY']='127.0.0.1,localhost'
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with streamablehttp_client('http://127.0.0.1:8001/mcp') as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize()
            async def call(group,name,args=None):
                r=await session.call_tool('call_tool',{'toolset_name':group,'tool_name':name,'arguments':args or {}})
                assert not r.isError,str(r)
                return json.loads(r.content[0].text)['returnValue']
            seq='animation_toolset.toolsets.sequencer.SequencerTools'
            await call(seq,'pause')
            shots=[]
            for frame in [8,45]:
                await call(seq,'set_playhead_frame',{'frame':frame})
                actual=await call(seq,'get_playhead_frame')
                assert actual==frame,(actual,frame)
                await asyncio.sleep(.75)
                shot=await call('EditorToolset.EditorAppToolset','CaptureViewport',{
                    'captureTransform':{'location':{'x':680,'y':0,'z':295},'rotation':{'pitch':-16,'yaw':180,'roll':0},'scale':{'x':1,'y':1,'z':1}},
                    'annotations':{'gridSpacing':0,'gridExtent':0,'gridHeight':0,'maxLabelDistance':0,'classFilter':{'refPath':'/Script/Engine.Actor'},'maxLabels':0},'bShowUI':False})
                raw=base64.b64decode(shot['image']['data'])
                (OUT/f'frame-{frame:03d}.png').write_bytes(raw)
                shots.append({'frame':frame,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            assert shots[0]['sha256']!=shots[1]['sha256'],'Viewport did not render a new frame'
            await call(seq,'set_loop_mode',{'loop':True})
            await call(seq,'play')
            assert await call(seq,'is_playing')
            (OUT/'mcp-verification.json').write_text(json.dumps({'passed':True,'frames':shots,'playing':True},indent=2))
            print('UE MCP: two frame captures and loop playback verified.')
asyncio.run(main())
