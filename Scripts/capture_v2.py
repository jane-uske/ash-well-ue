from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
camera=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='AW_HeroCamera')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for cmd in ['r.ScreenPercentage 100','r.HighResScreenshotDelay 48','r.Lumen.ScreenProbeGather.Temporal.MaxFramesAccumulated 32']:
    u.SystemLibrary.execute_console_command(world,cmd)
out=root/'Saved/Screenshots/MacEditor';out.mkdir(parents=True,exist_ok=True)
u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out/'FirstDescentV02.png'),camera=camera,delay=3,force_game_view=True)
