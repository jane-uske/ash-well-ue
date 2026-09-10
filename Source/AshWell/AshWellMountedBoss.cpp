#include "AshWellMountedBoss.h"
#include "AshWellCombatCharacter.h"
#include "AshWellBattleFX.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "Sound/SoundBase.h"
#include "Animation/AnimSequence.h"
#include "Components/AudioComponent.h"

AAshWellMountedBoss::AAshWellMountedBoss()
{
    PrimaryActorTick.bCanEverTick=true;
    AttackTuning={{.80f,.32f,1.f,.28f,27.f,2.f},{1.05f,.25f,1.2f,.32f,34.f,3.6f},{1.15f,1.05f,1.35f,.30f,32.f,7.f},{.70f,.34f,.95f,.28f,19.f,4.2f},{1.40f,.24f,1.45f,.65f,36.f,9.f},{1.1f,.90f,1.6f,.35f,38.f,11.f}};
    SceneRoot=CreateDefaultSubobject<USceneComponent>(TEXT("MountedGroundOrigin"));SetRootComponent(SceneRoot);
    BodyCollision=CreateDefaultSubobject<UBoxComponent>(TEXT("HorseBodyCollision"));BodyCollision->SetupAttachment(SceneRoot);
    BodyCollision->SetRelativeLocation(FVector(0,0,102));BodyCollision->SetBoxExtent(FVector(108,43,80));
    BodyCollision->SetCollisionProfileName(TEXT("Pawn"));
    BodyCollision->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    BodyCollision->SetCollisionResponseToChannel(ECC_Camera,ECR_Ignore);
    BodyCollision->SetGenerateOverlapEvents(false);BodyCollision->SetCanEverAffectNavigation(false);
}

