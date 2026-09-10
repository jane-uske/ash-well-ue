#include "AshWellCombatArena.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "AshWellChapterDirector.h"
#include "AshWellSession.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Sound/SoundBase.h"

AAshWellCombatArena::AAshWellCombatArena()
{
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ArenaRoot"));
    SceneRoot->SetMobility(EComponentMobility::Static);
    SetRootComponent(SceneRoot);

    MachineryAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("PoweredMachinery"));
    MachineryAudio->SetupAttachment(SceneRoot);
    MachineryAudio->bAutoActivate = false;
    MachineryAudio->bAllowSpatialization = false;
    MachineryAudio->SetVolumeMultiplier(0.32f);
}

FVector AAshWellCombatArena::GetArenaCenter() const
{
    return GetActorTransform().TransformPosition(LocalCenter);
}

FVector AAshWellCombatArena::GetPlayerStart() const
{
    return GetActorTransform().TransformPosition(LocalCenter + FVector(-420.f, -120.f, 90.f));
}

FVector AAshWellCombatArena::GetEnemyStart() const
{
    return GetActorTransform().TransformPosition(LocalCenter + FVector(300.f, 140.f, 0.f));
}

FVector AAshWellCombatArena::GetConsoleLocation() const
{
    return GetActorTransform().TransformPosition(LocalCenter + FVector(-240.f, -120.f, 100.f));
}

FVector AAshWellCombatArena::GetArrivalStart() const { return GetActorTransform().TransformPosition(LocalCenter+FVector(-1120,-300,90)); }
FVector AAshWellCombatArena::GetLiftPoint() const { return GetActorTransform().TransformPosition(LocalCenter+FVector(920,0,90)); }

UStaticMeshComponent* AAshWellCombatArena::AddMesh(const FString& Name, UStaticMesh* Mesh,
    const FVector& Position, const FVector& Scale, const FRotator& Rotation,
    UMaterialInterface* Material, bool bSolid, USceneComponent* Parent, bool bMovable)
{
    UStaticMeshComponent* Component = NewObject<UStaticMeshComponent>(this, FName(*Name));
    AddInstanceComponent(Component);
    Component->SetupAttachment(Parent ? Parent : SceneRoot.Get());
    Component->SetMobility(bMovable ? EComponentMobility::Movable : EComponentMobility::Static);
    Component->SetStaticMesh(Mesh);
    Component->SetRelativeLocation(Position);
    Component->SetRelativeRotation(Rotation);
    Component->SetRelativeScale3D(Scale);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCollisionProfileName(bSolid ? FName(TEXT("BlockAll")) : FName(TEXT("NoCollision")));
    Component->SetCanEverAffectNavigation(bSolid);
    if (Material) Component->SetMaterial(0, Material);
    Component->RegisterComponent();
    return Component;
}

UPointLightComponent* AAshWellCombatArena::AddLamp(const FString& Name, const FVector& Position,
    const FLinearColor& Color, float Intensity, float Radius)
{
    UPointLightComponent* Lamp = NewObject<UPointLightComponent>(this, FName(*Name));
    AddInstanceComponent(Lamp);
    Lamp->SetupAttachment(SceneRoot);
    Lamp->SetMobility(EComponentMobility::Movable);
    Lamp->SetRelativeLocation(Position);
    Lamp->IntensityUnits = ELightUnits::Lumens;
    Lamp->SetLightColor(Color);
    Lamp->SetIntensity(Intensity);
    Lamp->SetAttenuationRadius(Radius);
    Lamp->SetCastShadows(false);
    Lamp->VolumetricScatteringIntensity = 0.3f;
    Lamp->RegisterComponent();
    return Lamp;
}

void AAshWellCombatArena::AddBarrier(const FString& Name, const FVector& Position,
    const FVector& HalfSize, const FRotator& Rotation)
{
    UBoxComponent* Barrier = NewObject<UBoxComponent>(this, FName(*Name));
    AddInstanceComponent(Barrier);
    Barrier->SetupAttachment(SceneRoot);
    Barrier->SetMobility(EComponentMobility::Static);
    Barrier->SetRelativeLocation(Position);
    Barrier->SetRelativeRotation(Rotation);
    Barrier->SetBoxExtent(HalfSize);
    Barrier->SetCollisionProfileName(TEXT("BlockAll"));
    Barrier->SetGenerateOverlapEvents(false);
    Barrier->SetHiddenInGame(true);
    Barrier->RegisterComponent();
}

