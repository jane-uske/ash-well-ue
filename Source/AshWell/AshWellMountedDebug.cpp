#include "AshWellCombatCharacter.h"
#if WITH_EDITOR
#include "ShaderCompiler.h"
#endif
#include "AshWellMountedBoss.h"
#include "AshWellBattleFX.h"
#include "Components/InputComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerInput.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformProperties.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Dom/JsonObject.h"
#include "AudioMixerBlueprintLibrary.h"
#include "UnrealClient.h"
#include "FrameGrabber.h"
#include "Engine/GameViewportClient.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "Containers/Ticker.h"
#include "Async/Async.h"
#include "IImageWrapperModule.h"
#include "ImageCore.h"
#include "Modules/ModuleManager.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"
#include "HAL/IConsoleManager.h"
#include "Audio.h"

namespace
{
bool MountedRecording=false;
FString MountedRecordingPath;
double MountedRecordingStarted=0,MountedRecordingNext=0;
int MountedRecordingFrame=0;
FIntPoint MountedRecordingSize=FIntPoint::ZeroValue;
TWeakObjectPtr<AAshWellCombatCharacter> MountedReviewOwner;
bool MountedReviewStarted=false,MountedReviewFixtureStarted=false,MountedReviewFinished=false,MountedReviewAIResumed=false;
TSharedPtr<FJsonObject> MountedReviewFirstCharge;
constexpr int32 MountedCaptureFPS=24,MountedCaptureMaxWrites=8;
TUniquePtr<FFrameGrabber> MountedFrameGrabber;
FTSTicker::FDelegateHandle MountedCaptureTicker;
TWeakObjectPtr<AAshWellCombatCharacter> MountedRecordingOwner;
int32 MountedFramesInFlight=0,MountedFramesWritten=0,MountedFrameWriteFailures=0,MountedCaptureSkippedSlots=0;
int32 MountedPreviousContinuousSubmixes=0;
bool MountedChangedContinuousSubmixes=false;

struct FMountedFramePayload final : IFramePayload
{
    int32 Index=0;
    double RequestedAt=0,StartedAt=0;
    mutable double ReadyAt=0;
    virtual bool OnFrameReady_RenderThread(FColor*,FIntPoint,FIntPoint) const override
    {ReadyAt=FPlatformTime::Seconds();return true;}
};
struct FMountedFrameWriteResult
{
    int32 Index=0,Width=0,Height=0;
    double RequestSeconds=0,ReadySeconds=0,WriteMilliseconds=0;
    FString File;
    bool bSaved=false;
};
TArray<TFuture<FMountedFrameWriteResult>> MountedFrameWrites;

void WriteMountedRecordingJson(const FString& Path,const TSharedRef<FJsonObject>& Object,bool bAppend=false)
{
    FString Text;FJsonSerializer::Serialize(Object,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text));Text+=TEXT("\n");
    FFileHelper::SaveStringToFile(Text,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),bAppend?FILEWRITE_Append:0);
}

void DrainMountedFrameWrites(bool bWait)
{
    // Consume in request order even when later PNG jobs complete sooner.
    while(!MountedFrameWrites.IsEmpty()&&(bWait||MountedFrameWrites[0].IsReady()))
    {
        FMountedFrameWriteResult Result=MountedFrameWrites[0].Get();MountedFrameWrites.RemoveAt(0,EAllowShrinking::No);
        auto Frame=MakeShared<FJsonObject>();Frame->SetStringField(TEXT("file"),Result.File);Frame->SetNumberField(TEXT("index"),Result.Index);
        Frame->SetNumberField(TEXT("real_seconds"),Result.RequestSeconds);Frame->SetNumberField(TEXT("request_real_seconds"),Result.RequestSeconds);
        Frame->SetNumberField(TEXT("frame_ready_real_seconds"),Result.ReadySeconds);Frame->SetNumberField(TEXT("encode_write_ms"),Result.WriteMilliseconds);
        Frame->SetNumberField(TEXT("width"),Result.Width);Frame->SetNumberField(TEXT("height"),Result.Height);Frame->SetBoolField(TEXT("saved"),Result.bSaved);
        Frame->SetStringField(TEXT("timestamp_source"),TEXT("monotonic capture-request payload; readback-ready time is retained separately"));
        WriteMountedRecordingJson(MountedRecordingPath/TEXT("frames.jsonl"),Frame,true);
        if(Result.bSaved)++MountedFramesWritten;else ++MountedFrameWriteFailures;
    }
}

void QueueMountedCapturedFrames()
{
    if(!MountedFrameGrabber)return;
    TArray<FCapturedFrameData> Frames=MountedFrameGrabber->GetCapturedFrames();
    IImageWrapperModule* Images=FModuleManager::GetModulePtr<IImageWrapperModule>(TEXT("ImageWrapper"));
    for(FCapturedFrameData& Frame:Frames)
    {
        MountedFramesInFlight=FMath::Max(0,MountedFramesInFlight-1);
        const auto* Payload=Frame.GetPayload<FMountedFramePayload>();
        if(!Payload||!Images){++MountedFrameWriteFailures;continue;}
        FMountedFrameWriteResult Result;Result.Index=Payload->Index;Result.Width=Frame.BufferSize.X;Result.Height=Frame.BufferSize.Y;
        Result.File=FString::Printf(TEXT("frame-%06d.png"),Result.Index);
        Result.RequestSeconds=Payload->RequestedAt-Payload->StartedAt;Result.ReadySeconds=Payload->ReadyAt-Payload->StartedAt;
        const FString OutputFile=MountedRecordingPath/Result.File;
        // Only owned pixel arrays, strings and the preloaded image module enter the worker.
        // No UObject, viewport or actor is captured by an asynchronous PNG job.
        MountedFrameWrites.Add(Async(EAsyncExecution::ThreadPool,[Pixels=MoveTemp(Frame.ColorBuffer),Images,OutputFile,Result]() mutable
        {
            const double Before=FPlatformTime::Seconds();
            for(FColor& Pixel:Pixels)Pixel.A=255;
            TArray64<uint8> PNG;
            Result.bSaved=Pixels.Num()==Result.Width*Result.Height&&Images->CompressImage(PNG,EImageFormat::PNG,FImageView(Pixels.GetData(),Result.Width,Result.Height),-3)&&FFileHelper::SaveArrayToFile(PNG,*OutputFile);
            Result.WriteMilliseconds=(FPlatformTime::Seconds()-Before)*1000.;return Result;
        }));
    }
}

