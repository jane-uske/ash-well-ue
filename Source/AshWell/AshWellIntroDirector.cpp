#include "AshWellIntroDirector.h"

#include "AshWellIntroHUD.h"
#include "Animation/AnimSequence.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Scene.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Sound/SoundAttenuation.h"

namespace
{
constexpr float CompanionWalkSpeed = 90.0f;
constexpr float WalkAnimationReferenceSpeed = 51.4f;
constexpr float FootstepSpacing = 36.0f;
}

AAshWellIntroDirector::AAshWellIntroDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    CompanionVisual = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("CompanionVisual"));
    CompanionVisual->SetupAttachment(SceneRoot);
    CompanionVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CompanionVisual->SetGenerateOverlapEvents(false);
    CompanionVisual->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

    CompanionLantern = CreateDefaultSubobject<UPointLightComponent>(TEXT("CompanionLantern"));
    CompanionLantern->SetupAttachment(SceneRoot);
    CompanionLantern->SetMobility(EComponentMobility::Movable);
    CompanionLantern->SetIntensityUnits(ELightUnits::Lumens);
    CompanionLantern->SetIntensity(140.0f);
    CompanionLantern->SetAttenuationRadius(500.0f);
    CompanionLantern->SetSourceRadius(5.0f);
    CompanionLantern->SetLightColor(FLinearColor(1.0f, 0.42f, 0.12f));

    Machinery = CreateDefaultSubobject<UAudioComponent>(TEXT("Machinery"));
    Machinery->SetupAttachment(SceneRoot);
    Machinery->bAutoActivate = false;
    Machinery->bAllowSpatialization = false;

    Air = CreateDefaultSubobject<UAudioComponent>(TEXT("Air"));
    Air->SetupAttachment(SceneRoot);
    Air->bAutoActivate = false;
    Air->bAllowSpatialization = false;
}

void AAshWellIntroDirector::BeginPlay()
{
    Super::BeginPlay();
    if (!GetWorld() || !GetWorld()->IsGameWorld())
    {
        SetActorTickEnabled(false);
        return;
    }

    StartTime = GetWorld()->GetTimeSeconds();
    Player = UGameplayStatics::GetPlayerPawn(this, 0);
    CompanionVisual->SetSkeletalMesh(CompanionMesh);
    CompanionVisual->SetRelativeScale3D(VisualScale);
    CompanionVisual->SetRelativeRotation(VisualRotation);
    if (IdleAnimation)
    {
        CompanionVisual->PlayAnimation(IdleAnimation, true);
    }
    PositionCompanion();

    CloseAttenuation = NewObject<USoundAttenuation>(this);
    CloseAttenuation->Attenuation.bAttenuate = true;
    CloseAttenuation->Attenuation.bSpatialize = true;
    CloseAttenuation->Attenuation.AttenuationShapeExtents = FVector(150.0f);
    CloseAttenuation->Attenuation.FalloffDistance = 1700.0f;

    DistantAttenuation = NewObject<USoundAttenuation>(this);
    DistantAttenuation->Attenuation.bAttenuate = true;
    DistantAttenuation->Attenuation.bSpatialize = true;
    DistantAttenuation->Attenuation.AttenuationShapeExtents = FVector(2500.0f);
    DistantAttenuation->Attenuation.FalloffDistance = 13000.0f;

    if (MachinerySound)
    {
        Machinery->SetSound(MachinerySound);
        Machinery->FadeIn(3.0f, MachineryVolume);
    }
    if (AirSound)
    {
        Air->SetSound(AirSound);
        Air->FadeIn(2.5f, 0.50f);
    }
    UpdateLantern();
    for(int32 I=1;I<=6;++I)
    {
        const FString Name=FString::Printf(TEXT("AW_Foley_WetStoneStep_%02d"),I);
        if(auto* Sound=LoadObject<USoundBase>(nullptr,*(FString(TEXT("/Game/AshWell/Intro/Audio/"))+Name+TEXT(".")+Name)))CompanionSteps.Add(Sound);
    }
    WriteRuntimeSnapshot();
}