void AAshWellMountedBoss::BeginPlay()
{
    Super::BeginPlay();Home=GetActorLocation();Tags.AddUnique(TEXT("AshWellCombatEnemy"));Tags.AddUnique(TEXT("AshWellMountedBoss"));
    auto Audio=[](const TCHAR* N){const FString S=FString(TEXT("AW_Battle_"))+N;return LoadObject<USoundBase>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/BattlePolish/"))+S+TEXT(".")+S));};
    SwingSound=Audio(TEXT("Swing"));ImpactSound=Audio(TEXT("GroundSlam"));HoofSound=Audio(TEXT("Kick"));
    InitializeVisuals();UpdatePose(0);CacheWeaponSweepPose();
}

const FMountedAttackSpec& AAshWellMountedBoss::Spec() const
{
    return AttackTuning[FMath::Clamp(static_cast<int32>(AttackKind),0,AttackTuning.Num()-1)];
}

void AAshWellMountedBoss::ClearAttackTransient()
{
    bDamageConsumed=true;bResetWeaponSweep=true;bPreviousWeaponPoseValid=false;
    bBodyContactPending=false;bComboPending=bFollowup=bHeadingCommitted=false;
    for(auto A:ActiveAudio)if(IsValid(A))A->Stop();
    ActiveAudio.Reset();
    if(auto* FX=AAshWellBattleFX::Find(GetWorld()))FX->ClearMountedEffects();
}
void AAshWellMountedBoss::DebugCancelAttack()
{
    if(!IsQAEnabled())return;
    ++CancelledAttacks;ClearAttackTransient();Speed=ActualSpeed=0;
    SetActorLocation(FVector(GetActorLocation().X,GetActorLocation().Y,Home.Z));LeapHeight=0;
    ChangeState(Target.IsValid()?EMountedBossState::Approach:EMountedBossState::Idle);
    DecisionDelay=.5f;UpdatePose(0);CacheWeaponSweepPose();
}
void AAshWellMountedBoss::SetDebugPaused(bool bPaused)
{bAudioPaused=bPaused;for(auto A:ActiveAudio)if(IsValid(A))A->SetPaused(bPaused);}
void AAshWellMountedBoss::EndPlay(const EEndPlayReason::Type Reason)
{ClearAttackTransient();Super::EndPlay(Reason);}
bool AAshWellMountedBoss::IsHitWindowOpen() const
{
    if(bAudioPaused||UGameplayStatics::IsGamePaused(this)||State!=EMountedBossState::Active||bDamageConsumed)return false;
    if(AttackKind==EMountedBossAttack::Charge)return StateTime>=.16f;
    if(AttackKind==EMountedBossAttack::Rear)return StateTime>=.075f;
    if(AttackKind==EMountedBossAttack::LeapShield)return bLeapLanded;
    return true;
}

void AAshWellMountedBoss::SetArenaBounds(FVector Center,FVector2D HalfExtents)
{ArenaCenter=Center;ArenaHalfExtents=FVector2D(FMath::Max(500.,HalfExtents.X),FMath::Max(500.,HalfExtents.Y));}

void AAshWellMountedBoss::ActivateEncounter(APawn* Player)
{
    if(!IsValid(Player)||IsDead()||IsReturning())return;
    Target=Player;
    if(State==EMountedBossState::Idle){DecisionDelay=.65f;ChangeState(EMountedBossState::Approach);}
}

void AAshWellMountedBoss::ResetEncounter()
{
    ClearAttackTransient();ReceivedAttackIds.Reset();LeapHeight=0;
    Health=MaximumHealth;bPhaseTwo=bPhasePending=bComboPending=bFollowup=false;
    bHeadingCommitted=bDamageConsumed=bImpactPlayed=false;LeashTime=Speed=FightTime=HitReaction=0;
    for(float& C:Cooldowns)C=0;
    BodyCollision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    SetActorLocation(Home);SetActorRotation(FRotator(0,180,0));Target.Reset();++ResetCount;
    ChangeState(EMountedBossState::Idle);UpdatePose(0);CacheWeaponSweepPose();
    UE_LOG(LogTemp,Display,TEXT("AW_MOUNTED_RESET count=%d"),ResetCount);
}

void AAshWellMountedBoss::ChangeState(EMountedBossState NewState)
{
    if(NewState==EMountedBossState::Dead||NewState==EMountedBossState::Return||NewState==EMountedBossState::Idle)ClearAttackTransient();
    State=NewState;StateTime=0;
    if(State==EMountedBossState::Active)
    {
        if(!bHeadingCommitted){CommittedYaw=GetActorRotation().Yaw;bHeadingCommitted=true;}
        bDamageConsumed=bImpactPlayed=false;++StrikeCount;
        // The first active pose may differ from the final preparation pose.
        // Seed history only after that pose has actually been evaluated below.
        bResetWeaponSweep=true;
        PlaySound(SwingSound,GetAimPoint(),AttackKind==EMountedBossAttack::Rear?.18f:.42f,AttackKind==EMountedBossAttack::BodyCheck?.85f:1.f);
        UE_LOG(LogTemp,Display,TEXT("AW_MOUNTED_STRIKE kind=%s phase=%d yaw=%.2f"),*GetAttackLabel(),bPhaseTwo?2:1,CommittedYaw);
    }
    if(State==EMountedBossState::Dead)
    {
        Speed=0;bHeadingCommitted=false;bComboPending=false;BodyCollision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        PlaySound(ImpactSound,GetActorLocation(),.50f,.70f);OnDefeated.Broadcast();
    }
}

void AAshWellMountedBoss::BeginAttack(EMountedBossAttack Kind,bool bIsFollowup)
{
    ++AttackSerial;bLeapLanded=false;bBodyContactPending=false;
    AttackKind=Kind;bFollowup=bIsFollowup;bHeadingCommitted=false;bDamageConsumed=false;bImpactPlayed=false;
    bResetWeaponSweep=true;
    Cooldowns[static_cast<int32>(Kind)]=Spec().Cooldown;
    // One authored optional follow-up: overhead after a sweep; shield/rear always give their full punish.
    bComboPending=bPhaseTwo&&!bFollowup&&Kind==EMountedBossAttack::Sweep&&SelectionCount%3==0;
    ChangeState(EMountedBossState::Windup);
    UE_LOG(LogTemp,Display,TEXT("AW_MOUNTED_WINDUP kind=%s windup=%.2f commit=%.2f active=%.2f recovery=%.2f combo=%d"),*GetAttackLabel(),Spec().Windup,Spec().Windup-Spec().CommitLead,Spec().Active,Spec().Recovery,bComboPending);
}

void AAshWellMountedBoss::Tick(float DeltaSeconds)
{
    if(UGameplayStatics::IsGamePaused(this))return; // Also reject ticks queued before the pause input.
    Super::Tick(DeltaSeconds);
    const int32 Steps=FMath::Clamp(FMath::CeilToInt(DeltaSeconds*120.f),1,240);
    for(int32 I=0;I<Steps;++I)StepCombat(DeltaSeconds/Steps);
    UpdateHorseAnimation(DeltaSeconds);
    UpdatePose(0); // Seat and hands follow the evaluated horse skeleton in this rendered frame.
}

void AAshWellMountedBoss::StepCombat(float Dt)
{
    StateTime+=Dt;HitReaction=FMath::Max(0.f,HitReaction-Dt*4.f);
    if(IsEncounterRunning())FightTime+=Dt;
    for(float& C:Cooldowns)C=FMath::Max(0.f,C-Dt);
    DecisionDelay=FMath::Max(0.f,DecisionDelay-Dt);
    if(IsEncounterRunning()&&Target.IsValid())
    {
        const auto* Player=Cast<AAshWellCombatCharacter>(Target.Get());
        const bool Far=Target->GetActorLocation().X<ArenaCenter.X-1750.f||FVector::Dist2D(GetActorLocation(),Target->GetActorLocation())>2200.f||FVector::Dist2D(Target->GetActorLocation(),ArenaCenter)>3000.f;
        LeashTime=Far&&!bQAStationary?LeashTime+Dt:0;
        if((Player&&Player->IsDead())||LeashTime>2.f)
        {bComboPending=false;bHeadingCommitted=false;ChangeState(EMountedBossState::Return);}
    }
    const FVector Goal=Target.IsValid()?Target->GetActorLocation():Home;
    switch(State)
    {
        case EMountedBossState::Approach:
        {
            if(!Target.IsValid()){ChangeState(EMountedBossState::Return);break;}
            if(bPhasePending&&!bQAStationary){bPhasePending=false;bPhaseTwo=true;bComboPending=false;ChangeState(EMountedBossState::PhaseChange);break;}
            const float Distance=FVector::Dist2D(GetActorLocation(),Goal);
            const FVector Direction=(Goal-GetActorLocation()).GetSafeNormal2D();
            const float Facing=FVector::DotProduct(GetActorForwardVector(),Direction);
            float Desired=Distance>750?400.f:Distance>420?260.f:145.f;
            if(Distance<245&&Facing>.45f)Desired=0;
            if(Facing<-.1f)Desired=FMath::Min(Desired,110.f);
            StepMovement(Dt,Goal,bQAStationary?0:Desired,!bQAStationary);
            if(!bQAStationary&&DecisionDelay<=0)SelectAttack();
            break;
        }
        case EMountedBossState::Windup:
        {
            if(!bHeadingCommitted&&StateTime>=Spec().Windup-Spec().CommitLead)
            {bHeadingCommitted=true;CommittedYaw=GetActorRotation().Yaw;}
            FVector SteeringGoal=Goal;
            if(AttackKind==EMountedBossAttack::Charge&&!bHeadingCommitted)
            {
                // The visible polearm passes about 100 cm to the horse's right.
                // Aim the horse to the player's left so the blade crosses them and
                // the body clears them. This choice freezes at the normal commit point.
                const FVector ForwardToTarget=(Goal-GetActorLocation()).GetSafeNormal2D();
                const FVector RightOfTarget(-ForwardToTarget.Y,ForwardToTarget.X,0);
                SteeringGoal-=RightOfTarget*105.f;
            }
            StepMovement(Dt,SteeringGoal,0,!bHeadingCommitted&&!bQAStationary);
            if(StateTime>=Spec().Windup)ChangeState(EMountedBossState::Active);
            break;
        }
        case EMountedBossState::Active:
        {
            const float Desired=AttackKind==EMountedBossAttack::Charge?850.f:AttackKind==EMountedBossAttack::LeapShield?240.f:AttackKind==EMountedBossAttack::BodyCheck?420.f:AttackKind==EMountedBossAttack::Overhead?180.f:0.f;
            StepMovement(Dt,Goal,Desired,false);
            if(AttackKind==EMountedBossAttack::LeapShield)
            {
                // The actor is the sole root displacement source. All children follow.
                const float Flight=.68f,T=FMath::Min(StateTime/Flight,1.f);
                LeapHeight=150.f*4*T*(1-T);MaximumLeapHeight=FMath::Max(MaximumLeapHeight,LeapHeight);
                MoveSwept(FVector(0,0,Home.Z+LeapHeight-GetActorLocation().Z));
                if(StateTime>=Flight&&!bLeapLanded){MoveSwept(FVector(0,0,Home.Z-GetActorLocation().Z));bLeapLanded=GetActorLocation().Z<=Home.Z+.5f;LeapHeight=FMath::Max(0.f,float(GetActorLocation().Z-Home.Z));}
            }
            break;
        }
        case EMountedBossState::Recovery:
            StepMovement(Dt,Goal,0,false);
            if(StateTime>=Spec().Recovery)FinishAttack();
            break;
        case EMountedBossState::PhaseChange:
            StepMovement(Dt,Goal,0,false);
            if(StateTime>=1.65f){DecisionDelay=.40f;ChangeState(EMountedBossState::Approach);}
            break;
        case EMountedBossState::Return:
        {
            const float Distance=FVector::Dist2D(GetActorLocation(),Home);
            if(Distance<20.f)
            {
                // Arrive, stop, and step around to the resting heading; do not orbit
                // the small arrival radius at full speed or snap through 180 degrees.
                StepMovement(Dt,GetActorLocation()+FVector(-100,0,0),0,true);
                if(Speed<5&&FMath::Abs(FMath::FindDeltaAngleDegrees(GetActorRotation().Yaw,180.f))<3.f)ResetEncounter();
            }
            else
            {
                const float Facing=FVector::DotProduct(GetActorForwardVector(),(Home-GetActorLocation()).GetSafeNormal2D());
                const float Desired=FMath::Min(260.f,Distance*.65f)*FMath::Clamp(Facing,.12f,1.f);
                StepMovement(Dt,Home,Desired,true);
            }
            break;
        }
        default:StepMovement(Dt,Goal,0,false);break;
    }
    if(State!=EMountedBossState::Active&&GetActorLocation().Z>Home.Z+.01f)
    {MoveSwept(FVector(0,0,FMath::Max(Home.Z,GetActorLocation().Z-550.f*Dt)-GetActorLocation().Z));LeapHeight=FMath::Max(0.f,float(GetActorLocation().Z-Home.Z));}
    if(bHeadingCommitted&&(State==EMountedBossState::Windup||State==EMountedBossState::Active))
        MaximumCommittedYawDrift=FMath::Max(MaximumCommittedYawDrift,FMath::Abs(FMath::FindDeltaAngleDegrees(CommittedYaw,GetActorRotation().Yaw)));
    UpdatePose(Dt);
    if(bResetWeaponSweep)CacheWeaponSweepPose();
    if(State==EMountedBossState::Active)
    {
        TryDamage();
        if(StateTime>=Spec().Active)ChangeState(EMountedBossState::Recovery);
    }
    CacheWeaponSweepPose();
}

void AAshWellMountedBoss::StepMovement(float Dt,const FVector& Goal,float DesiredSpeed,bool bAllowTurning)
{
    const float PreviousYaw=GetActorRotation().Yaw;
    const float Accel=State==EMountedBossState::Active?(AttackKind==EMountedBossAttack::Charge?1300.f:AttackKind==EMountedBossAttack::BodyCheck?1000.f:380.f):380.f;
    Speed=FMath::FInterpConstantTo(Speed,DesiredSpeed,Dt,DesiredSpeed>Speed?Accel:700.f);
    if(bAllowTurning)
    {
        const float Wanted=(Goal-GetActorLocation()).Rotation().Yaw;
        // Radius grows with speed; a walking pivot uses visible stepping rather than a snap turn.
        const float Radius=260.f+Speed*.50f;
        const float Degrees=FMath::Clamp(FMath::RadiansToDegrees(FMath::Max(Speed,130.f)/Radius),27.f,72.f);
        const FRotator Candidate(0,FMath::FixedTurn(GetActorRotation().Yaw,Wanted,Degrees*Dt),0);
        FCollisionQueryParams Params(SCENE_QUERY_STAT(MountedBodyTurn),false,this);
        if(!GetWorld()->OverlapBlockingTestByChannel(BodyCollision->GetComponentLocation(),Candidate.Quaternion(),ECC_Pawn,FCollisionShape::MakeBox(BodyCollision->GetUnscaledBoxExtent()),Params))SetActorRotation(Candidate);
        else ++BlockedTurnCount;
    }
    const FVector Before=GetActorLocation();MoveSwept(GetActorForwardVector()*Speed*Dt);
    const float AngularTravel=FMath::Abs(FMath::DegreesToRadians(FMath::FindDeltaAngleDegrees(PreviousYaw,GetActorRotation().Yaw)))*65.f;
    TurnTravel+=AngularTravel;TurnSpeed=Dt>SMALL_NUMBER?AngularTravel/Dt:0;
    LastTravel=FVector::Dist2D(Before,GetActorLocation());ActualSpeed=Dt>SMALL_NUMBER?LastTravel/Dt:0;DistanceTravelled+=LastTravel;
    GaitPhase=FMath::Fmod(GaitPhase+LastTravel/220.f,1.f);HoofDistance+=LastTravel;
    // Hoof audio is emitted from actual descending hoof contacts in the visual adapter.
}

void AAshWellMountedBoss::MoveSwept(const FVector& Delta)
{
    const FVector Position=GetActorLocation();float Fraction=1.f;
    for(int32 Axis=0;Axis<2;++Axis)
    {
        const float D=Delta[Axis],Half=Axis==0?ArenaHalfExtents.X:ArenaHalfExtents.Y;
        if(FMath::Abs(D)>SMALL_NUMBER)
        {
            const float Boundary=ArenaCenter[Axis]+(D>0?Half-185:-Half+185);
            Fraction=FMath::Min(Fraction,static_cast<float>(FMath::Clamp((Boundary-Position[Axis])/D,0.,1.)));
        }
    }
    const FVector Destination=Position+Delta*Fraction;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(MountedBodyMove),false,this);FHitResult Hit;
    const FVector Center=BodyCollision->GetComponentLocation();const FVector Move=Destination-GetActorLocation();
    const bool Blocked=GetWorld()->SweepSingleByChannel(Hit,Center,Center+Move,GetActorQuat(),ECC_Pawn,FCollisionShape::MakeBox(BodyCollision->GetUnscaledBoxExtent()),Params);
    SetActorLocation(GetActorLocation()+Move*(Blocked?FMath::Max(0.f,Hit.Time-.005f):1.f),false);
    if(Blocked&&Hit.GetActor()==Target.Get()&&State==EMountedBossState::Active&&AttackKind==EMountedBossAttack::BodyCheck)bBodyContactPending=true;
    if(Blocked&&Hit.Time<.05f)Speed=FMath::Max(0.f,Speed-30.f);
}