bool TickMountedCapture(float)
{
    if(!MountedRecording||!MountedFrameGrabber)return false;
    DrainMountedFrameWrites(false);QueueMountedCapturedFrames();
    const double Now=FPlatformTime::Seconds();
    if(Now>=MountedRecordingNext)
    {
        const int32 Due=1+FMath::Max(0,FMath::FloorToInt((Now-MountedRecordingNext)*MountedCaptureFPS));
        MountedRecordingNext+=double(Due)/MountedCaptureFPS;MountedCaptureSkippedSlots+=Due-1;
        if(MountedFrameWrites.Num()+MountedFramesInFlight<MountedCaptureMaxWrites)
        {
            auto Payload=MakeShared<FMountedFramePayload,ESPMode::ThreadSafe>();Payload->Index=MountedRecordingFrame++;
            Payload->RequestedAt=Now;Payload->StartedAt=MountedRecordingStarted;
            ++MountedFramesInFlight;MountedFrameGrabber->CaptureThisFrame(Payload);
        }
        else ++MountedCaptureSkippedSlots; // A time gap is recorded; gameplay never waits for PNG compression.
    }
    return true;
}

bool MountedWavIsComplete(const FString& Path)
{
    TUniquePtr<FArchive> Reader(IFileManager::Get().CreateFileReader(*Path,FILEREAD_Silent));
    if(!Reader||Reader->TotalSize()<44)return false;
    uint8 Header[12];Reader->Serialize(Header,12);
    const uint32 RiffBytes=uint32(Header[4])|(uint32(Header[5])<<8)|(uint32(Header[6])<<16)|(uint32(Header[7])<<24);
    return Header[0]=='R'&&Header[1]=='I'&&Header[2]=='F'&&Header[3]=='F'&&Header[8]=='W'&&Header[9]=='A'&&Header[10]=='V'&&Header[11]=='E'&&Reader->TotalSize()>=int64(RiffBytes)+8;
}

bool StartMountedCapture(AAshWellCombatCharacter* Owner)
{
    if(MountedRecording||!Owner||!Owner->GetWorld()||!FSlateApplication::IsInitialized())return false;
    UGameViewportClient* Client=Owner->GetWorld()->GetGameViewport();FSceneViewport* Viewport=Client?Client->GetGameViewport():nullptr;
    if(!Viewport||Viewport->GetSize().X<=0||Viewport->GetSize().Y<=0||!Viewport->GetViewportWidget().IsValid())return false;
    const TSharedPtr<SViewport> Widget=Viewport->GetViewportWidget().Pin();
    const TSharedPtr<ISlateViewport> ViewportInterface=Widget.IsValid()?Widget->GetViewportInterface().Pin():nullptr;
    const TSharedPtr<FSceneViewport> SharedViewport=StaticCastSharedPtr<FSceneViewport>(ViewportInterface);
    if(!SharedViewport.IsValid()||SharedViewport.Get()!=Viewport)return false;
    FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
    // PCMWriter prefixes its own Saved/BouncedWavFiles directory for relative paths.
    // Resolve once here so image and WAV output use the same correct absolute directory.
    MountedRecordingPath=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("MountedBoss/Recordings")/(FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%SZ"))+TEXT("-")+FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8)));
    if(!IFileManager::Get().MakeDirectory(*MountedRecordingPath,true))return false;
    // UE 5.8 DrawRectangle uses the capture rect as target-buffer size. Capturing
    // to a smaller texture leaves an unrendered border on Metal. Keep sizes equal
    // and encode the entire native frame; never crop that defect out of evidence.
    MountedRecordingSize=SharedViewport->GetSize();
    if(Widget.IsValid())
    {const FVector2D Size=Widget->GetCachedGeometry().GetAbsoluteSize();if(Size.X>0&&Size.Y>0)MountedRecordingSize=FIntPoint(FMath::RoundToInt(Size.X),FMath::RoundToInt(Size.Y));}
    MountedFrameGrabber=MakeUnique<FFrameGrabber>(SharedViewport.ToSharedRef(),MountedRecordingSize,PF_B8G8R8A8,4);
    MountedFrameGrabber->StartCapturingFrames();MountedFrameWrites.Reset();MountedRecordingOwner=Owner;
    MountedRecordingFrame=MountedFramesInFlight=MountedFramesWritten=MountedFrameWriteFailures=MountedCaptureSkippedSlots=0;
    MountedRecordingStarted=FPlatformTime::Seconds();MountedRecordingNext=MountedRecordingStarted;
    // UE's submix auto-disable returns before the legacy recording append. Keep
    // real silent samples on the audio clock; never repair missing time in muxing.
    if(auto* CVar=IConsoleManager::Get().FindConsoleVariable(TEXT("au.NeverDisableSubmixes")))
    {MountedPreviousContinuousSubmixes=CVar->GetInt();CVar->SetWithCurrentPriority(1);MountedChangedContinuousSubmixes=true;}
    UAudioMixerBlueprintLibrary::StartRecordingOutput(Owner,180.f);MountedRecording=true;
    MountedCaptureTicker=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&TickMountedCapture));
    auto Meta=MakeShared<FJsonObject>();Meta->SetStringField(TEXT("status"),TEXT("recording"));Meta->SetStringField(TEXT("source"),TEXT("presented UE viewport via FFrameGrabber; master audio submix"));
    Meta->SetNumberField(TEXT("nominal_capture_fps"),MountedCaptureFPS);Meta->SetNumberField(TEXT("width"),MountedRecordingSize.X);Meta->SetNumberField(TEXT("height"),MountedRecordingSize.Y);
    WriteMountedRecordingJson(MountedRecordingPath/TEXT("recording.json"),Meta);return true;
}

