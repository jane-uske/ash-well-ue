using UnrealBuildTool;
public class AshWell : ModuleRules
{
    public AshWell(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        // Existing Warden and mounted units include the same unguarded rest-pose
        // constants. Compile separately without changing either baseline rig.
        bUseUnity = false;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "SlateCore", "Json", "JsonUtilities", "ClothingSystemRuntimeCommon", "ChaosCloth", "AnimGraphRuntime", "AudioMixer" });
        PrivateDependencyModuleNames.AddRange(new string[] { "MovieSceneCapture", "Slate", "ImageWrapper", "ImageCore", "RenderCore", "RHI", "AnimationWarpingRuntime" });
        if(Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "ClothingSystemEditor", "ClothingSystemEditorInterface", "AnimGraph", "BlueprintGraph", "KismetCompiler", "AnimationWarpingEditor" });
    }
}
