#include "AshWellCombatArena.h"

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
    AddRail(TEXT("EastRail"), LocalCenter + FVector(690.f, -640.f, 0.f), LocalCenter + FVector(690.f, 640.f, 0.f));
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
    UE_LOG(LogTemp, Display, TEXT("ASHWELL CombatArena: power on."));
}

void AAshWellCombatArena::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bPowered) return;
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