bool StopMountedCapture(AAshWellCombatCharacter* Owner,const FString& Reason)
{
    if(!MountedRecording||MountedRecordingOwner.Get()!=Owner)return false;
    const double Stopped=FPlatformTime::Seconds();MountedRecording=false;
    if(MountedCaptureTicker.IsValid()){FTSTicker::GetCoreTicker().RemoveTicker(MountedCaptureTicker);MountedCaptureTicker.Reset();}
    UAudioMixerBlueprintLibrary::StopRecordingOutput(Owner,EAudioRecordingExportType::WavFile,TEXT("game-audio"),MountedRecordingPath);
    if(MountedChangedContinuousSubmixes)
    {if(auto* CVar=IConsoleManager::Get().FindConsoleVariable(TEXT("au.NeverDisableSubmixes")))CVar->SetWithCurrentPriority(MountedPreviousContinuousSubmixes);MountedChangedContinuousSubmixes=false;}
    // Waiting is confined to explicit stop/save or actor teardown, never the capture tick.
    if(MountedFrameGrabber)
    {
        MountedFrameGrabber->StopCapturingFrames();FlushRenderingCommands();QueueMountedCapturedFrames();
        MountedFrameGrabber->Shutdown();QueueMountedCapturedFrames();MountedFrameGrabber.Reset();
    }
    DrainMountedFrameWrites(true);
    const FString WavFile=MountedRecordingPath/TEXT("game-audio.wav");const double AudioDeadline=FPlatformTime::Seconds()+5.;
    bool AudioComplete=MountedWavIsComplete(WavFile);
    while(!AudioComplete&&FPlatformTime::Seconds()<AudioDeadline){FPlatformProcess::Sleep(.01f);AudioComplete=MountedWavIsComplete(WavFile);}
    double AudioSeconds=0;
    if(AudioComplete)
    {
        TArray<uint8> Bytes;FWaveModInfo Info;
        if(FFileHelper::LoadFileToArray(Bytes,*WavFile)&&Info.ReadWaveInfo(Bytes.GetData(),Bytes.Num())&&Info.pAvgBytesPerSec&&*Info.pAvgBytesPerSec)
            AudioSeconds=double(Info.SampleDataSize)/double(*Info.pAvgBytesPerSec);
    }
    const bool AudioCoversTimeline=AudioComplete&&FMath::Abs(AudioSeconds-(Stopped-MountedRecordingStarted))<=.25;
    const bool Complete=MountedFrameWriteFailures==0&&MountedFramesWritten>0&&AudioCoversTimeline;
    auto Meta=MakeShared<FJsonObject>();Meta->SetStringField(TEXT("status"),Complete?(MountedCaptureSkippedSlots||MountedFramesInFlight?TEXT("saved_with_gaps"):TEXT("saved")):TEXT("incomplete"));
    Meta->SetStringField(TEXT("stop_reason"),Reason);Meta->SetNumberField(TEXT("duration_seconds"),Stopped-MountedRecordingStarted);
    Meta->SetNumberField(TEXT("frames_requested"),MountedRecordingFrame);Meta->SetNumberField(TEXT("frames_written"),MountedFramesWritten);Meta->SetNumberField(TEXT("frame_write_failures"),MountedFrameWriteFailures);
    Meta->SetNumberField(TEXT("uncaptured_requests_at_stop"),MountedFramesInFlight);Meta->SetNumberField(TEXT("skipped_capture_slots"),MountedCaptureSkippedSlots);
    Meta->SetNumberField(TEXT("nominal_capture_fps"),MountedCaptureFPS);Meta->SetNumberField(TEXT("width"),MountedRecordingSize.X);Meta->SetNumberField(TEXT("height"),MountedRecordingSize.Y);
    Meta->SetBoolField(TEXT("audio_wav_complete"),AudioComplete);Meta->SetStringField(TEXT("audio_path"),WavFile);
    Meta->SetNumberField(TEXT("audio_duration_seconds"),AudioSeconds);Meta->SetBoolField(TEXT("audio_covers_wall_timeline"),AudioCoversTimeline);
    Meta->SetStringField(TEXT("source"),TEXT("presented UE viewport via FFrameGrabber; asynchronous PNG compression; master audio submix"));
    Meta->SetStringField(TEXT("timing"),TEXT("Real frame-ready/request timestamps in frames.jsonl. Preserve gaps and full duration; no cuts or time compression."));
    Meta->SetStringField(TEXT("reload_policy"),TEXT("Every actor EndPlay closes this segment. Press F8 after R to start a new segment; loading gaps are not represented as captured footage."));
    FString ReviewMode;FParse::Value(FCommandLine::Get(),TEXT("MountedReviewRecord="),ReviewMode);
    Meta->SetStringField(TEXT("review_fixture"),ReviewMode);
    Meta->SetStringField(TEXT("input_source"),ReviewMode.IsEmpty()?TEXT("interactive window controls"):TEXT("explicit asset/single-action review fixture; not ordinary-input combat"));
    Meta->SetNumberField(TEXT("save_wait_seconds"),FPlatformTime::Seconds()-Stopped);
    WriteMountedRecordingJson(MountedRecordingPath/TEXT("recording.json"),Meta);MountedRecordingOwner.Reset();return Complete;
}

