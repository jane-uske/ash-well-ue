#include "AshWellWarden.h"

#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "Sound/SoundBase.h"

AAshWellWarden::AAshWellWarden()
{
    PrimaryActorTick.bCanEverTick = true;
    Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("WardenCapsule"));
    SetRootComponent(Capsule);
    // This kinematic actor has no CharacterMovement floor solver. Keep five
    // centimetres of clearance so horizontal sweeps do not begin in the deck.
    // Body origin stays -135: the visible feet still meet the platform surface.
    Capsule->InitCapsuleSize(62.0f, 130.0f);
    Capsule->SetCollisionProfileName(TEXT("Pawn"));
    Capsule->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Capsule->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
    Capsule->SetGenerateOverlapEvents(false);

    Body = CreateDefaultSubobject<USceneComponent>(TEXT("WardenBody"));
    Body->SetupAttachment(Capsule);
    Body->SetRelativeLocation(FVector(0, 0, -135));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Steel(TEXT("/Game/AshWell/Materials/M_DarkSteel.M_DarkSteel"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Rust(TEXT("/Game/AshWell/Materials/V2/M_Rust.M_Rust"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Amber(TEXT("/Game/AshWell/Materials/M_Amber.M_Amber"));

    AddPart(TEXT("Pelvis"), Cube.Object, Steel.Object, FVector(-6,0,106), FVector(62,90,34));
    AddPart(TEXT("Core"), Cylinder.Object, Steel.Object, FVector(-8,0,140), FVector(56,56,64));
    AddPart(TEXT("Chest"), Cube.Object, Rust.Object, FVector(-8,0,170), FVector(76,112,70), FRotator(7,0,0));
    AddPart(TEXT("ChestSlab"), Cube.Object, Steel.Object, FVector(32,0,175), FVector(12,82,50), FRotator(7,0,0));
    AddPart(TEXT("Collar"), Cube.Object, Steel.Object, FVector(-5,0,211), FVector(78,108,15));
    AddPart(TEXT("Head"), Cube.Object, Steel.Object, FVector(1,0,237), FVector(48,52,43));
    AddPart(TEXT("Visor"), Cube.Object, Amber.Object, FVector(26,0,242), FVector(3,39,6));
    AddPart(TEXT("FaceGuard"), Cube.Object, Rust.Object, FVector(28,0,228), FVector(9,42,16));
    AddPart(TEXT("LeftShoulder"), Cube.Object, Rust.Object, FVector(-7,69,199), FVector(67,39,37), FRotator(0,0,-10));
    AddPart(TEXT("RightShoulder"), Cube.Object, Rust.Object, FVector(-7,-69,199), FVector(67,39,37), FRotator(0,0,10));
    AddPart(TEXT("BackTank"), Cylinder.Object, Rust.Object, FVector(-62,-22,187), FVector(35,35,112));
    AddPart(TEXT("BackPipe"), Cylinder.Object, Steel.Object, FVector(-58,32,223), FVector(18,18,98));
    AddPart(TEXT("PipeCap"), Cube.Object, Rust.Object, FVector(-51,32,272), FVector(32,25,10));
    for (int32 Index = 0; Index < 5; ++Index)
    {
        const FString Name = FString::Printf(TEXT("ChestRib%d"), Index);
        AddPart(*Name, Cube.Object, Steel.Object, FVector(40,-34 + Index*17,172), FVector(8,5,54));
    }

    LeftThigh = AddPart(TEXT("LeftThigh"), Cylinder.Object, Steel.Object, FVector::ZeroVector, FVector::OneVector);
    LeftShin = AddPart(TEXT("LeftShin"), Cylinder.Object, Rust.Object, FVector::ZeroVector, FVector::OneVector);
    RightThigh = AddPart(TEXT("RightThigh"), Cylinder.Object, Steel.Object, FVector::ZeroVector, FVector::OneVector);
    RightShin = AddPart(TEXT("RightShin"), Cylinder.Object, Rust.Object, FVector::ZeroVector, FVector::OneVector);
    LeftFoot = AddPart(TEXT("LeftFoot"), Cube.Object, Steel.Object, FVector(15,38,10), FVector(61,38,20));
    RightFoot = AddPart(TEXT("RightFoot"), Cube.Object, Steel.Object, FVector(15,-38,10), FVector(61,38,20));
    RightUpperArm = AddPart(TEXT("RightUpperArm"), Cylinder.Object, Steel.Object, FVector::ZeroVector, FVector::OneVector);
    RightForearm = AddPart(TEXT("RightForearm"), Cylinder.Object, Rust.Object, FVector::ZeroVector, FVector::OneVector);
    LeftUpperArm = AddPart(TEXT("LeftUpperArm"), Cylinder.Object, Steel.Object, FVector::ZeroVector, FVector::OneVector);
    LeftForearm = AddPart(TEXT("LeftForearm"), Cylinder.Object, Rust.Object, FVector::ZeroVector, FVector::OneVector);
    HammerShaft = AddPart(TEXT("HammerShaft"), Cylinder.Object, Steel.Object, FVector::ZeroVector, FVector::OneVector);
    HammerHead = AddPart(TEXT("HammerHead"), Cube.Object, Rust.Object, FVector::ZeroVector, FVector(95,82,58));
    HammerBand = AddPart(TEXT("HammerBand"), Cube.Object, Steel.Object, FVector::ZeroVector, FVector(101,17,64));
    WarningRing = AddPart(TEXT("HammerWarning"), Sphere.Object, Amber.Object, FVector::ZeroVector, FVector(11,11,11));

    EyeLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("WardenEyeLight"));
    EyeLight->SetupAttachment(Body);
    EyeLight->SetRelativeLocation(FVector(48,0,242));
    EyeLight->SetLightColor(FLinearColor(1.0f,0.22f,0.025f));
    EyeLight->SetIntensity(95.0f);
    EyeLight->SetAttenuationRadius(260.0f);
    EyeLight->SetCastShadows(false);

    ImpactLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("WardenImpactLight"));
    ImpactLight->SetupAttachment(Body);
    ImpactLight->SetLightColor(FLinearColor(1.0f,0.52f,0.10f));
    ImpactLight->SetIntensity(0.0f);
    ImpactLight->SetAttenuationRadius(340.0f);
    ImpactLight->SetCastShadows(false);
    for (int32 Index=0; Index<12; ++Index)
    {
        const FString Name = FString::Printf(TEXT("HitSpark%d"), Index);
        UStaticMeshComponent* Spark = AddPart(*Name, Cube.Object, Amber.Object, FVector::ZeroVector, FVector(3,3,17));
        Spark->SetVisibility(false);
        Spark->SetCastShadow(false);
        Sparks.Add(Spark);
    }
    UpdatePose(0.0f);
}

UStaticMeshComponent* AAshWellWarden::AddPart(const TCHAR* Name, UStaticMesh* Mesh,
    UMaterialInterface* Material, FVector Position, FVector Dimensions, FRotator Rotation)
{
    UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(FName(Name));
    Part->SetupAttachment(Body);
    Part->SetStaticMesh(Mesh);
    if (Material) Part->SetMaterial(0, Material);
    Part->SetRelativeLocation(Position);
    Part->SetRelativeRotation(Rotation);
    Part->SetRelativeScale3D(Dimensions / 100.0f);
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Part->SetGenerateOverlapEvents(false);
    Part->SetCanEverAffectNavigation(false);
    Parts.Add(Part);
    return Part;
}

void AAshWellWarden::BeginPlay()
{
    Super::BeginPlay();
    Tags.AddUnique(TEXT("AshWellCombatEnemy"));
    SwingSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Swing.AW_Combat_Swing"));
    SlamSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Impact.AW_Combat_Impact"));
    if(UStaticMesh* Armor=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/Geometry/SM_Combat_ArmorBlock.SM_Combat_ArmorBlock")))
    {
        for(UStaticMeshComponent* Part:Parts)
        {
            if(Part->GetStaticMesh()&&Part->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Engine/BasicShapes/Cube")))Part->SetStaticMesh(Armor);
        }
    }
}

void AAshWellWarden::SetArenaBounds(FVector Center, FVector2D HalfExtents)
{
    ArenaCenter = Center;
    ArenaHalfExtents = FVector2D(FMath::Max(100.0, HalfExtents.X), FMath::Max(100.0, HalfExtents.Y));
    bHasBounds = true;
}

void AAshWellWarden::ActivateEncounter(APawn* Player)
{
    if (!IsValid(Player) || IsDead()) return;
    Target = Player;
    if (State == EWellWardenState::Dormant) ChangeState(EWellWardenState::Chase);
}

void AAshWellWarden::ChangeState(EWellWardenState NewState)
{
    const EWellWardenState PreviousState=State;
    State = NewState;
    StateTime = 0.0f;
    if (State == EWellWardenState::Strike) bStrikeHit = false;
    if(State==EWellWardenState::Strike&&SwingSound)UGameplayStatics::PlaySoundAtLocation(this,SwingSound,GetAimPoint(),.7f,.65f);
    if(State==EWellWardenState::Recovery&&PreviousState==EWellWardenState::Strike)
    {
        const FVector Ground=GetActorLocation()+GetActorForwardVector()*190-FVector(0,0,125);
        if(SlamSound)UGameplayStatics::PlaySoundAtLocation(this,SlamSound,Ground,.85f,.65f);
        EmitSparks(Ground);
    }
    if (State == EWellWardenState::Dead)
    {
        Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        EmitSparks(GetAimPoint());
        OnDefeated.Broadcast();
    }
}

void AAshWellWarden::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    StateTime += DeltaSeconds;
    TotalTime += DeltaSeconds;
    HitFlash = FMath::Max(0.0f, HitFlash - DeltaSeconds);
    switch (State)
    {
    case EWellWardenState::Chase:
        if (Target.IsValid())
        {
            FaceTarget(DeltaSeconds, 160.0f);
            const float Distance = FVector::Dist2D(GetActorLocation(), Target->GetActorLocation());
            const FVector Direction = (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
            if (Distance <= 245.0f && FVector::DotProduct(GetActorForwardVector(), Direction) > 0.65f)
                ChangeState(EWellWardenState::Windup);
            else StepTowardTarget(DeltaSeconds);
        }
        break;
    case EWellWardenState::Windup:
        // The final 0.35 seconds commits to a direction, so a lateral dodge can earn an opening.
        if (StateTime < WindupSeconds - 0.35f) FaceTarget(DeltaSeconds, 70.0f);
        if (StateTime >= WindupSeconds) ChangeState(EWellWardenState::Strike);
        break;
    case EWellWardenState::Strike:
        // The weapon is descending before damage becomes active.
        if (StateTime >= 0.065f) TryStrike();
        if (StateTime >= StrikeSeconds)
        {
            EmitSparks(GetActorTransform().TransformPosition(FVector(190,-65,-120)));
            ChangeState(EWellWardenState::Recovery);
        }
        break;
    case EWellWardenState::Recovery:
        if (StateTime >= RecoverySeconds) ChangeState(EWellWardenState::Chase);
        break;
    case EWellWardenState::Stagger:
        if (StateTime >= 0.32f)
        {
            if (RecoveryAfterStagger > 0.0f)
            {
                ChangeState(EWellWardenState::Recovery);
                StateTime = RecoverySeconds-RecoveryAfterStagger;
                RecoveryAfterStagger = 0.0f;
            }
            else ChangeState(EWellWardenState::Chase);
        }
        break;
    default: break;
    }
    UpdatePose(DeltaSeconds);
    UpdateSparks(DeltaSeconds);
}

void AAshWellWarden::FaceTarget(float DeltaSeconds, float DegreesPerSecond)
{
    if (!Target.IsValid()) return;
    const FVector Direction = (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
    if (!Direction.IsNearlyZero())
        SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), FRotator(0, Direction.Rotation().Yaw, 0), DeltaSeconds, DegreesPerSecond));
}

void AAshWellWarden::StepTowardTarget(float DeltaSeconds)
{
    if (!Target.IsValid()) return;
    FVector Destination = GetActorLocation() + (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D() * WalkSpeed * DeltaSeconds;
    if (bHasBounds)
    {
        Destination.X = FMath::Clamp(Destination.X, ArenaCenter.X-ArenaHalfExtents.X+65.0f, ArenaCenter.X+ArenaHalfExtents.X-65.0f);
        Destination.Y = FMath::Clamp(Destination.Y, ArenaCenter.Y-ArenaHalfExtents.Y+65.0f, ArenaCenter.Y+ArenaHalfExtents.Y-65.0f);
    }
    const FVector Before = GetActorLocation();
    FHitResult Hit;
    AddActorWorldOffset(Destination-Before, true, &Hit);
    if (Hit.bBlockingHit && Hit.Time < 1.0f)
    {
        FVector Slide = FVector::VectorPlaneProject((Destination-Before)*(1.0f-Hit.Time), Hit.Normal);
        Slide.Z = 0.0f;
        AddActorWorldOffset(Slide, true);
    }
    GaitPhase += FVector::Dist2D(Before, GetActorLocation()) / 33.0f;
}

void AAshWellWarden::TryStrike()
{
    if (bStrikeHit || !Target.IsValid()) return;
    const FVector TargetPosition = Target->GetActorLocation();
    const FVector Offset = TargetPosition - GetActorLocation();
    if (Offset.Size2D() > 305.0f || FMath::Abs(Offset.Z) > 170.0f) return;
    if (FVector::DotProduct(GetActorForwardVector(), Offset.GetSafeNormal2D()) < 0.52f) return;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(WardenMelee), false, this);
    FHitResult Hit;
    if (GetWorld()->LineTraceSingleByChannel(Hit, GetAimPoint(), TargetPosition, ECC_Visibility, Params)
        && Hit.GetActor() != Target.Get()) return;
    bStrikeHit = true;
    UGameplayStatics::ApplyDamage(Target.Get(), AttackDamage, nullptr, this, nullptr);
}

bool AAshWellWarden::ReceiveMeleeHit(float Damage, const FVector& Source)
{
    if (IsDead() || Damage <= 0.0f) return false;
    Health = FMath::Max(0.0f, Health - Damage);
    HitFlash = 0.16f;
    FVector HitPoint = GetAimPoint() + (Source-GetAimPoint()).GetSafeNormal() * 32.0f;
    EmitSparks(HitPoint);
    if (Health <= 0.0f) ChangeState(EWellWardenState::Dead);
    else if ((State == EWellWardenState::Chase || State == EWellWardenState::Recovery)
        && TotalTime-LastStaggerTime > 1.6f)
    {
        LastStaggerTime = TotalTime;
        // A successful punish must not accidentally shorten the enemy's recovery.
        RecoveryAfterStagger = State == EWellWardenState::Recovery ? FMath::Max(0.0f, RecoverySeconds-StateTime) : 0.0f;
        ChangeState(EWellWardenState::Stagger);
    }
    return true;
}

void AAshWellWarden::SetLink(UStaticMeshComponent* Part, const FVector& A, const FVector& B, float Width)
{
    if (!Part) return;
    const FVector Delta = B-A;
    Part->SetRelativeLocation((A+B)*0.5f);
    Part->SetRelativeRotation(FRotationMatrix::MakeFromZ(Delta.GetSafeNormal()).Rotator());
    Part->SetRelativeScale3D(FVector(Width/100.0f, Width/100.0f, Delta.Size()/100.0f));
}

void AAshWellWarden::UpdatePose(float DeltaSeconds)
{
    const bool bWalking = State == EWellWardenState::Chase;
    const float Gait = bWalking ? FMath::Sin(GaitPhase) : 0.0f;
    const float LeftLift = bWalking ? FMath::Max(0.0f, FMath::Cos(GaitPhase))*13.0f : 0.0f;
    const float RightLift = bWalking ? FMath::Max(0.0f, -FMath::Cos(GaitPhase))*13.0f : 0.0f;
    const FVector LeftToe(15+Gait*26,38,10+LeftLift);
    const FVector RightToe(15-Gait*26,-38,10+RightLift);
    LeftFoot->SetRelativeLocation(LeftToe);
    RightFoot->SetRelativeLocation(RightToe);
    const FVector LeftKnee(14+Gait*12,38,64+LeftLift*0.3f);
    const FVector RightKnee(14-Gait*12,-38,64+RightLift*0.3f);
    SetLink(LeftThigh, FVector(-8,38,111), LeftKnee, 32);
    SetLink(LeftShin, LeftKnee, LeftToe+FVector(-10,0,11), 29);
    SetLink(RightThigh, FVector(-8,-38,111), RightKnee, 32);
    SetLink(RightShin, RightKnee, RightToe+FVector(-10,0,11), 29);

    const FVector RestHand(44,-83,147);
    const FVector RestHead(84,-83,36);
    const FVector RaisedHand(-29,-82,239);
    const FVector RaisedHead(-83,-82,316);
    const FVector SlamHand(88,-72,133);
    const FVector SlamHead(195,-67,30);
    FVector Hand = RestHand;
    FVector Head = RestHead;
    float Lean = 0;
    if (State == EWellWardenState::Windup)
    {
        const float Alpha = FMath::Clamp(StateTime/(WindupSeconds-0.20f), 0.0f, 1.0f);
        const float Smooth = Alpha*Alpha*(3-2*Alpha);
        Hand = FMath::Lerp(RestHand, RaisedHand, Smooth);
        Head = FMath::Lerp(RestHead, RaisedHead, Smooth);
        Lean = 7.0f*Smooth;
    }
    else if (State == EWellWardenState::Strike)
    {
        const float Alpha = FMath::Clamp(StateTime/(StrikeSeconds*0.8f),0.0f,1.0f);
        Hand = FMath::Lerp(RaisedHand,SlamHand,Alpha*Alpha);
        Head = FMath::Lerp(RaisedHead,SlamHead,Alpha*Alpha);
        Lean = FMath::Lerp(7.0f,-8.0f,Alpha);
    }
    else if (State == EWellWardenState::Recovery)
    {
        const float Alpha = FMath::Clamp((StateTime-0.42f)/(RecoverySeconds-0.42f),0.0f,1.0f);
        Hand = FMath::Lerp(SlamHand,RestHand,Alpha);
        Head = FMath::Lerp(SlamHead,RestHead,Alpha);
        Lean = -8.0f*(1-Alpha);
    }
    else if (State == EWellWardenState::Stagger)
    {
        Lean = 10.0f*FMath::Sin(FMath::Clamp(StateTime/0.32f,0.0f,1.0f)*PI);
    }
    if (bWalking) { Hand.Z += FMath::Abs(Gait)*5; Head.Z += FMath::Abs(Gait)*5; }
    FVector Elbow = (FVector(0,-65,194)+Hand)*0.5f + FVector(-18,-19,-4);
    SetLink(RightUpperArm,FVector(0,-65,194),Elbow,29);
    SetLink(RightForearm,Elbow,Hand,26);
    const FVector OtherElbow(6-Gait*9,78,143);
    SetLink(LeftUpperArm,FVector(0,65,194),OtherElbow,28);
    SetLink(LeftForearm,OtherElbow,FVector(30+Gait*13,76,97),24);
    SetLink(HammerShaft,Hand+(Hand-Head).GetSafeNormal()*30,Head,11);
    HammerHead->SetRelativeLocation(Head);
    HammerBand->SetRelativeLocation(Head);
    const FRotator HammerRotation = FRotationMatrix::MakeFromZ((Hand-Head).GetSafeNormal()).Rotator();
    HammerHead->SetRelativeRotation(HammerRotation);
    HammerBand->SetRelativeRotation(HammerRotation);
    WarningRing->SetRelativeLocation(Head+FVector(0,0,22));
    WarningRing->SetVisibility(IsAttacking());

    if (IsDead())
    {
        const float Alpha = FMath::Clamp(StateTime/1.05f,0.0f,1.0f);
        Body->SetRelativeRotation(FRotator(-75*Alpha,0,12*Alpha));
        Body->SetRelativeLocation(FVector(0,0,-135+24*Alpha));
        EyeLight->SetIntensity(FMath::Max(0.0f,1.0f-Alpha)*80);
        WarningRing->SetVisibility(false);
    }
    else
    {
        const float Jolt = HitFlash > 0 ? FMath::Sin(TotalTime*130)*HitFlash*26 : 0;
        Body->SetRelativeLocation(FVector(Jolt,0,-135));
        Body->SetRelativeRotation(FRotator(Lean,0,bWalking?Gait*1.0f:0));
        const bool bWarning = State == EWellWardenState::Windup;
        EyeLight->SetIntensity(bWarning ? 170+100*FMath::Sin(StateTime*19) : 95.0f);
        EyeLight->SetLightColor(bWarning ? FLinearColor(1.0f,0.045f,0.008f) : FLinearColor(1.0f,0.22f,0.025f));
    }
}

void AAshWellWarden::EmitSparks(const FVector& WorldPosition)
{
    SparkTime = 0.0f;
    SparkOrigin = WorldPosition;
    SparkVelocities.Reset();
    for (int32 Index=0; Index<Sparks.Num(); ++Index)
    {
        const float Angle = Index*2.39996f + TotalTime;
        SparkVelocities.Add(FVector(FMath::Cos(Angle)*210,FMath::Sin(Angle)*210,70+(Index%4)*65));
        Sparks[Index]->SetVisibility(true);
    }
    ImpactLight->SetWorldLocation(WorldPosition);
}

void AAshWellWarden::UpdateSparks(float DeltaSeconds)
{
    SparkTime += DeltaSeconds;
    const float Alpha = FMath::Clamp(1.0f-SparkTime/0.30f,0.0f,1.0f);
    ImpactLight->SetIntensity(Alpha*760.0f);
    for (int32 Index=0; Index<Sparks.Num(); ++Index)
    {
        Sparks[Index]->SetVisibility(Alpha > 0);
        if (Alpha > 0 && SparkVelocities.IsValidIndex(Index))
        {
            Sparks[Index]->SetWorldLocation(SparkOrigin+SparkVelocities[Index]*SparkTime+FVector(0,0,-490*SparkTime*SparkTime));
            Sparks[Index]->SetWorldRotation(FRotationMatrix::MakeFromZ(SparkVelocities[Index]).Rotator());
            Sparks[Index]->SetWorldScale3D(FVector(0.025f,0.025f,0.14f)*Alpha);
        }
    }
}

FVector AAshWellWarden::GetAimPoint() const
{
    return GetActorLocation()+FVector(0,0,55);
}

float AAshWellWarden::GetAttackProgress() const
{
    if (State == EWellWardenState::Windup) return FMath::Clamp(StateTime/WindupSeconds,0.0f,1.0f);
    return State == EWellWardenState::Strike ? 1.0f : 0.0f;
}

FString AAshWellWarden::GetStateLabel() const
{
    switch (State)
    {
    case EWellWardenState::Dormant: return TEXT("沉眠");
    case EWellWardenState::Chase: return TEXT("逼近");
    case EWellWardenState::Windup: return TEXT("蓄势");
    case EWellWardenState::Strike: return TEXT("重击");
    case EWellWardenState::Recovery: return TEXT("破绽");
    case EWellWardenState::Stagger: return TEXT("失衡");
    case EWellWardenState::Dead: return TEXT("停机");
    }
    return FString();
}