void AAshWellCombatArena::AddRail(const FString& Name, const FVector& Start, const FVector& End)
{
    const FVector Delta = End - Start;
    const float Length = Delta.Size2D();
    const FRotator Yaw(0.f, FMath::RadiansToDegrees(FMath::Atan2(Delta.Y, Delta.X)), 0.f);
    const FVector Middle = (Start + End) * 0.5f;
    AddBarrier(Name + TEXT("_Safety"), Middle + FVector(0.f, 0.f, 70.f),
        FVector(Length * 0.5f + 4.f, 7.f, 70.f), Yaw);
    AddMesh(Name + TEXT("_Cap"), Cube, Middle + FVector(0.f, 0.f, 112.f),
        FVector(Length / 100.f, 0.065f, 0.07f), Yaw, Rust);
    AddMesh(Name + TEXT("_Mid"), Cube, Middle + FVector(0.f, 0.f, 57.f),
        FVector(Length / 100.f, 0.04f, 0.05f), Yaw, Steel);
    AddMesh(Name + TEXT("_Toe"), Cube, Middle + FVector(0.f, 0.f, 8.f),
        FVector(Length / 100.f, 0.08f, 0.16f), Yaw, Rust);
    const int32 Spans = FMath::Max(1, FMath::CeilToInt(Length / 180.f));
    for (int32 I = 0; I <= Spans; ++I)
    {
        const FVector Position = FMath::Lerp(Start, End, static_cast<float>(I) / Spans);
        AddMesh(FString::Printf(TEXT("%s_Post_%02d"), *Name, I), Cube,
            Position + FVector(0.f, 0.f, 56.f), FVector(0.085f, 0.085f, 1.12f), Yaw, Steel);
    }
}

void AAshWellCombatArena::BuildDeck()
{
    // A single simple-collision slab avoids gaps, seams, and tiny step-up obstacles.
    AddMesh(TEXT("DeckStructure"), Cube, LocalCenter + FVector(0.f, 0.f, -22.f),
        FVector(14.f, 13.f, 0.44f), FRotator::ZeroRotator, Concrete, true);
    // Surface tiles are visual only, inset below the collision surface.
    for (int32 X = 0; X < 7; ++X)
    {
        for (int32 Y = 0; Y < 7; ++Y)
        {
            const FVector P = LocalCenter + FVector(-600.f + X * 200.f, -555.f + Y * 185.f, -1.f);
            AddMesh(FString::Printf(TEXT("DeckPanel_%d_%d"), X, Y), Cube, P,
                FVector(1.96f, 1.81f, 0.025f), FRotator::ZeroRotator, ((X + Y) % 4 == 0) ? Steel : Stone);
        }
        AddMesh(FString::Printf(TEXT("LowerCrossbeam_%d"), X), Cube,
            LocalCenter + FVector(-600.f + X * 200.f, 0.f, -60.f),
            FVector(0.23f, 13.3f, 0.7f), FRotator::ZeroRotator, Rust);
    }
    AddMesh(TEXT("FrontGirder"), Cube, LocalCenter + FVector(0.f, -635.f, -69.f),
        FVector(14.25f, 0.32f, 1.25f), FRotator::ZeroRotator, Rust);
    AddMesh(TEXT("BackGirder"), Cube, LocalCenter + FVector(0.f, 635.f, -69.f),
        FVector(14.25f, 0.32f, 1.25f), FRotator::ZeroRotator, Rust);

    AddRail(TEXT("SouthRail"), LocalCenter + FVector(-690.f, -640.f, 0.f), LocalCenter + FVector(690.f, -640.f, 0.f));
    AddRail(TEXT("NorthRail"), LocalCenter + FVector(-690.f, 640.f, 0.f), LocalCenter + FVector(690.f, 640.f, 0.f));
    AddRail(TEXT("EastRailLower"), LocalCenter + FVector(690.f, -640.f, 0.f), LocalCenter + FVector(690.f, -160.f, 0.f));
    AddRail(TEXT("EastRailUpper"), LocalCenter + FVector(690.f, 160.f, 0.f), LocalCenter + FVector(690.f, 640.f, 0.f));
    // The west opening lines up with the original bridge's end at Y = 800 cm.
    AddRail(TEXT("WestRailLower"), LocalCenter + FVector(-690.f, -640.f, 0.f), LocalCenter + FVector(-690.f, -440.f, 0.f));
    AddRail(TEXT("WestRailUpper"), LocalCenter + FVector(-690.f, -160.f, 0.f), LocalCenter + FVector(-690.f, 640.f, 0.f));

    // Low equipment provides two readable obstacles without hiding the attack silhouettes.
    for (int32 I = 0; I < 2; ++I)
    {
        const FVector P = LocalCenter + (I == 0 ? FVector(-460.f, 390.f, 0.f) : FVector(420.f, -380.f, 0.f));
        AddMesh(FString::Printf(TEXT("ServicePlinth_%d"), I), Cube, P + FVector(0.f, 0.f, 14.f),
            FVector(1.65f, 1.3f, 0.28f), FRotator::ZeroRotator, Concrete, true);
        AddMesh(FString::Printf(TEXT("ServiceHousing_%d"), I), Cylinder, P + FVector(0.f, 0.f, 49.f),
            FVector(1.1f, 1.1f, 0.7f), FRotator::ZeroRotator, Rust, true);
        AddMesh(FString::Printf(TEXT("ServiceCap_%d"), I), Cylinder, P + FVector(0.f, 0.f, 88.f),
            FVector(1.22f, 1.22f, 0.09f), FRotator::ZeroRotator, Steel);
        AddMesh(FString::Printf(TEXT("ServicePipe_%d"), I), Cylinder, P + FVector(0.f, 80.f, 33.f),
            FVector(0.26f, 0.26f, 1.4f), FRotator(0.f, 0.f, 90.f), Rust);
    }

    const FLinearColor Warm(1.f, 0.42f, 0.15f);
    AddLamp(TEXT("EntryWorklight"), LocalCenter + FVector(-450.f, -340.f, 460.f), Warm, 4100.f, 1300.f);
    AddLamp(TEXT("WellBounce"), LocalCenter + FVector(200.f, 0.f, 680.f),
        FLinearColor(0.24f, 0.47f, 0.66f), 3500.f, 1700.f);
    const FVector LampPositions[] = {
        FVector(-610.f, -540.f, 150.f), FVector(-600.f, 535.f, 150.f),
        FVector(-70.f, -540.f, 150.f), FVector(50.f, 535.f, 150.f),
        FVector(600.f, -540.f, 150.f), FVector(600.f, 535.f, 150.f)
    };
    for (int32 I = 0; I < UE_ARRAY_COUNT(LampPositions); ++I)
    {
        const FVector P = LocalCenter + LampPositions[I];
        AddMesh(FString::Printf(TEXT("LampMast_%d"), I), Cube, P - FVector(0.f, 0.f, 70.f),
            FVector(0.10f, 0.1f, 1.6f), FRotator::ZeroRotator, Steel);
        AddMesh(FString::Printf(TEXT("LampCage_%d"), I), Cube, P + FVector(0.f, 0.f, 9.f),
            FVector(0.3f, 0.3f, 0.08f), FRotator::ZeroRotator, Rust);
        AddMesh(FString::Printf(TEXT("LampGlass_%d"), I), Sphere, P,
            FVector(0.16f, 0.16f, 0.20f), FRotator::ZeroRotator, Amber);
        SequenceLamps.Add(AddLamp(FString::Printf(TEXT("SequentialLight_%d"), I), P, Warm, 0.f, 620.f));
    }
}

