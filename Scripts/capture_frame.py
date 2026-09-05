"""Capture the lit real-time UE editor viewport, without a UI overlay."""
import pathlib
import unreal as u

ROOT = pathlib.Path(__file__).resolve().parents[1]
out = ROOT / 'Saved/Screenshots/MacEditor'
out.mkdir(parents=True, exist_ok=True)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
camera = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == 'AW_HeroCamera')
u.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
u.EditorLevelLibrary.editor_set_game_view(True)
u.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out / 'FirstDescent.png'), camera=camera, delay=3.0, force_game_view=True)
u.log('ASHWELL: realtime screenshot requested')