FVector AAshWellIntroDirector::RoutePosition(float Parameter)
{
    if (Parameter <= 12.0f)
    {
        return FVector((-6.0f + Parameter) * 100.0f, 0.0f, 0.0f);
    }
    const float Q = (Parameter - 12.0f) / 20.0f;
    return FVector((6.0f + 18.0f * Q) * 100.0f,
        800.0f * Q * Q * (3.0f - 2.0f * Q), 0.0f);
}

void AAshWellIntroDirector::PositionCompanion()
{
    const FVector Position = RoutePosition(RouteParameter);
    const FVector Tangent = RoutePosition(RouteParameter + 0.01f) - Position;
    SetActorLocationAndRotation(Position, Tangent.Rotation());
}

double AAshWellIntroDirector::ElapsedTime() const
{
    return GetWorld() ? GetWorld()->GetTimeSeconds() - StartTime : 0.0;
}

void AAshWellIntroDirector::SetCaption(const FString& Text, float Duration)
{
    if (APlayerController* Controller = UGameplayStatics::GetPlayerController(this, 0))
    {
        if (AAshWellIntroHUD* HUD = Cast<AAshWellIntroHUD>(Controller->GetHUD()))
        {
            HUD->SetSubtitle(Text, Duration);
        }
    }
}

void AAshWellIntroDirector::BeginWalk()
{
    Phase = EIntroPhase::Walking;
    if (WalkAnimation)
    {
        CompanionVisual->PlayAnimation(WalkAnimation, true);
        CompanionVisual->SetPlayRate(CompanionWalkSpeed / WalkAnimationReferenceSpeed);
    }
    SetCaption(TEXT("跟紧我。别看下面。"), 3.0f);
}

void AAshWellIntroDirector::BeginHush()
{
    Phase = EIntroPhase::Hush;
    HushStartTime = ElapsedTime();
    if (StopAnimation)
    {
        CompanionVisual->PlayAnimation(StopAnimation, false);
    }
    SetCaption(TEXT("停。……听。"), 4.0f);
    if (HushSound)
    {
        UGameplayStatics::PlaySoundAtLocation(this, HushSound,
            GetActorLocation() + FVector(0.0f, 0.0f, 160.0f),
            0.48f, 1.0f, 0.0f, CloseAttenuation);
    }
    if (MachinerySound)
    {
        Machinery->AdjustVolume(0.7f, MachineryVolume * 0.4f);
    }
}

void AAshWellIntroDirector::BeginListening()
{
    Phase = EIntroPhase::Listening;
    if (DistantMetalSound)
    {
        UGameplayStatics::PlaySoundAtLocation(this, DistantMetalSound,
            FVector(5500.0f, 2700.0f, 600.0f), 0.65f, 1.0f, 0.0f, DistantAttenuation);
    }
    if (MachinerySound)
    {
        Machinery->AdjustVolume(3.0f, MachineryVolume);
    }
    SetCaption(TEXT("下面还有人。"), 4.0f);
}

void AAshWellIntroDirector::UpdateLantern()
{
    const FVector LightPosition = CompanionVisual->GetBoneIndex(LanternBone) != INDEX_NONE
        ? CompanionVisual->GetBoneLocation(LanternBone, EBoneSpaces::WorldSpace)
        : GetActorTransform().TransformPosition(FVector(20.0f, 35.0f, 70.0f));
    CompanionLantern->SetWorldLocation(LightPosition);
    const double Time = ElapsedTime();
    const float Flicker = 1.0f + 0.019f * FMath::Sin(Time * 7.1)
        + 0.011f * FMath::Sin(Time * 13.7 + 0.6);
    CompanionLantern->SetIntensity(140.0f * Flicker);
}

void AAshWellIntroDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!GetWorld() || !GetWorld()->IsGameWorld())
    {
        return;
    }
    if (!Player.IsValid())
    {
        Player = UGameplayStatics::GetPlayerPawn(this, 0);
    }

    if (Player.IsValid())
    {
        const FVector PlayerPosition = Player->GetActorLocation();
        if (Phase == EIntroPhase::Waiting && PlayerPosition.X > 500.0f)
        {
            BeginWalk();
        }

        if (Phase == EIntroPhase::Walking)
        {
            // Parameter spacing is not arc length; account for the bend so
            // the worker keeps a consistent speed through the bend.
            const float CentimetresPerParameter = static_cast<float>(
                (RoutePosition(RouteParameter + 0.01f) - RoutePosition(RouteParameter)).Size()) / 0.01f;
            const FVector PreviousPosition = GetActorLocation();
            RouteParameter = FMath::Min(24.0f,
                RouteParameter + CompanionWalkSpeed * DeltaSeconds / FMath::Max(1.0f, CentimetresPerParameter));
            PositionCompanion();
            FootTravel+=FVector::Dist2D(PreviousPosition,GetActorLocation());
            if(FootTravel>=FootstepSpacing&&CompanionSteps.Num())
            {
                FootTravel-=FootstepSpacing;
                UGameplayStatics::PlaySoundAtLocation(this,CompanionSteps[FootCount++%CompanionSteps.Num()],GetActorLocation(),.28f,1.f,0.f,CloseAttenuation);
            }
            if (RouteParameter >= 24.0f)
            {
                Phase = EIntroPhase::AwaitingPlayer;
                if (IdleAnimation)
                {
                    CompanionVisual->PlayAnimation(IdleAnimation, true);
                }
            }
        }

        if (Phase == EIntroPhase::AwaitingPlayer &&
            (FVector::Dist2D(PlayerPosition, GetActorLocation()) <= 650.0f || PlayerPosition.X > 950.0f))
        {
            BeginHush();
        }
    }

    if (Phase == EIntroPhase::Hush || Phase == EIntroPhase::Listening)
    {
        const float HushElapsed = static_cast<float>(ElapsedTime() - HushStartTime);
        if (StopAnimation && !bStopPoseHeld && HushElapsed >= StopAnimation->GetPlayLength())
        {
            CompanionVisual->SetPosition(FMath::Max(0.0f, StopAnimation->GetPlayLength() - 0.001f), false);
            CompanionVisual->bPauseAnims = true;
            bStopPoseHeld = true;
        }
        if (Phase == EIntroPhase::Hush && HushElapsed >= 4.0f)
        {
            BeginListening();
        }
    }

    UpdateLantern();
    SnapshotCountdown -= DeltaSeconds;
    if (SnapshotCountdown <= 0.0f)
    {
        SnapshotCountdown = 1.0f;
        WriteRuntimeSnapshot();
    }
}

FString AAshWellIntroDirector::GetPhaseName() const
{
    switch (Phase)
    {
        case EIntroPhase::Waiting: return TEXT("waiting");
        case EIntroPhase::Walking: return TEXT("walking");
        case EIntroPhase::AwaitingPlayer: return TEXT("awaiting_player");
        case EIntroPhase::Hush: return TEXT("hush");
        case EIntroPhase::Listening: return TEXT("listening");
    }
    return TEXT("unknown");
}

void AAshWellIntroDirector::WriteRuntimeSnapshot() const
{
    if (!GetWorld() || !GetWorld()->IsGameWorld())
    {
        return;
    }
    auto PositionObject = [](const FVector& Position)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetNumberField(TEXT("x"), Position.X);
        Object->SetNumberField(TEXT("y"), Position.Y);
        Object->SetNumberField(TEXT("z"), Position.Z);
        return Object;
    };
    TSharedRef<FJsonObject> Snapshot = MakeShared<FJsonObject>();
    Snapshot->SetStringField(TEXT("phase"), GetPhaseName());
    Snapshot->SetNumberField(TEXT("elapsed_seconds"), ElapsedTime());
    Snapshot->SetNumberField(TEXT("route_parameter"), RouteParameter);
    Snapshot->SetStringField(TEXT("position_units"), TEXT("centimetres"));
    Snapshot->SetObjectField(TEXT("companion_position"), PositionObject(GetActorLocation()));
    if (Player.IsValid())
    {
        Snapshot->SetObjectField(TEXT("player_position"), PositionObject(Player->GetActorLocation()));
    }
    Snapshot->SetBoolField(TEXT("stop_pose_held"), bStopPoseHeld);
    FString Serialized;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Serialized);
    FJsonSerializer::Serialize(Snapshot, Writer);

    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Automation"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString File = FPaths::Combine(Directory, TEXT("intro-director-runtime.json"));
    const FString TemporaryFile = File + TEXT(".tmp");
    if (FFileHelper::SaveStringToFile(Serialized, *TemporaryFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        IFileManager::Get().Move(*File, *TemporaryFile, true, true, false, true);
    }
}