void AAshWellCombatArena::BuildConnection()
{
    // LocalCenter - (1200, 300) is the established bridge endpoint, (2400, 800).
    const FVector Start = LocalCenter + FVector(-1230.f, -300.f, 0.f);
    const FVector End = LocalCenter + FVector(-650.f, -300.f, 0.f);
    const FVector Middle = (Start + End) * 0.5f;
    AddMesh(TEXT("BridgeConnector"), Cube, Middle - FVector(0.f, 0.f, 15.f),
        FVector(5.8f, 2.8f, 0.30f), FRotator::ZeroRotator, Steel, true);
    AddRail(TEXT("ConnectorLeft"), Start + FVector(0.f, -135.f, 0.f), End + FVector(0.f, -135.f, 0.f));
    AddRail(TEXT("ConnectorRight"), Start + FVector(0.f, 135.f, 0.f), End + FVector(0.f, 135.f, 0.f));
    for (int32 I = 0; I < 7; ++I)
    {
        AddMesh(FString::Printf(TEXT("BridgeSeam_%d"), I), Cube,
            Start + FVector(30.f + I * 85.f, 0.f, 0.2f),
            FVector(0.035f, 2.7f, 0.018f), FRotator::ZeroRotator, Rust);
    }
}

void AAshWellCombatArena::BuildSwitchgear()
{
    const FVector Base = LocalCenter + FVector(-240.f, -120.f, 0.f);
    AddMesh(TEXT("SwitchgearFoot"), Cube, Base + FVector(0.f, 0.f, 8.f),
        FVector(0.70f, 0.70f, 0.16f), FRotator::ZeroRotator, Rust, true);
    AddMesh(TEXT("SwitchgearCabinet"), Cube, Base + FVector(0.f, 0.f, 57.f),
        FVector(0.50f, 0.62f, 0.98f), FRotator::ZeroRotator, Steel, true);
    AddMesh(TEXT("SwitchgearPanel"), Cube, Base + FVector(-26.f, 0.f, 92.f),
        FVector(0.05f, 0.52f, 0.34f), FRotator(0.f, 0.f, -10.f), Rust);
    for (int32 I = 0; I < 3; ++I)
    {
        AddMesh(FString::Printf(TEXT("Meter_%d"), I), Cylinder,
            Base + FVector(-30.f, -17.f + I * 17.f, 103.f),
            FVector(0.10f, 0.10f, 0.04f), FRotator(90.f, 0.f, 0.f), Amber);
    }
    ConsoleLamp = AddLamp(TEXT("ConsolePilot"), Base + FVector(-44.f, 0.f, 114.f),
        FLinearColor(1.f, 0.38f, 0.10f), 85.f, 235.f);

    LeverPivot = NewObject<USceneComponent>(this, TEXT("PowerLever"));
    AddInstanceComponent(LeverPivot);
    LeverPivot->SetupAttachment(SceneRoot);
    LeverPivot->SetMobility(EComponentMobility::Movable);
    LeverPivot->SetRelativeLocation(Base + FVector(-31.f, 0.f, 72.f));
    LeverPivot->RegisterComponent();
    AddMesh(TEXT("LeverStem"), Cylinder, FVector(-12.f, 0.f, 9.f), FVector(0.025f, 0.025f, 0.30f),
        FRotator(-50.f, 0.f, 0.f), Rust, false, LeverPivot, true);
    AddMesh(TEXT("LeverGrip"), Cylinder, FVector(-23.f, 0.f, 17.f), FVector(0.07f, 0.07f, 0.24f),
        FRotator(0.f, 0.f, 90.f), Steel, false, LeverPivot, true);
}