const TCHAR* MountedFixtureNames[]={TEXT("sweep"),TEXT("overhead"),TEXT("charge"),TEXT("body_check"),TEXT("rear"),TEXT("leap_shield")};
const TCHAR* MountedFixtureLabels[]={TEXT("横扫"),TEXT("过顶劈"),TEXT("冲锋掠斩"),TEXT("马肩撞"),TEXT("前蹄踏击"),TEXT("跃起盾砸")};
void DebugVector(const TSharedRef<FJsonObject>& Object,const TCHAR* Key,const FVector& Value)
{
    TArray<TSharedPtr<FJsonValue>> Values;
    Values.Add(MakeShared<FJsonValueNumber>(Value.X));Values.Add(MakeShared<FJsonValueNumber>(Value.Y));Values.Add(MakeShared<FJsonValueNumber>(Value.Z));
    Object->SetArrayField(Key,Values);
}
}

void AAshWellCombatCharacter::InitializeMountedDebugInput(UInputComponent* Input)
{
#if !UE_BUILD_SHIPPING
    if(!Input||bMountedDebugInputBound||!FParse::Param(FCommandLine::Get(),TEXT("MountedDebug")))return;
    bMountedDebugEnabled=true;bMountedDebugInputBound=true;
    if(auto* PC=Cast<APlayerController>(Controller))if(PC->PlayerInput)
    {
        // UE Development builds reserve these for viewmode commands. Remove only
        // this encounter's overlapping runtime binds, leaving project config intact.
        const FKey Reserved[]={EKeys::F1,EKeys::F2,EKeys::F3,EKeys::F4,EKeys::F5,EKeys::F6,EKeys::F7,EKeys::F8};
        PC->PlayerInput->DebugExecBindings.RemoveAll([&](const FKeyBind& B){for(const FKey& K:Reserved)if(B.Key==K)return true;return false;});
    }
    // Paused execution is restricted to these debug bindings. The character and boss
    // keep their ordinary paused tick policy, so action clocks and hit windows stop.
    Input->BindKey(EKeys::F8,IE_Pressed,this,&AAshWellCombatCharacter::ToggleMountedRecording).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::F1,IE_Pressed,this,&AAshWellCombatCharacter::ToggleMountedDebugPanel).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::F2,IE_Pressed,this,&AAshWellCombatCharacter::ToggleMountedDebugPause).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::F3,IE_Pressed,this,&AAshWellCombatCharacter::ToggleMountedDebugSlow).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::F4,IE_Pressed,this,&AAshWellCombatCharacter::ResetMountedDebugEncounter).bExecuteWhenPaused=true;
    Input->BindKey(EKeys::F5,IE_Pressed,this,&AAshWellCombatCharacter::ResumeMountedDebugAI).bExecuteWhenPaused=true;
    const FKey Fixtures[]={EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six};
    for(int32 I=0;I<6;++I)
    {
        FInputKeyBinding Binding(FInputChord(Fixtures[I]),IE_Pressed);Binding.bExecuteWhenPaused=true;
        Binding.KeyDelegate.GetDelegateForManualSet().BindLambda([this,I](){StartMountedDebugFixture(I);});
        Input->KeyBindings.Add(MoveTemp(Binding));
    }
    const FKey RecordedKeys[]={EKeys::W,EKeys::A,EKeys::S,EKeys::D,EKeys::LeftMouseButton,EKeys::RightMouseButton,EKeys::SpaceBar,EKeys::LeftShift,EKeys::LeftControl,EKeys::Tab,EKeys::E,EKeys::R,EKeys::Escape};
    for(const FKey& Key:RecordedKeys)for(int32 Edge=0;Edge<2;++Edge)
    {
        FInputKeyBinding Binding(FInputChord(Key),Edge==0?IE_Pressed:IE_Released);
        Binding.bConsumeInput=false;Binding.bExecuteWhenPaused=true;
        const FString Detail=Key.ToString()+(Edge==0?TEXT(":pressed"):TEXT(":released"));
        Binding.KeyDelegate.GetDelegateForManualSet().BindLambda([this,Detail,Key,Edge]()
        {
            // Releases received while paused must not leave held movement modifiers stuck on resume.
            if(Edge==1&&UGameplayStatics::IsGamePaused(this))
            {
                if(Key==EKeys::LeftShift){bSprintHeld=false;bSprint=false;}
                if(Key==EKeys::LeftControl)bSlow=false;
                if(Key==EKeys::SpaceBar)StopJumping();
            }
            RecordMountedDebugEvent(TEXT("input"),Detail);
        });
        Input->KeyBindings.Add(MoveTemp(Binding));
    }
#endif
}

void AAshWellCombatCharacter::InitializeMountedDebugLog()
{
    if(bMountedDebugLogReady||!bMountedDebugEnabled||!bMountedExperiment||!GetWorld())return;
    MountedDebugStartReal=FPlatformTime::Seconds();MountedDebugNextTrace=MountedDebugStartReal;
    MountedDebugSessionId=FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%SZ"))+TEXT("-")+FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8);
    const FString Directory=FPaths::ProjectSavedDir()/TEXT("MountedBoss/Debug");IFileManager::Get().MakeDirectory(*Directory,true);
    MountedDebugLogPath=Directory/(MountedDebugSessionId+TEXT(".jsonl"));bMountedDebugLogReady=true;
    RecordMountedDebugEvent(TEXT("session_start"),TEXT("Input/event timeline for diagnosis; not deterministic or bit-exact replay."));
}