void AAshWellMountedBoss::SelectAttack()
{
    if(!Target.IsValid())return;
    const FVector Delta=Target->GetActorLocation()-GetActorLocation();const float Distance=Delta.Size2D();
    const float Angle=FMath::FindDeltaAngleDegrees(GetActorRotation().Yaw,Delta.Rotation().Yaw);
    const auto Ready=[&](EMountedBossAttack Kind){return Cooldowns[static_cast<int32>(Kind)]<=0;};
    EMountedBossAttack Choice=EMountedBossAttack::Sweep;bool Chosen=false;
    if(bPhaseTwo&&Distance>320&&Distance<600&&FMath::Abs(Angle)<30&&Ready(EMountedBossAttack::LeapShield)){Choice=EMountedBossAttack::LeapShield;Chosen=true;}
    else if((bPhaseTwo||FMath::Abs(Angle)>100)&&Distance<340&&Ready(EMountedBossAttack::Rear)) {Choice=EMountedBossAttack::Rear;Chosen=true;}
    else if(Distance<215&&FMath::Abs(Angle)<55&&Ready(EMountedBossAttack::BodyCheck)) {Choice=EMountedBossAttack::BodyCheck;Chosen=true;}
    else if(Distance>570&&Distance<900&&FMath::Abs(Angle)<20&&Ready(EMountedBossAttack::Charge)) {Choice=EMountedBossAttack::Charge;Chosen=true;}
    else if(Distance<310&&FMath::Abs(Angle)<50&&Ready(EMountedBossAttack::Overhead)&&SelectionCount%2==1) {Choice=EMountedBossAttack::Overhead;Chosen=true;}
    else if(Distance<315&&Angle> -40&&Angle<110&&Ready(EMountedBossAttack::Sweep)) {Choice=EMountedBossAttack::Sweep;Chosen=true;}
    if(Chosen){++SelectionCount;BeginAttack(Choice);}else DecisionDelay=.12f;
}

