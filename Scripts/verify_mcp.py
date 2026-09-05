import asyncio,json
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
 async with streamablehttp_client('http://127.0.0.1:8001/mcp') as (r,w,_):
  async with ClientSession(r,w) as s:
   await s.initialize(); evidence=[]
   async def call(group,name,args):
    result=await s.call_tool('call_tool',{'toolset_name':group,'tool_name':name,'arguments':args})
    if result.isError: raise RuntimeError(str(result))
    data=json.loads(result.content[0].text)
    evidence.append({'tool':name,'result':data})
    return data.get('returnValue')
   scene='editor_toolset.toolsets.scene.SceneTools';actor='editor_toolset.toolsets.actor.ActorTools'
   level=await call(scene,'get_current_level',{})
   assert level=='/Game/AshWell/Maps/FirstDescentIntro',level
   probe=await call(scene,'add_to_scene_from_class',{'actor_type':{'refPath':'/Script/Engine.PointLight'},'name':'MCP_Connection_Verification_Temporary','xform':{'location':{'x':0,'y':0,'z':-10000}}})
   try:
    await call(actor,'set_actor_transform',{'actor':probe,'xform':{'location':{'x':123,'y':456,'z':-10000}}})
    result=await call(actor,'get_actor_transform',{'actor':probe})
    assert '123' in json.dumps(result) and '456' in json.dumps(result),result
   finally:
    assert await call(scene,'remove_from_scene',{'actor':probe})
   remaining=await call(scene,'find_actors',{'name':'MCP_Connection_Verification_Temporary','tag':'','collision_channels':[]})
   assert not remaining,remaining
   path=Path(__file__).resolve().parents[1]/'Saved/Automation/mcp-verification.json'
   path.write_text(json.dumps({'passed':True,'url':'http://127.0.0.1:8001/mcp','evidence':evidence},ensure_ascii=False,indent=2))
   print(path.read_text())
asyncio.run(main())