void AAshWellCombatCharacter::RecordMountedDebugEvent(const FString& Event,const FString& Detail)
{
    if(!bMountedDebugEnabled||!bMountedExperiment||!GetWorld()||bMountedDebugLogFailed)return;
    if(!bMountedDebugLogReady){InitializeMountedDebugLog();if(!bMountedDebugLogReady)return;}
    auto O=MakeShared<FJsonObject>();
    O->SetStringField(TEXT("schema"),TEXT("ashwell.mounted.debug.v1"));O->SetStringField(TEXT("session"),MountedDebugSessionId);
    O->SetStringField(TEXT("event"),Event);O->SetStringField(TEXT("detail"),Detail);O->SetStringField(TEXT("utc"),FDateTime::UtcNow().ToIso8601());
    O->SetNumberField(TEXT("real_seconds"),FPlatformTime::Seconds()-MountedDebugStartReal);O->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
    O->SetNumberField(TEXT("frame"),static_cast<double>(GFrameCounter));O->SetNumberField(TEXT("dilation"),UGameplayStatics::GetGlobalTimeDilation(this));
    O->SetBoolField(TEXT("paused"),UGameplayStatics::IsGamePaused(this));O->SetBoolField(TEXT("single_attack_mode"),bMountedDebugSingle);
    O->SetStringField(TEXT("player_action"),GetCombatState());O->SetNumberField(TEXT("player_action_seconds"),StateTime);
    O->SetBoolField(TEXT("player_iframe"),IsInvulnerable());O->SetNumberField(TEXT("health"),Health);O->SetNumberField(TEXT("stamina"),Stamina);
    O->SetNumberField(TEXT("forward_input"),ForwardInput);O->SetNumberField(TEXT("right_input"),RightInput);
    O->SetNumberField(TEXT("attack_buffer_seconds"),AttackBuffer);O->SetNumberField(TEXT("dodge_buffer_seconds"),DodgeBuffer);
    O->SetNumberField(TEXT("player_hits"),HitCount);O->SetNumberField(TEXT("player_damage_count"),DamageTakenCount);O->SetNumberField(TEXT("player_evaded_count"),EvadedHits);
    DebugVector(O,TEXT("player_position"),GetActorLocation());DebugVector(O,TEXT("player_velocity"),GetVelocity());
    if(Controller)DebugVector(O,TEXT("camera_rotation_pyr"),FVector(Controller->GetControlRotation().Pitch,Controller->GetControlRotation().Yaw,Controller->GetControlRotation().Roll));
    if(IsValid(MountedBoss.Get()))
    {O->SetObjectField(TEXT("boss"),MountedBoss->GetTelemetry());O->SetNumberField(TEXT("attack_serial"),MountedBoss->GetAttackSerial());O->SetBoolField(TEXT("boss_hit_window"),MountedBoss->IsHitWindowOpen());}
    if(Event==TEXT("session_end")&&!MountedDebugFrameMs.IsEmpty())
    {
        MountedDebugFrameMs.Sort();double Total=0;for(float Ms:MountedDebugFrameMs)Total+=Ms;
        O->SetNumberField(TEXT("frame_count"),MountedDebugFrameMs.Num());O->SetNumberField(TEXT("mean_frame_ms"),Total/MountedDebugFrameMs.Num());
        O->SetNumberField(TEXT("p50_frame_ms"),MountedDebugFrameMs[int((MountedDebugFrameMs.Num()-1)*.5)]);O->SetNumberField(TEXT("p95_frame_ms"),MountedDebugFrameMs[int((MountedDebugFrameMs.Num()-1)*.95)]);O->SetNumberField(TEXT("p99_frame_ms"),MountedDebugFrameMs[int((MountedDebugFrameMs.Num()-1)*.99)]);
        O->SetBoolField(TEXT("capture_enabled"),bMountedRecordingObserved||FParse::Param(FCommandLine::Get(),TEXT("MountedRecord"))||FParse::Param(FCommandLine::Get(),TEXT("MountedCapture")));
    }
    if(Event==TEXT("session_start"))
    {
        O->SetStringField(TEXT("engine"),FEngineVersion::Current().ToString());O->SetStringField(TEXT("platform"),FPlatformProperties::PlatformName());
        O->SetStringField(TEXT("cpu"),FPlatformMisc::GetCPUBrand());O->SetStringField(TEXT("project"),FApp::GetProjectName());
        O->SetStringField(TEXT("map"),UGameplayStatics::GetCurrentLevelName(this,true));O->SetBoolField(TEXT("hero_v02"),bHeroComplete);
        O->SetStringField(TEXT("replay_scope"),TEXT("Timestamped key edges, sampled movement/camera, state transitions and contacts. Physics, frame scheduling and cloth are not bit-exact replayable."));
        O->SetNumberField(TEXT("trace_period_real_seconds"),.20);O->SetBoolField(TEXT("character_ticks_when_paused"),PrimaryActorTick.bTickEvenWhenPaused);
        int32 X=0,Y=0;if(auto* PC=Cast<APlayerController>(Controller))PC->GetViewportSize(X,Y);
        O->SetNumberField(TEXT("viewport_width"),X);O->SetNumberField(TEXT("viewport_height"),Y);
    }
    FString Line;FJsonSerializer::Serialize(O,TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Line));Line+=TEXT("\n");
    if(!FFileHelper::SaveStringToFile(Line,*MountedDebugLogPath,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),FILEWRITE_Append))
    {bMountedDebugLogFailed=true;UE_LOG(LogTemp,Warning,TEXT("AW_MOUNTED_DEBUG_LOG_FAILED %s"),*MountedDebugLogPath);}
}