void AAshWellMountedBoss::FinishAttack()
{
    bHeadingCommitted=false;
    if(bPhasePending)
    {bPhasePending=false;bPhaseTwo=true;bComboPending=false;bFollowup=false;ChangeState(EMountedBossState::PhaseChange);return;}
    // Full sweep recovery precedes this follow-up; it cannot erase an already earned opening.
    if(bComboPending&&Target.IsValid()&&FVector::Dist2D(GetActorLocation(),Target->GetActorLocation())<470.f)
    {bComboPending=false;BeginAttack(EMountedBossAttack::Overhead,true);return;}
    bComboPending=bFollowup=false;DecisionDelay=.28f;ChangeState(EMountedBossState::Approach);
}

void AAshWellMountedBoss::TryDamage()
{
    if(!Target.IsValid()||!IsHitWindowOpen())return;
    bool Contact=false,BladeContact=false;FHitResult Hit;FCollisionQueryParams Params(SCENE_QUERY_STAT(MountedVisibleWeapon),false,this);
    if(AttackKind==EMountedBossAttack::Rear||AttackKind==EMountedBossAttack::LeapShield)
    {
        if(StateTime<.075f)return;
        if(AttackKind==EMountedBossAttack::LeapShield&&ShieldPoint.Z-90.f>Home.Z+25.f)return;
        const FVector Ground=AttackKind==EMountedBossAttack::LeapShield?FVector(ShieldPoint.X,ShieldPoint.Y,Home.Z):GetActorLocation()+GetActorForwardVector()*85.f;
        if(!bImpactPlayed)
        {bImpactPlayed=true;PlaySound(ImpactSound,Ground,.7f,.92f);if(auto* FX=AAshWellBattleFX::Find(GetWorld()))FX->Burst(Ground,.9f,false,false);}
        const FVector D=Target->GetActorLocation()-Ground;
        FHitResult Block;
        const bool Wall=GetWorld()->LineTraceSingleByChannel(Block,Ground+FVector(0,0,45),Target->GetActorLocation(),ECC_Visibility,Params)&&Block.GetActor()!=Target.Get();
        const float Radius=AttackKind==EMountedBossAttack::LeapShield?260.f:275.f;
        Contact=!Wall&&D.Size2D()<Radius&&FMath::Abs(D.Z)<155.f;
    }
    else if(AttackKind==EMountedBossAttack::BodyCheck)
    {
        // The same swept horse-body collider that blocks movement reports this contact.
        // It is harmful only during the explicit body-check window.
        Contact=bBodyContactPending;
    }
    else
    {
        if(AttackKind==EMountedBossAttack::Charge&&StateTime<.16f)return;
        // Sweep the distal 95 cm of the rigid, visible polearm, including between-frame travel.
        for(int32 I=0;I<7&&!Contact;++I)
        {
            const float A=.51f+.49f*I/6.f;
            Contact=GetWorld()->SweepSingleByChannel(Hit,FMath::Lerp(PreviousGrip,PreviousTip,A),FMath::Lerp(WeaponGrip,WeaponTip,A),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeSphere(18.f),Params)&&Hit.GetActor()==Target.Get();
        }
        if(!Contact&&bPreviousWeaponPoseValid&&Weapon&&Weapon->GetStaticMesh()&&Weapon->GetStaticMesh()->GetFName()==FName(TEXT("SM_MountedHalberd")))
        {
            // Actual outer edge from Scripts/build_mounted_asset_props.py, in mesh-local cm:
            // (125,0,39) -> (144,0,51) -> (169,0,47). Midpoints keep sample spacing <= 13 cm.
            // These cover visible metal outside the shaft without inflating the existing 18 cm tolerance.
            const FVector EdgeSamples[]={FVector(125,0,39),FVector(134.5f,0,45),FVector(144,0,51),FVector(156.5f,0,49),FVector(169,0,47)};
            const FTransform CurrentWeaponTransform=Weapon->GetComponentTransform();
            for(const FVector& LocalPoint:EdgeSamples)
            {
                Contact=GetWorld()->SweepSingleByChannel(Hit,PreviousWeaponTransform.TransformPosition(LocalPoint),CurrentWeaponTransform.TransformPosition(LocalPoint),FQuat::Identity,ECC_Pawn,FCollisionShape::MakeSphere(18.f),Params)&&Hit.GetActor()==Target.Get();
                if(Contact){BladeContact=true;break;}
            }
        }
    }
    if(Contact)
    {
        bDamageConsumed=true;++ContactCount;
        if(AttackKind==EMountedBossAttack::Rear||AttackKind==EMountedBossAttack::LeapShield)++AreaContactCount;
        else if(AttackKind==EMountedBossAttack::BodyCheck)++BodyContactCount;else ++WeaponContactCount;
        if(BladeContact)++BladeEdgeContactCount;
        const float Applied=UGameplayStatics::ApplyDamage(Target.Get(),Spec().Damage,nullptr,this,nullptr);
        if(Applied>0)PlaySound(ImpactSound,Target->GetActorLocation(),.32f,1.16f);
        UE_LOG(LogTemp,Display,TEXT("AW_MOUNTED_CONTACT kind=%s applied=%.1f window=%.3f"),*GetAttackLabel(),Applied,StateTime);
    }
}

