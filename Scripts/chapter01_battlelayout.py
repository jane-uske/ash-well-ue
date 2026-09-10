from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];actors=u.get_editor_subsystem(u.EditorActorSubsystem);report={'intersections':[]}
for a in actors.get_all_level_actors():
 c=a.get_component_by_class(u.StaticMeshComponent)
 if not c:continue
 origin,extent=a.get_actor_bounds(False);label=a.get_actor_label()
 if origin.x+extent.x>3250 and origin.x-extent.x<5510 and origin.y+extent.y>260 and origin.y-extent.y<2330 and origin.z+extent.z>15 and origin.z-extent.z<350:
  report['intersections'].append({'label':label,'folder':str(a.get_folder_path()),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'origin':[origin.x,origin.y,origin.z],'extent':[extent.x,extent.y,extent.z],'location':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]})
(R/'Saved/BattlePolish/layout-inspect.json').write_text(json.dumps(report,indent=2))
# The inherited city is a single coherent backdrop assembled at the world origin.
# Translate that whole backdrop together, keeping windows/cables/lights aligned,
# so the 1.65x station no longer intersects the old pier's solid-looking facade.
report['moved']=[]
for a in actors.get_all_level_actors():
 label=a.get_actor_label();folder=str(a.get_folder_path());c=a.get_component_by_class(u.StaticMeshComponent)
 mesh=c.static_mesh.get_path_name() if c and c.static_mesh else ''
 if 'AW_BattleLayout_v1' in [str(t) for t in a.tags]:continue
 if folder=='Chapter01/InheritedFar' and ('/ArchitectureV2/' in mesh or isinstance(a,(u.PointLight,u.RectLight))):
  p=a.get_actor_location();a.set_actor_location(u.Vector(p.x+1500,p.y,p.z),False,False);a.tags=list(a.tags)+['AW_BattleLayout_v1'];report['moved'].append(label)
 elif label.startswith('AWC_StationSupport_') or label.startswith('AWC_PierCollar_'):
  p=a.get_actor_location();a.set_actor_location(u.Vector(p.x,p.y+950,p.z),False,False);a.tags=list(a.tags)+['AW_BattleLayout_v1'];report['moved'].append(label)
ring=u.EditorAssetLibrary.load_asset('/Game/AshWell/Combat/BattlePolish/SM_BattleShockRing');b=ring.get_bounds();report['ring_radius_cm']=max(b.box_extent.x,b.box_extent.y)
assert 45<report['ring_radius_cm']<55,report['ring_radius_cm']
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(R/'Saved/BattlePolish/layout-apply.json').write_text(json.dumps(report,indent=2))
report={'moved':report['moved'],'ring_radius_cm':report['ring_radius_cm']}