void AAshWellCombatCharacter::TickMountedDebug(float DeltaSeconds)
{
    if(!bMountedDebugEnabled||!bMountedExperiment||!MountedBoss)return;
    if(MountedRecording)bMountedRecordingObserved=true;
    if(!UGameplayStatics::IsGamePaused(this)&&bMountedDebugOwnedPause)
    {MountedBoss->SetDebugPaused(false);bMountedDebugOwnedPause=false;RecordMountedDebugEvent(TEXT("debug_pause"),TEXT("resumed_by_other_control"));}
    if(MountedDebugFrameMs.Num()<100000)MountedDebugFrameMs.Add(float(FApp::GetDeltaTime())*1000.f);
    InitializeMountedDebugLog();
    const FString BossState=MountedBoss->GetStateLabel(),Attack=MountedBoss->GetAttackLabel(),PlayerState=GetCombatState();
    const int32 Serial=MountedBoss->GetAttackSerial();
    if(BossState!=MountedDebugLastBossState||Attack!=MountedDebugLastAttack||Serial!=MountedDebugLastSerial)
    {RecordMountedDebugEvent(TEXT("boss_state"));MountedDebugLastBossState=BossState;MountedDebugLastAttack=Attack;MountedDebugLastSerial=Serial;}
    if(PlayerState!=MountedDebugLastPlayerState){RecordMountedDebugEvent(TEXT("player_state"));MountedDebugLastPlayerState=PlayerState;}
    if(DamageTakenCount!=MountedDebugLastDamage||HitCount!=MountedDebugLastHits||MountedBoss->GetContactCount()!=MountedDebugLastContacts)
    {RecordMountedDebugEvent(TEXT("contact_counts"));MountedDebugLastDamage=DamageTakenCount;MountedDebugLastHits=HitCount;MountedDebugLastContacts=MountedBoss->GetContactCount();}
    const double Now=FPlatformTime::Seconds();
    if(Now>=MountedDebugNextTrace){RecordMountedDebugEvent(TEXT("trace"));MountedDebugNextTrace=Now+.20;}
    // Explicit project-owned render export, usable without operating the desktop.
    // It is intentionally labelled a fixture and is never used to claim C.
    FString ReviewMode;FParse::Value(FCommandLine::Get(),TEXT("MountedReviewRecord="),ReviewMode);
    if(ReviewMode==TEXT("asset")||ReviewMode==TEXT("charge")||ReviewMode==TEXT("death")||ReviewMode==TEXT("size")||ReviewMode==TEXT("moves"))
    {
        const bool ExternalReview=FParse::Param(FCommandLine::Get(),TEXT("MountedReviewExternal"));
        float StartDelay=3.f;FParse::Value(FCommandLine::Get(),TEXT("MountedReviewStartDelay="),StartDelay);
        if(MountedReviewOwner.Get()!=this){MountedReviewOwner=this;MountedReviewStarted=MountedReviewFixtureStarted=MountedReviewFinished=MountedReviewAIResumed=false;MountedReviewFirstCharge.Reset();}
        bool AssetsReady=true;
#if WITH_EDITOR
        AssetsReady=!GShaderCompilingManager||!GShaderCompilingManager->IsCompiling();
#endif
        if(!MountedReviewStarted&&GetWorld()->GetRealTimeSeconds()>StartDelay&&AssetsReady)
        {
            MountedReviewStarted=true;if(ReviewMode==TEXT("asset")||ReviewMode==TEXT("death")){SetActorHiddenInGame(true);if(auto* PC=Cast<APlayerController>(Controller))if(PC->GetHUD())PC->GetHUD()->bShowHUD=false;}
            if(ReviewMode==TEXT("size"))
            {
                FVector P=MountedBoss->GetActorLocation()+MountedBoss->GetActorRightVector()*300;
                P.Z=MountedBoss->GroundHeightAt(P)+GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+2;
                SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);
            }
            if(ExternalReview)
            {
                MountedRecordingStarted=Now;
                MountedRecordingPath=FPaths::ProjectSavedDir()/TEXT("MountedBoss/ExternalReviews")/MountedDebugSessionId;
                IFileManager::Get().MakeDirectory(*MountedRecordingPath,true);
                RecordMountedDebugEvent(TEXT("external_review_start"),ReviewMode);
            }
            else ToggleMountedRecording();
            UE_LOG(LogTemp,Display,TEXT("AW_REVIEW_RECORD mode=%s external=%d path=%s"),*ReviewMode,ExternalReview,*MountedRecordingPath);
            if(!ExternalReview&&!MountedRecording){UE_LOG(LogTemp,Error,TEXT("AW_REVIEW_RECORD_BLOCKED no live viewport capture"));FPlatformMisc::RequestExit(false);}
        }
        if((MountedRecording||(ExternalReview&&MountedReviewStarted))&&!MountedReviewFinished)
        {
            const double Elapsed=Now-MountedRecordingStarted;
            if(ReviewMode==TEXT("moves")&&Elapsed>.5&&Elapsed<42.5)
            {
                const int32 Index=FMath::Min(5,FMath::FloorToInt((Elapsed-.5)/7.));
                if(!MountedReviewFixtureStarted||MountedDebugFixture!=Index)
                {MountedReviewFixtureStarted=true;StartMountedDebugFixture(Index);bMountedDebugVisible=false;}
            }
            if(ReviewMode==TEXT("moves")&&Elapsed>42.5&&!MountedReviewAIResumed)
            {ResumeMountedDebugAI();MountedReviewAIResumed=true;}
            if(ReviewMode==TEXT("death")&&!MountedReviewFixtureStarted&&Elapsed>3)
            {MountedReviewFixtureStarted=true;MountedBoss->SetQAHealth(0);}
            if(ReviewMode==TEXT("charge")&&!MountedReviewFixtureStarted&&Elapsed>.5)
            {MountedReviewFixtureStarted=true;StartMountedDebugFixture(2);bMountedDebugVisible=false;}
            if(ReviewMode==TEXT("charge")&&MountedReviewFixtureStarted&&!MountedReviewAIResumed&&Elapsed>5.2&&MountedBoss->GetCombatState()==EMountedBossState::Approach)
            {MountedReviewFirstCharge=MountedBoss->GetTelemetry();ResumeMountedDebugAI();MountedReviewAIResumed=true;}
            float Duration=ReviewMode==TEXT("asset")?25.f:18.f;FParse::Value(FCommandLine::Get(),TEXT("MountedReviewSeconds="),Duration);
            if(Elapsed>=FMath::Clamp(Duration,8.f,60.f))
            {
                MountedReviewFinished=true;auto Summary=MakeShared<FJsonObject>();Summary->SetObjectField(TEXT("boss"),MountedBoss->GetTelemetry());Summary->SetNumberField(TEXT("player_health"),Health);Summary->SetStringField(TEXT("mode"),ReviewMode);Summary->SetNumberField(TEXT("dilation"),UGameplayStatics::GetGlobalTimeDilation(this));
                Summary->SetBoolField(TEXT("natural_ai_resumed"),MountedReviewAIResumed);if(MountedReviewFirstCharge)Summary->SetObjectField(TEXT("first_charge_complete"),MountedReviewFirstCharge.ToSharedRef());
                WriteMountedRecordingJson(MountedRecordingPath/TEXT("review.json"),Summary);if(!ExternalReview)ToggleMountedRecording();FPlatformMisc::RequestExit(false);
            }
        }
    }
}

