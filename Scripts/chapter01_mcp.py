"""Client for this chapter's own UE MCP instance; no global connection changes."""
import asyncio,json,sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
R=Path(__file__).resolve().parents[1]
async def main():
 async with streamablehttp_client('http://127.0.0.1:19854/mcp') as (r,w,_):
  async with ClientSession(r,w) as s:
   await s.initialize()
   if len(sys.argv)==1:res=await s.list_tools()
   else:res=await s.call_tool(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {})
   data=res.model_dump(mode='json');(R/'Saved/Chapter01/mcp-last.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps(data,ensure_ascii=False))
   if getattr(res,'isError',False):raise SystemExit(1)
asyncio.run(main())