void AAshWellCombatArena::BuildTurbine()
{
    // Machinery sits beyond the north railing so its bulk cannot obstruct the encounter.
    const FVector Base = LocalCenter + FVector(180.f, 815.f, 175.f);
    AddMesh(TEXT("TurbineBed"), Cube, Base + FVector(0.f, 0.f, -185.f),
        FVector(5.8f, 3.8f, 0.6f), FRotator::ZeroRotator, Concrete);
    AddMesh(TEXT("TurbineRear"), Cylinder, Base + FVector(0.f, 105.f, 0.f),
        FVector(4.8f, 4.8f, 2.1f), FRotator(0.f, 0.f, 90.f), Steel);
    AddMesh(TEXT("TurbineDarkFace"), Cylinder, Base + FVector(0.f, -7.f, 0.f),
        FVector(4.5f, 4.5f, 0.11f), FRotator(0.f, 0.f, 90.f), Steel);
    for (int32 I = 0; I < 16; ++I)
    {
        const float Angle = I * 2.f * PI / 16.f;
        const FVector RingOffset(FMath::Cos(Angle) * 222.f, -24.f, FMath::Sin(Angle) * 222.f);
        AddMesh(FString::Printf(TEXT("TurbineRim_%d"), I), Cube, Base + RingOffset,
            FVector(0.20f, 0.36f, 0.9f), FRotator(-FMath::RadiansToDegrees(Angle), 0.f, 0.f), Rust);
    }
    Rotor = NewObject<USceneComponent>(this, TEXT("PoweredRotor"));
    AddInstanceComponent(Rotor);
    Rotor->SetupAttachment(SceneRoot);
    Rotor->SetMobility(EComponentMobility::Movable);
    Rotor->SetRelativeLocation(Base + FVector(0.f, -39.f, 0.f));
    Rotor->RegisterComponent();
    AddMesh(TEXT("RotorHub"), Cylinder, FVector::ZeroVector, FVector(0.75f, 0.75f, 0.45f),
        FRotator(0.f, 0.f, 90.f), Rust, false, Rotor, true);
    for (int32 I = 0; I < 6; ++I)
    {
        const float Angle = I * 2.f * PI / 6.f;
        AddMesh(FString::Printf(TEXT("RotorBlade_%d"), I), Cube,
            FVector(FMath::Cos(Angle) * 106.f, 0.f, FMath::Sin(Angle) * 106.f),
            FVector(1.95f, 0.19f, 0.43f), FRotator(-FMath::RadiansToDegrees(Angle), 0.f, 0.f), Rust,
            false, Rotor, true);
    }
    for (int32 I = 0; I < 2; ++I)
    {
        const FVector P = Base + FVector(I == 0 ? -270.f : 270.f, 70.f, 75.f);
        AddMesh(FString::Printf(TEXT("TurbinePipe_%d"), I), Cylinder, P,
            FVector(0.8f, 0.8f, 6.f), FRotator::ZeroRotator, Rust);
        AddMesh(FString::Printf(TEXT("TurbinePipeBand_%d"), I), Cylinder, P + FVector(0.f, 0.f, 45.f),
            FVector(1.0f, 1.0f, 0.16f), FRotator::ZeroRotator, Steel);
    }
    SequenceLamps.Add(AddLamp(TEXT("MachineFlood"), Base + FVector(-280.f, -210.f, 190.f),
        FLinearColor(1.f, 0.52f, 0.25f), 0.f, 1600.f));
}

