#include "AshWellSession.h"
#include "Misc/App.h"
#include "AudioDevice.h"
#include "Engine/World.h"

void UAshWellSession::Init()
{
    Super::Init();LoadConfig();
    MasterVolume=FMath::Clamp(MasterVolume,0.f,1.f);
    MouseSensitivity=FMath::Clamp(MouseSensitivity,.3f,2.f);
}
void UAshWellSession::ApplyAudio(UWorld* World) const
{
    if(World)if(auto Audio=World->GetAudioDevice())Audio->SetTransientPrimaryVolume(MasterVolume);
}
void UAshWellSession::Adjust(int32 Row,int32 Direction,UWorld* World)
{
    if(Row==0)MasterVolume=FMath::Clamp(MasterVolume+.1f*Direction,0.f,1.f);
    if(Row==1)MouseSensitivity=FMath::Clamp(MouseSensitivity+.1f*Direction,.3f,2.f);
    if(Row==2)bSubtitles=!bSubtitles;
    ApplyAudio(World);SaveConfig();
}


#include "HAL/PlatformMemory.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "GameFramework/GameUserSettings.h"
#include "Engine/Engine.h"

void UAshWellSession::RecordFrame(float Dt,UWorld* World)
{
    const double Now=FPlatformTime::Seconds();
    if(RunStart==0)RunStart=LastReport=Now;
    FrameTimes.Add(float(FApp::GetDeltaTime())*1000.f);
    if(Now-LastReport<10)return;
    LastReport=Now;
    const uint64 Memory=FPlatformMemory::GetStats().UsedPhysical;
    PeakMemory=FMath::Max(PeakMemory,Memory);
    if(Now-RunStart>60&&WarmMemory==0)WarmMemory=Memory;
    TArray<float> Sorted=FrameTimes;Sorted.Sort();
    const auto P=[&](float F){return Sorted[FMath::Clamp(FMath::FloorToInt((Sorted.Num()-1)*F),0,Sorted.Num()-1)];};
    int32 Hitches=0;for(float T:FrameTimes)if(T>50)++Hitches;
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();
    O->SetNumberField(TEXT("wall_seconds"),Now-RunStart);O->SetNumberField(TEXT("frames"),FrameTimes.Num());
    O->SetNumberField(TEXT("p50_ms"),P(.5));O->SetNumberField(TEXT("p95_ms"),P(.95));O->SetNumberField(TEXT("p99_ms"),P(.99));
    O->SetNumberField(TEXT("hitches_over_50ms"),Hitches);O->SetNumberField(TEXT("attempts"),Attempts);
    O->SetNumberField(TEXT("rss_mb"),Memory/1048576.);O->SetNumberField(TEXT("warm_rss_mb"),WarmMemory/1048576.);O->SetNumberField(TEXT("peak_rss_mb"),PeakMemory/1048576.);
    if(GEngine&&GEngine->GameUserSettings){const FIntPoint R=GEngine->GameUserSettings->GetScreenResolution();O->SetNumberField(TEXT("width"),R.X);O->SetNumberField(TEXT("height"),R.Y);}
    O->SetBoolField(TEXT("complete"),Now-RunStart>=1800);
    FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(O,Writer);
    FFileHelper::SaveStringToFile(Text,*(FPaths::ProjectSavedDir()/TEXT("Automation/performance-runtime.json")));
    if(Now-RunStart>=1800&&FParse::Param(FCommandLine::Get(),TEXT("CombatSoak")))FPlatformMisc::RequestExit(false);
}