void AAshWellCombatCharacter::ToggleMountedDebugPanel()
{if(!bMountedDebugEnabled||!bMountedExperiment)return;bMountedDebugVisible=!bMountedDebugVisible;RecordMountedDebugEvent(TEXT("debug_panel"),bMountedDebugVisible?TEXT("show"):TEXT("hide"));}

void AAshWellCombatCharacter::ToggleMountedDebugPause()
{
    if(!bMountedDebugEnabled||!bMountedExperiment)return;
    const bool Pause=!UGameplayStatics::IsGamePaused(this);
    if(UGameplayStatics::SetGamePaused(this,Pause)){bMountedDebugOwnedPause=Pause;if(Pause)bMountedDebugVisible=true;if(MountedBoss)MountedBoss->SetDebugPaused(Pause);}
    RecordMountedDebugEvent(TEXT("debug_pause"),Pause?TEXT("pause"):TEXT("resume"));
}

void AAshWellCombatCharacter::ToggleMountedDebugSlow()
{
    if(!bMountedDebugEnabled||!bMountedExperiment)return;
    const bool Slow=UGameplayStatics::GetGlobalTimeDilation(this)>.5f;
    UGameplayStatics::SetGlobalTimeDilation(this,Slow?.25f:1.f);bMountedDebugOwnedSlow=Slow;
    RecordMountedDebugEvent(TEXT("debug_speed"),Slow?TEXT("0.25x"):TEXT("1x"));
}

