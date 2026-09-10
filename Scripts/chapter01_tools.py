"""Project-specific tools exposed through UE 5.8's native MCP server."""
import unreal,toolset_registry,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unreal.uclass()
class ChapterOneTools(unreal.ToolsetDefinition):
    """Build and inspect the approved Chapter One map without editing other levels."""
    @toolset_registry.tool_call
    @staticmethod
    def run_stage(stage: str) -> str:
        """Run a project chapter stage, including battleassets import and battlelayout spacing repair."""
        assert stage in ['import','build','inspect','playtest','grandassets','battleassets','battlelayout','swordassets','shutdown'],stage
        p=ROOT/'Scripts'/('chapter01_'+stage+'.py')
        scope={'__file__':str(p)};exec(compile(p.read_text(),str(p),'exec'),scope)
        return json.dumps(scope.get('report',{'stage':stage,'ok':True}),ensure_ascii=False)
