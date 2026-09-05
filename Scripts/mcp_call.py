import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
 async with streamablehttp_client("http://127.0.0.1:8001/mcp") as (r,w,_):
  async with ClientSession(r,w) as s:
   info=await s.initialize()
   if len(sys.argv)==1:
    result={"server":info.model_dump(mode="json"),"tools":(await s.list_tools()).model_dump(mode="json")}
   else:
    result=(await s.call_tool(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {})).model_dump(mode="json")
   print(json.dumps(result,ensure_ascii=False,indent=2))
asyncio.run(main())
