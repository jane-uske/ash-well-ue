"""Local MCP client for the explicitly started Terrace editor server."""
from pathlib import Path
import urllib.request,json,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Saved/Terrace'
def call(name,arguments=None):
 headers=json.loads((OUT/'mcp-session.json').read_text())
 payload={'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':name,'arguments':arguments or {}}}
 request=urllib.request.Request('http://127.0.0.1:19852/mcp',data=json.dumps(payload).encode(),headers=headers)
 with urllib.request.urlopen(request,timeout=45) as response:result=json.loads(response.read())
 return result
if __name__=='__main__':
 result=call(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {})
 (OUT/'mcp-last-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps(result,ensure_ascii=False))