void AAshWellCombatCharacter::ResetMountedDebugEncounter()
{
    if(!bMountedDebugEnabled||!bMountedExperiment||!MountedBoss)return;
    RecordMountedDebugEvent(TEXT("debug_reset_begin"));
    UGameplayStatics::SetGamePaused(this,false);bMountedDebugOwnedPause=false;
    MountedBoss->SetDebugPaused(false);MountedBoss->DebugCancelAttack();MountedBoss->ResetEncounter();MountedBoss->SetQAStationary(false);
    if(BattleFX)BattleFX->ClearMountedEffects();
    GetCharacterMovement()->SetMovementMode(MOVE_Walking);GetCharacterMovement()->StopMovementImmediately();ConsumeMovementInputVector();StopJumping();
    SetActorLocation(FVector(-2050,0,MountedBoss->GroundHeightAt(FVector(-2050,0,0))+90),false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(FRotator::ZeroRotator);
    if(Controller)Controller->SetControlRotation(FRotator(-10,0,0));
    Health=Stamina=100;DamageFlash=RegenDelay=AttackBuffer=DodgeBuffer=0;ForwardInput=RightInput=0;
    bSprint=bSprintHeld=bSprintExhausted=false;bEncounterActive=bLockedOn=false;bMountedDebugSingle=false;
    bAttackConnected=false;EndingTime=-1;RecordTime=0;SwordReadyTime=0;JumpVisualPhase=0;JumpVisualAge=0;
    SetAction(EAction::Idle);Feedback=TEXT("战斗已快速复位；E 进入，或数字键单招");FeedbackTime=3;
    RecordMountedDebugEvent(TEXT("debug_reset_complete"));
}

void AAshWellCombatCharacter::ResumeMountedDebugAI()
{
    if(!bMountedDebugEnabled||!bMountedExperiment||!MountedBoss)return;
    if(IsDead()||HasWon())ResetMountedDebugEncounter();
    UGameplayStatics::SetGamePaused(this,false);bMountedDebugOwnedPause=false;MountedBoss->SetDebugPaused(false);
    MountedBoss->DebugCancelAttack();MountedBoss->SetQAStationary(false);bMountedDebugSingle=false;
    if(GetActorLocation().X<-1400)SetActorLocation(FVector(-850,0,MountedBoss->GroundHeightAt(FVector(-850,0,0))+90),false,nullptr,ETeleportType::TeleportPhysics);
    bEncounterActive=true;MountedBoss->ActivateEncounter(this);bLockedOn=true;
    Feedback=TEXT("自然 AI 已恢复");FeedbackTime=2;RecordMountedDebugEvent(TEXT("debug_natural_ai"));
}

void AAshWellCombatCharacter::StartMountedDebugFixture(int32 Index)
{
    if(!bMountedDebugEnabled||!bMountedExperiment||!MountedBoss||Index<0||Index>=6)return;
    ResetMountedDebugEncounter();bMountedDebugSingle=true;bMountedDebugVisible=true;MountedDebugFixture=Index;
    MountedBoss->SetActorLocation(FVector::ZeroVector);MountedBoss->SetActorRotation(FRotator::ZeroRotator);
    MountedBoss->SetQAStationary(true);
    const FVector Positions[]={FVector(230,120,88),FVector(255,0,88),FVector(560,65,88),FVector(165,-55,88),FVector(185,130,88),FVector(380,-80,88)};
    FVector Position=Positions[Index];
    if(Index==2&&FParse::Param(FCommandLine::Get(),TEXT("MountedChargeSample")))Position.Y=105*MountedBoss->GetActorScale3D().X;
    Position.Z=MountedBoss->GroundHeightAt(Position)+GetCapsuleComponent()->GetScaledCapsuleHalfHeight()+2;
    SetActorLocation(Position,false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(FRotator(0,(-Position).Rotation().Yaw,0));
    if(Controller)Controller->SetControlRotation(FRotator(-10,(-Positions[Index]).Rotation().Yaw,0));
    bEncounterActive=true;bLockedOn=true;MountedBoss->ActivateEncounter(this);
    const bool Started=MountedBoss->ForceAttack(MountedFixtureNames[Index]);
    Feedback=Started?FString::Printf(TEXT("单招：%s；再次按 %d 重来，F5 自然 AI"),MountedFixtureLabels[Index],Index+1):TEXT("单招未启动，请检查调试启动参数");FeedbackTime=4;
    RecordMountedDebugEvent(Started?TEXT("fixture_start"):TEXT("fixture_failed"),MountedFixtureNames[Index]);
}

TArray<FString> AAshWellCombatCharacter::GetMountedDebugLines() const
{
    TArray<FString> Lines;if(!MountedBoss)return Lines;
    const auto Boss=MountedBoss->GetTelemetry();
    const bool Paused=UGameplayStatics::IsGamePaused(this);
    Lines.Add(FString::Printf(TEXT("%s  |  %s  |  %.2fx"),bMountedDebugSingle?TEXT("单招模式"):TEXT("自然 AI"),Paused?TEXT("已暂停"):TEXT("运行中"),UGameplayStatics::GetGlobalTimeDilation(this)));
    Lines.Add(FString::Printf(TEXT("Boss %s / %s  ·  序号 %d  ·  P%d"),*MountedBoss->GetStateLabel(),*MountedBoss->GetAttackLabel(),MountedBoss->GetAttackSerial(),MountedBoss->IsPhaseTwo()?2:1));
    Lines.Add(FString::Printf(TEXT("动作 %.3fs  ·  有效判定 %s"),MountedBoss->GetStateTime(),MountedBoss->IsHitWindowOpen()?TEXT("开启"):TEXT("关闭")));
    Lines.Add(FString::Printf(TEXT("前摇 %.2fs / 出手 %.2fs / 恢复 %.2fs"),Boss->GetNumberField(TEXT("windup_seconds")),Boss->GetNumberField(TEXT("active_seconds")),Boss->GetNumberField(TEXT("recovery_seconds"))));
    Lines.Add(FString::Printf(TEXT("锁向 %.2fs  ·  已锁 %s  ·  偏航 %.2f°"),Boss->GetNumberField(TEXT("commit_at_seconds")),Boss->GetBoolField(TEXT("heading_committed"))?TEXT("是"):TEXT("否"),MountedBoss->GetCommittedYawDrift()));
    Lines.Add(FString::Printf(TEXT("玩家 %s %.3fs  ·  无敌 %s  ·  HP %.0f / 体力 %.0f"),*GetCombatState(),StateTime,IsInvulnerable()?TEXT("开启"):TEXT("关闭"),Health,Stamina));
    Lines.Add(FString::Printf(TEXT("马速 %.0f cm/s  ·  命中 %d  ·  玩家受伤 %d"),Boss->GetNumberField(TEXT("actual_speed_cm_s")),MountedBoss->GetContactCount(),DamageTakenCount));
    Lines.Add(MountedRecording?TEXT("REC 连续录制（含主混音）；F8 停止保存"):TEXT("F8 开始连续录制（含主混音）"));
    Lines.Add(TEXT("F1 面板  F2 暂停  F3 慢放  F4 复位  F5 自然 AI"));
    Lines.Add(TEXT("1 横扫  2 下劈  3 冲锋  4 马肩撞  5 蹄击  6 跃盾"));
    Lines.Add(bMountedDebugLogFailed?TEXT("日志写入失败；详见 UE 日志"):FString(TEXT("日志："))+FPaths::GetCleanFilename(MountedDebugLogPath));
    Lines.Add(TEXT("记录输入与事件供追溯；不是逐帧确定性回放。"));
    return Lines;
}

void AAshWellCombatCharacter::ToggleMountedRecording()
{
    if(!bMountedDebugEnabled||!bMountedExperiment)return;
    if(!MountedRecording)
    {
        if(StartMountedCapture(this))
        {bMountedRecordingObserved=true;Feedback=TEXT("开始录制：原尺寸 / 24fps，F8 停止保存");FeedbackTime=3;RecordMountedDebugEvent(TEXT("record_start"),MountedRecordingPath);}
        else
        {Feedback=TEXT("录制未启动：游戏视口或输出目录不可用");FeedbackTime=4;RecordMountedDebugEvent(TEXT("record_start_failed"));}
    }
    else
    {
        const bool Saved=StopMountedCapture(this,TEXT("F8_stop"));Feedback=Saved?TEXT("录制已保存；帧间隙详情见 recording.json"):TEXT("录制保存不完整；请检查 recording.json");FeedbackTime=4;
        RecordMountedDebugEvent(TEXT("record_stop"),MountedRecordingPath);
    }
}

void AAshWellCombatCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if(bMountedDebugEnabled&&bMountedExperiment)
    {
        if(MountedRecording&&MountedRecordingOwner.Get()==this)
        {StopMountedCapture(this,FString::Printf(TEXT("actor_end_play_%d"),static_cast<int32>(EndPlayReason)));RecordMountedDebugEvent(TEXT("record_stop"),MountedRecordingPath);}
        RecordMountedDebugEvent(TEXT("session_end"),FString::FromInt(static_cast<int32>(EndPlayReason)));
        if(IsValid(MountedBoss.Get()))MountedBoss->SetDebugPaused(false);
        if(GetWorld())
        {
            if(bMountedDebugOwnedPause)UGameplayStatics::SetGamePaused(this,false);
            if(bMountedDebugOwnedSlow)UGameplayStatics::SetGlobalTimeDilation(this,1.f);
        }
        bMountedDebugLogReady=false;bMountedDebugEnabled=false;
    }
    Super::EndPlay(EndPlayReason);
}