void AAshWellMountedBoss::CacheWeaponSweepPose()
{
    PreviousGrip=WeaponGrip;PreviousTip=WeaponTip;PreviousShield=ShieldPoint;
    bPreviousWeaponPoseValid=Weapon!=nullptr;
    if(Weapon)PreviousWeaponTransform=Weapon->GetComponentTransform();
    bResetWeaponSweep=false;
}

bool AAshWellMountedBoss::ReceiveMeleeHit(float Damage,const FVector& Source,uint64 AttackId)
{
    if(IsDead()||IsReturning()||Damage<=0)return false;
    if(AttackId&&ReceivedAttackIds.Contains(AttackId)){++DuplicateReceiveRejected;return false;}
    if(AttackId)ReceivedAttackIds.Add(AttackId);
    Health=FMath::Max(0.f,Health-Damage);HitReaction=.6f;
    if(Health<=MaximumHealth*.5f&&!bPhaseTwo)bPhasePending=true;
    // Mounted attacks have armour; receiving damage never cancels or shortens their recovery.
    if(Health<=0)ChangeState(EMountedBossState::Dead);
    else if(State==EMountedBossState::Approach&&FightTime-LastHitTime>1.5f)
    {Speed*=.6f;DecisionDelay=FMath::Max(DecisionDelay,.20f);LastHitTime=FightTime;}
    return true;
}

