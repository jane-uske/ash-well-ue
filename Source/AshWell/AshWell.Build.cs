using UnrealBuildTool;
public class AshWell : ModuleRules
{
    public AshWell(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "SlateCore", "Json", "JsonUtilities", "ClothingSystemRuntimeCommon", "ChaosCloth", "AnimGraphRuntime", "AudioMixer" });
        PrivateDependencyModuleNames.AddRange(new string[] { "MovieSceneCapture", "Slate", "ImageWrapper", "ImageCore", "RenderCore", "RHI" });
        if(Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "ClothingSystemEditor", "ClothingSystemEditorInterface" });
    }
}