void AAshWellCombatArena::BeginPlay()
{
    Super::BeginPlay();
    bGrandEncounter=AAshWellChapterDirector::Find(GetWorld())!=nullptr;
    if(bGrandEncounter)
    {
        const FVector Anchor(2400,800,0),Scale(1.65,1.65,1);
        SceneRoot->SetMobility(EComponentMobility::Movable);
        SetActorScale3D(Scale);SetActorLocation(Anchor-Anchor*Scale);
        SceneRoot->SetMobility(EComponentMobility::Static);
    }
    Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    Cylinder = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Steel = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/AshWell/Materials/V2/M_OldSteel.M_OldSteel"));
    Rust = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/AshWell/Materials/V2/M_Rust.M_Rust"));
    Stone = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/AshWell/Materials/V2/M_WetStone.M_WetStone"));
    Concrete = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/AshWell/Materials/V2/M_Concrete.M_Concrete"));
    Amber = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/AshWell/Materials/M_Amber.M_Amber"));
    if (!Cube || !Cylinder || !Sphere || !Steel || !Rust || !Stone || !Concrete || !Amber)
    {
        UE_LOG(LogTemp, Error, TEXT("ASHWELL CombatArena: required mesh or material was not found."));
        return;
    }
    RelaySound = LoadObject<USoundBase>(nullptr, TEXT("/Game/AshWell/Intro/Audio/AW_Foley_LanternGear_03.AW_Foley_LanternGear_03"));
    LoadShiftSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/AshWell/Intro/Audio/AW_Event_DistantLoadShift.AW_Event_DistantLoadShift"));
    MachineryAudio->SetSound(LoadObject<USoundBase>(nullptr,
        TEXT("/Game/AshWell/Intro/Audio/AW_Amb_MachineryLoop.AW_Amb_MachineryLoop")));
    BuildDeck();
    BuildConnection();
    BuildSwitchgear();
    BuildTurbine();
    BuildExit();BuildPolishDetails();if(bGrandEncounter){BuildEntry();if(!FParse::Param(FCommandLine::Get(),TEXT("BattleBaseline")))BuildBattleAtmosphere();}
    const TCHAR* Tracks[]={TEXT("AW_Polish_Ambient"),TEXT("AW_Polish_Combat"),TEXT("AW_Polish_Overload")};
    for(int32 I=0;I<3;++I)
    {
        auto* Audio=NewObject<UAudioComponent>(this);AddInstanceComponent(Audio);Audio->SetupAttachment(SceneRoot);
        Audio->bAutoActivate=false;Audio->bAllowSpatialization=false;
        const FString Asset=FString(TEXT("/Game/AshWell/Combat/Polish/"))+Tracks[I]+TEXT(".")+Tracks[I];
        Audio->SetSound(LoadObject<USoundBase>(nullptr,*Asset));
#if !UE_BUILD_SHIPPING
        if(I==1&&bGrandEncounter)
            if(auto* Suno=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/GrandEncounter/AW_Suno_Warden_Combat.AW_Suno_Warden_Combat"))){Audio->SetSound(Suno);bSunoMusic=true;}
#endif
        Audio->RegisterComponent();
        Audio->SetVolumeMultiplier(I==0?.22f:0.f);Audio->Play();if(I==1&&bSunoMusic)Audio->Stop();MusicLayers.Add(Audio);
    }
    WardenVoice=NewObject<UAudioComponent>(this,TEXT("WardenLastWords"));AddInstanceComponent(WardenVoice);
    WardenVoice->SetupAttachment(SceneRoot);WardenVoice->bAutoActivate=false;WardenVoice->bAllowSpatialization=false;
    WardenVoice->SetSound(LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Polish/AW_Polish_Voice.AW_Polish_Voice")));WardenVoice->RegisterComponent();
    UE_LOG(LogTemp, Display, TEXT("ASHWELL CombatArena: built maintenance deck at %s; %d sequential lamps; collision slab at Z=0."),
        *GetArenaCenter().ToCompactString(), SequenceLamps.Num());
}

void AAshWellCombatArena::PowerOn()
{
    if (bPowered) return;
    bPowered = true;
    PowerElapsed = 0.f;
    if (ConsoleLamp) ConsoleLamp->SetIntensity(170.f);
    if (RelaySound) UGameplayStatics::PlaySoundAtLocation(this, RelaySound, GetConsoleLocation(), 0.7f, 0.75f);
    if (LoadShiftSound) UGameplayStatics::PlaySoundAtLocation(this, LoadShiftSound,
        GetArenaCenter() + FVector(900.f, 1200.f, -300.f), 0.45f, 0.85f);
    if (MachineryAudio && MachineryAudio->Sound) MachineryAudio->FadeIn(3.5f, 0.30f);
    if(MusicLayers.Num()==3){if(bSunoMusic&&!MusicLayers[1]->IsPlaying())MusicLayers[1]->Play();MusicLayers[1]->AdjustVolume(2.7f,bSunoMusic?.7f:.32f);}
    UE_LOG(LogTemp, Display, TEXT("ASHWELL CombatArena: power on."));
}

void AAshWellCombatArena::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if(ImpactDuckTime>0)
    {
        ImpactDuckTime-=float(FApp::GetDeltaTime());
        if(ImpactDuckTime<=0&&MusicLayers.Num()==3&&!bFinished)MusicLayers[1]->AdjustVolume(.16f,bSunoMusic?.7f:.32f);
    }
    if(bEntryOpening&&EntryTime<2.7f)
    {
        EntryTime=FMath::Min(2.7f,EntryTime+DeltaSeconds);
        const float Open=FMath::SmoothStep(0.f,2.7f,EntryTime)*145.f;
        EntryLeft->SetRelativeLocation(LocalCenter+FVector(-697,-370-Open,300));
        EntryRight->SetRelativeLocation(LocalCenter+FVector(-697,-230+Open,300));
    }
    if (!bPowered) return;
    if(bFinished)
    {
        FinishTime+=DeltaSeconds;
        if(Rotor&&FinishTime<2.f)Rotor->AddLocalRotation(FRotator(42.f*(1-FinishTime/2.f)*DeltaSeconds,0,0));
        if(ExitGate)ExitGate->SetRelativeLocation(LocalCenter+FVector(705,0,135+FMath::SmoothStep(4.f,7.f,FinishTime)*300));
        if(WardenVoice&&FinishTime>=2.f&&FinishTime-DeltaSeconds<2.f)WardenVoice->Play();
        if(bDeparting)
        {
            DepartureTime+=DeltaSeconds;
            LiftRoot->SetRelativeLocation(LocalCenter+FVector(920,0,FMath::Min(DepartureTime,5.f)*75.f));
        }
        return;
    }
    PowerElapsed += DeltaSeconds;
    if (LeverPivot) LeverPivot->SetRelativeRotation(FRotator(FMath::Lerp(0.f, -68.f,
        FMath::Clamp(PowerElapsed / 0.45f, 0.f, 1.f)), 0.f, 0.f));
    for (int32 I = 0; I < SequenceLamps.Num(); ++I)
    {
        const float Delay = 0.4f + I * 0.43f;
        const float Fade = FMath::Clamp((PowerElapsed - Delay) / 0.22f, 0.f, 1.f);
        SequenceLamps[I]->SetIntensity(Fade * (I == SequenceLamps.Num() - 1 ? 7000.f : 1200.f));
        if (I == RelaysFired && PowerElapsed >= Delay)
        {
            if (RelaySound) UGameplayStatics::PlaySoundAtLocation(this, RelaySound,
                SequenceLamps[I]->GetComponentLocation(), 0.27f, 0.85f + 0.035f * I);
            ++RelaysFired;
        }
    }
    if (Rotor)
    {
        const float Speed = FMath::Lerp(0.f, 42.f, FMath::Clamp((PowerElapsed - 1.5f) / 5.f, 0.f, 1.f));
        Rotor->AddLocalRotation(FRotator(Speed * DeltaSeconds, 0.f, 0.f));
    }
}

void AAshWellCombatArena::SetOverload()
{
    if(bOverloaded)return;bOverloaded=true;
    if(MusicLayers.Num()==3)MusicLayers[2]->AdjustVolume(1.5f,.30f);
    for(const auto& Lamp:SequenceLamps)Lamp->SetLightColor(FLinearColor(1,.20,.055));
    if(LoadShiftSound)UGameplayStatics::PlaySoundAtLocation(this,LoadShiftSound,GetEnemyStart(),.8f,.72f);
}
void AAshWellCombatArena::FinishEncounter()
{
    if(bFinished)return;bFinished=true;
    if(MachineryAudio)MachineryAudio->FadeOut(.6f,0.f);
    for(const auto& Layer:MusicLayers)Layer->AdjustVolume(.7f,.035f);
    for(const auto& Lamp:SequenceLamps)Lamp->SetLightColor(FLinearColor(.35f,.55f,.65f));
    UE_LOG(LogTemp,Display,TEXT("AW_ENDING machinery_stopped"));
}
void AAshWellCombatArena::Depart()
{
    if(!bFinished||FinishTime<7.f||bDeparting)return;
    bDeparting=true;
    if(LoadShiftSound)UGameplayStatics::PlaySoundAtLocation(this,LoadShiftSound,GetLiftPoint(),.55f,.8f);
    UE_LOG(LogTemp,Display,TEXT("AW_ENDING lift_departure"));
}
void AAshWellCombatArena::BuildExit()
{
    LiftRoot=NewObject<USceneComponent>(this,TEXT("ServiceLift"));AddInstanceComponent(LiftRoot);
    LiftRoot->SetupAttachment(SceneRoot);LiftRoot->SetMobility(EComponentMobility::Movable);
    LiftRoot->SetRelativeLocation(LocalCenter+FVector(920,0,0));LiftRoot->RegisterComponent();
    AddMesh(TEXT("LiftFloor"),Cube,FVector(0,0,-18),FVector(4.6,3.2,.36),FRotator::ZeroRotator,Steel,true,LiftRoot,true);
    for(int32 I=-1;I<=1;I+=2)
    {
        AddMesh(FString::Printf(TEXT("LiftSide%d"),I),Cube,FVector(0,I*158,65),FVector(4.6,.10,1.3),FRotator::ZeroRotator,Rust,true,LiftRoot,true);
        AddMesh(FString::Printf(TEXT("LiftGuide%d"),I),Cylinder,LocalCenter+FVector(1110,I*185,430),FVector(.16,.16,9.5),FRotator::ZeroRotator,Steel);
    }
    AddMesh(TEXT("LiftBack"),Cube,FVector(220,0,70),FVector(.12,3.2,1.4),FRotator::ZeroRotator,Rust,true,LiftRoot,true);
    ExitGate=AddMesh(TEXT("LiftSafetyGate"),Cube,LocalCenter+FVector(705,0,135),FVector(.12,3.2,2.7),FRotator::ZeroRotator,Steel,true,nullptr,true);
    AddLamp(TEXT("LiftSignal"),LocalCenter+FVector(850,0,260),FLinearColor(.25,.5,.7),900,650);
}
void AAshWellCombatArena::BuildPolishDetails()
{
    // Small physical scale cues sit at the edges; the combat floor stays clear.
    for(int32 I=0;I<18;++I)
    {
        const FVector P=LocalCenter+FVector(-620+I*70,-595,.8);
        AddMesh(FString::Printf(TEXT("SafetyStripe%d"),I),Cube,P,FVector(.32,.10,.014),FRotator(0,-35,0),Amber);
        if(I%3==0)AddMesh(FString::Printf(TEXT("DeckFastener%d"),I),Cylinder,P+FVector(0,45,1),FVector(.05,.05,.035),FRotator::ZeroRotator,Steel);
    }
    for(int32 I=0;I<4;++I)
    {
        AddMesh(FString::Printf(TEXT("Conduit%d"),I),Cylinder,LocalCenter+FVector(-920,151+I*11,35),FVector(.035,.035,5.5),FRotator(0,90,90),Steel);
        AddMesh(FString::Printf(TEXT("PipeBracket%d"),I),Cube,LocalCenter+FVector(-1110+I*125,170,32),FVector(.045,.8,.12),FRotator::ZeroRotator,Rust);
    }
}

FVector AAshWellCombatArena::GetEntryPoint() const
{return GetActorTransform().TransformPosition(LocalCenter+FVector(-697,-300,90));}
bool AAshWellCombatArena::OpenEntry(const FVector& PlayerPosition)
{
    if(!bGrandEncounter||IsEntryOpen()||FVector::Dist2D(PlayerPosition,GetEntryPoint())>=330)return false;
    if(FVector::Dist2D(PlayerPosition,GetEntryPoint())<330&&!bEntryOpening)
    {
        bEntryOpening=true;
        if(bSunoMusic&&MusicLayers.Num()==3){MusicLayers[1]->Play();MusicLayers[1]->FadeIn(2.7f,.25f);}
        if(LoadShiftSound)UGameplayStatics::PlaySoundAtLocation(this,LoadShiftSound,GetEntryPoint(),.85f,.55f);
        UE_LOG(LogTemp,Display,TEXT("AW_GRAND entry_opening"));
    }
    return true;
}
void AAshWellCombatArena::BuildEntry()
{
    // Opaque bulkhead hides the entire opponent until the two powered leaves part.
    for(const FVector& Panel : {FVector(-697,-545,210),FVector(-697,245,810)})
        AddMesh(Panel.Y<0?TEXT("EntryWallSouth"):TEXT("EntryWallNorth"),Cube,LocalCenter+FVector(Panel.X,Panel.Y,350),FVector(.35,Panel.Z/100,7),FRotator::ZeroRotator,Steel,true);
    AddMesh(TEXT("EntryLintel"),Cube,LocalCenter+FVector(-697,-300,650),FVector(.6,3.0,1),FRotator::ZeroRotator,Rust,true);
    EntryLeft=AddMesh(TEXT("EntryDoorLeft"),Cube,LocalCenter+FVector(-697,-370,300),FVector(.28,1.4,6),FRotator::ZeroRotator,Steel,true,nullptr,true);
    EntryRight=AddMesh(TEXT("EntryDoorRight"),Cube,LocalCenter+FVector(-697,-230,300),FVector(.28,1.4,6),FRotator::ZeroRotator,Steel,true,nullptr,true);
    for(int32 I=0;I<7;++I)
    {
        const float Z=45+I*80;
        AddMesh(FString::Printf(TEXT("DoorLeftRib%d"),I),Cube,FVector(-18,0,Z-300),FVector(.09,1.3,.06),FRotator::ZeroRotator,Rust,false,EntryLeft,true);
        AddMesh(FString::Printf(TEXT("DoorRightRib%d"),I),Cube,FVector(-18,0,Z-300),FVector(.09,1.3,.06),FRotator::ZeroRotator,Rust,false,EntryRight,true);
    }
    if(const auto* S=Cast<UAshWellSession>(GetGameInstance()))if(S->bChapterReachedStation){bEntryOpening=true;EntryTime=2.69f;}
    AddLamp(TEXT("DoorSignal"),LocalCenter+FVector(-750,-300,500),FLinearColor(1,.32,.08),2200,800);
    AddLamp(TEXT("WardenSilhouette"),LocalCenter+FVector(550,140,540),FLinearColor(.28,.44,.60),14000,1900);
    auto* BossKey=AddLamp(TEXT("WardenFrontFill"),LocalCenter+FVector(-50,30,520),FLinearColor(1,.50,.20),8500,1550);BossKey->SetCastShadows(true);
}

void AAshWellCombatArena::DuckForImpact()
{
    if(!bPowered||bFinished||MusicLayers.Num()!=3)return;
    ImpactDuckTime=.20f;MusicLayers[1]->AdjustVolume(.025f,bSunoMusic?.30f:.15f);
}

void AAshWellCombatArena::BuildBattleAtmosphere()
{
    if(auto* Vault=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/BattlePolish/SM_BattleVault.SM_BattleVault")))
        AddMesh(TEXT("HighIronVault"),Vault,LocalCenter+FVector(0,0,1150),FVector(1.05,1.65,1),FRotator::ZeroRotator,Steel);
    // All new massing is overhead or beyond the existing rails; the fighting floor stays open.
    for(int I=0;I<6;++I)
    {
        const float X=-580+(I%3)*580,Side=I<3?-1.f:1.f;
        const FVector P=LocalCenter+FVector(X,Side*890,720);
        AddMesh(FString::Printf(TEXT("SuspendedCounterweight_%d"),I),Cube,P,FVector(2.5,2.0,6.8),FRotator(0,8*Side,0),Rust);
        for(int J=0;J<2;++J)
            AddMesh(FString::Printf(TEXT("WeightCable_%d_%d"),I,J),Cylinder,P+FVector((J-.5)*150,0,570),FVector(.10,.10,7.8),FRotator::ZeroRotator,Steel);
        for(int J=0;J<4;++J)
            AddMesh(FString::Printf(TEXT("WeightRib_%d_%d"),I,J),Cube,P+FVector(0,-Side*106,(J-1.5)*150),FVector(2.8,.14,.20),FRotator::ZeroRotator,Steel);
        AddLamp(FString::Printf(TEXT("ShaftLight_%d"),I),P+FVector(-90,-Side*180,200),FLinearColor(.22,.38,.56),10500,1500);
    }
    AddLamp(TEXT("VaultAmberBounce"),LocalCenter+FVector(350,0,1350),FLinearColor(1,.40,.12),21000,2500);
}