FVector AAshWellMountedBoss::GetAimPoint() const{return GetActorLocation()+FVector(0,0,185.f);}
FVector AAshWellMountedBoss::GetAttackContact() const{return AttackKind==EMountedBossAttack::BodyCheck?ShieldPoint:AttackKind==EMountedBossAttack::Rear?GetActorLocation()+GetActorForwardVector()*85.f:WeaponTip;}
float AAshWellMountedBoss::GetAttackProgress() const{return State==EMountedBossState::Windup?FMath::Clamp(StateTime/Spec().Windup,0.f,1.f):State==EMountedBossState::Active?FMath::Clamp(StateTime/Spec().Active,0.f,1.f):0.f;}
FString AAshWellMountedBoss::GetStateLabel() const
{static const TCHAR* N[]={TEXT("idle"),TEXT("approach"),TEXT("windup"),TEXT("active"),TEXT("recovery"),TEXT("phase_change"),TEXT("return"),TEXT("dead")};return N[static_cast<int32>(State)];}
FString AAshWellMountedBoss::GetAttackLabel() const
{static const TCHAR* N[]={TEXT("sweep"),TEXT("overhead"),TEXT("charge"),TEXT("body_check"),TEXT("rear"),TEXT("leap_shield")};return N[static_cast<int32>(AttackKind)];}
void AAshWellMountedBoss::PlaySound(USoundBase* Sound,const FVector& Point,float Volume,float Pitch)
{
    ActiveAudio.RemoveAll([](const auto& A){return !IsValid(A)||!A->IsPlaying();});
    if(Sound&&!bAudioPaused)if(auto* A=UGameplayStatics::SpawnSoundAtLocation(this,Sound,Point,FRotator::ZeroRotator,Volume,Pitch)){A->bShouldRemainActiveIfDropped=false;ActiveAudio.Add(A);}
}

