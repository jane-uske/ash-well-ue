import json
from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
data={'collision_channels':[n for n in dir(u.CollisionChannel) if n.isupper()],
      'collision_responses':[n for n in dir(u.CollisionResponseType) if n.isupper()],
      'input_helpers':[n for n in dir(u.PlayerController) if 'input' in n or 'key' in n],
      'play_docs':u.LevelEditorSubsystem.editor_request_begin_play.__doc__}
(root/'Saved/Automation/intro-api.json').write_text(json.dumps(data,indent=2))
