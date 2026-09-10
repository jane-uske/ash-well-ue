import unreal as u
m=u.EditorAssetLibrary.load_asset('/Game/AshWell/Combat/HeroComplete/SK_HeroCloak')
assert u.AshWellHeroTools.build_hero_clothing(m)
u.EditorAssetLibrary.save_loaded_asset(m)
u.log('HERO_CLOTH_REBOUND')