bool AAshWellMountedBoss::IsQAEnabled() const
{return FParse::Param(FCommandLine::Get(),TEXT("MountedQA"))||FCString::Strifind(FCommandLine::Get(),TEXT("MountedProbe="))!=nullptr||FParse::Param(FCommandLine::Get(),TEXT("MountedDebug"));}
void AAshWellMountedBoss::SetQAStationary(bool bStationary){if(IsQAEnabled())bQAStationary=bStationary;}
void AAshWellMountedBoss::SetQAHealth(float NewHealth)
{if(IsQAEnabled()){Health=FMath::Clamp(NewHealth,0.f,MaximumHealth);if(Health<=0)ChangeState(EMountedBossState::Dead);else if(Health<=MaximumHealth*.5f&&!bPhaseTwo)bPhasePending=true;}}
bool AAshWellMountedBoss::ForceAttack(const FString& Name)
{
    if(!IsQAEnabled()||!Target.IsValid()||IsDead())return false;
    const TCHAR* Names[]={TEXT("sweep"),TEXT("overhead"),TEXT("charge"),TEXT("body_check"),TEXT("rear"),TEXT("leap_shield")};
    for(int32 I=0;I<6;++I)if(Name.Equals(Names[I],ESearchCase::IgnoreCase))
    {if(I>=4)bPhaseTwo=true;++SelectionCount;BeginAttack(static_cast<EMountedBossAttack>(I));return true;}
    return false;
}

TSharedRef<FJsonObject> AAshWellMountedBoss::GetTelemetry() const
{
    auto O=MakeShared<FJsonObject>();
    O->SetBoolField(TEXT("hoof_bones_valid"),bHoofBonesValid);O->SetNumberField(TEXT("hoof_contacts"),HoofContacts);O->SetNumberField(TEXT("support_sample_seconds"),SupportSampleTime);O->SetNumberField(TEXT("support_drift_cm_s"),SupportSampleTime>0?SupportDriftDistance/SupportSampleTime:0);
    O->SetNumberField(TEXT("shield_ground_gap_cm"),ShieldPoint.Z-Home.Z-90.f);O->SetNumberField(TEXT("attack_serial"),AttackSerial);O->SetBoolField(TEXT("hit_window_open"),IsHitWindowOpen());O->SetNumberField(TEXT("body_contacts"),BodyContactCount);
    O->SetNumberField(TEXT("cancelled_attacks"),CancelledAttacks);O->SetNumberField(TEXT("duplicate_receive_rejected"),DuplicateReceiveRejected);O->SetNumberField(TEXT("maximum_leap_height_cm"),MaximumLeapHeight);O->SetBoolField(TEXT("leap_landed"),bLeapLanded);
    O->SetNumberField(TEXT("active_audio_components"),ActiveAudio.FilterByPredicate([](const auto& A){return IsValid(A)&&A->IsPlaying();}).Num());
    O->SetStringField(TEXT("state"),GetStateLabel());O->SetStringField(TEXT("attack"),GetAttackLabel());
    O->SetNumberField(TEXT("health"),Health);O->SetNumberField(TEXT("speed_cm_s"),Speed);
    O->SetNumberField(TEXT("maximum_health"),MaximumHealth);O->SetNumberField(TEXT("actual_speed_cm_s"),ActualSpeed);O->SetNumberField(TEXT("blocked_turn_count"),BlockedTurnCount);
    const FVector BodyHalfExtents=BodyCollision->GetScaledBoxExtent();
    O->SetNumberField(TEXT("body_half_length_cm"),BodyHalfExtents.X);O->SetNumberField(TEXT("body_half_width_cm"),BodyHalfExtents.Y);O->SetNumberField(TEXT("body_half_height_cm"),BodyHalfExtents.Z);
    O->SetNumberField(TEXT("state_time"),StateTime);O->SetNumberField(TEXT("fight_time"),FightTime);
    O->SetNumberField(TEXT("distance_travelled_cm"),DistanceTravelled);O->SetNumberField(TEXT("gait_phase"),GaitPhase);
    O->SetNumberField(TEXT("heading_yaw"),GetActorRotation().Yaw);O->SetNumberField(TEXT("committed_yaw"),CommittedYaw);
    O->SetNumberField(TEXT("committed_yaw_drift"),MaximumCommittedYawDrift);O->SetBoolField(TEXT("heading_committed"),bHeadingCommitted);
    O->SetNumberField(TEXT("windup_seconds"),Spec().Windup);O->SetNumberField(TEXT("active_seconds"),Spec().Active);O->SetNumberField(TEXT("recovery_seconds"),Spec().Recovery);
    O->SetNumberField(TEXT("commit_at_seconds"),Spec().Windup-Spec().CommitLead);
    O->SetNumberField(TEXT("strikes"),StrikeCount);O->SetNumberField(TEXT("contacts"),ContactCount);
    O->SetNumberField(TEXT("weapon_contacts"),WeaponContactCount);O->SetNumberField(TEXT("shield_contacts"),ShieldContactCount);O->SetNumberField(TEXT("area_contacts"),AreaContactCount);
    O->SetNumberField(TEXT("blade_edge_contacts"),BladeEdgeContactCount);O->SetNumberField(TEXT("blade_edge_samples"),5);O->SetNumberField(TEXT("weapon_sweep_radius_cm"),18);
    O->SetNumberField(TEXT("reset_count"),ResetCount);O->SetBoolField(TEXT("phase_two"),bPhaseTwo);O->SetBoolField(TEXT("combo_pending"),bComboPending);
    O->SetBoolField(TEXT("horse_visual"),bHorseVisual);O->SetBoolField(TEXT("rider_visual"),bRiderVisual);
    O->SetBoolField(TEXT("walk_loaded"),HorseWalk!=nullptr);O->SetBoolField(TEXT("run_loaded"),HorseRun!=nullptr);O->SetBoolField(TEXT("rear_loaded"),HorseRear!=nullptr);O->SetBoolField(TEXT("death_loaded"),HorseDeath!=nullptr);
    O->SetStringField(TEXT("horse_animation"),CurrentHorseAnimation?CurrentHorseAnimation->GetName():TEXT("fallback"));
    O->SetNumberField(TEXT("horse_animation_time"),HorseAnimationTime);
    O->SetNumberField(TEXT("horse_animation_phase"),CurrentHorseAnimation&&CurrentHorseAnimation->GetPlayLength()>0?HorseAnimationTime/CurrentHorseAnimation->GetPlayLength():0.f);
    O->SetNumberField(TEXT("walk_reference_cm_s"),114.13f);O->SetNumberField(TEXT("gallop_reference_cm_s"),477.34f);
    O->SetBoolField(TEXT("saddle_bone_follow"),bHorseSeatBone);O->SetBoolField(TEXT("rear_procedural"),HorseRear==nullptr);
    O->SetNumberField(TEXT("x"),GetActorLocation().X);O->SetNumberField(TEXT("y"),GetActorLocation().Y);O->SetNumberField(TEXT("z"),GetActorLocation().Z);
    auto V=[&](const TCHAR* Prefix,const FVector& Point){O->SetNumberField(FString(Prefix)+TEXT("_x"),Point.X);O->SetNumberField(FString(Prefix)+TEXT("_y"),Point.Y);O->SetNumberField(FString(Prefix)+TEXT("_z"),Point.Z);};
    V(TEXT("weapon_tip"),WeaponTip);V(TEXT("weapon_grip"),WeaponGrip);V(TEXT("shield"),ShieldPoint);
    if(Weapon)V(TEXT("blade_outer"),Weapon->GetComponentTransform().TransformPosition(FVector(144,0,51)));
    return O;
}
FString AAshWellMountedBoss::GetTelemetryJson() const
{FString Text;FJsonSerializer::Serialize(GetTelemetry(),TJsonWriterFactory<>::Create(&Text));return Text;}
