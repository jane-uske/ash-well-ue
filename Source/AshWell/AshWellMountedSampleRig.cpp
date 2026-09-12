#include "AshWellMountedSampleRig.h"
#include "AshWellMountedSampleAnimation.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimMontage.h"
#include "Curves/CurveFloat.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMeshSocket.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

AAshWellMountedSampleRig::AAshWellMountedSampleRig()
{
    PrimaryActorTick.bCanEverTick=false;
    auto* Root=CreateDefaultSubobject<USceneComponent>(TEXT("SampleRoot"));SetRootComponent(Root);
    ReviewCamera=CreateDefaultSubobject<UCameraComponent>(TEXT("AssetInspectionCamera"));ReviewCamera->SetupAttachment(Root);ReviewCamera->FieldOfView=65;
    Horse=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SampleHorse"));Horse->SetupAttachment(Root);Horse->SetRelativeScale3D(FVector(1.3f));Horse->SetRelativeRotation(FRotator(0,90,0));
    // Local rider/horse proportions; the owning boss scales the complete assembly.
    Rider=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SampleRider"));Rider->SetupAttachment(Root);Rider->SetRelativeScale3D(FVector(1.6f));
    Poleaxe=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SamplePoleaxe"));Poleaxe->SetupAttachment(Rider,TEXT("SampleWeaponGrip"));Poleaxe->SetAbsolute(false,false,true);
    Shield=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SampleShield"));Shield->SetupAttachment(Rider,TEXT("SampleShieldGrip"));Shield->SetAbsolute(false,false,true);
    // Match the retained combat reach with visible geometry (196 cm grip-to-tip),
    // rather than increasing the hit tolerance around a shorter new weapon.
    Poleaxe->SetRelativeScale3D(FVector(280.f/245.f));
    Shield->SetRelativeScale3D(FVector(150.f/105.f));
    for(auto* M:{Horse.Get(),Rider.Get()})
    {M->SetCollisionEnabled(ECollisionEnabled::NoCollision);M->SetGenerateOverlapEvents(false);M->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;M->PrimaryComponentTick.bStartWithTickEnabled=false;}
    for(auto* M:{Poleaxe.Get(),Shield.Get()}){M->SetCollisionEnabled(ECollisionEnabled::NoCollision);M->SetGenerateOverlapEvents(false);}
}
void AAshWellMountedSampleRig::BeginPlay()
{
    Super::BeginPlay();
    const FString Base=TEXT("/Game/AshWell/Combat/MountedChargeSample/");
    auto Skin=[&](const TCHAR* N){return LoadObject<USkeletalMesh>(nullptr,*(Base+N+TEXT(".")+N));};
    auto Static=[&](const TCHAR* N){return LoadObject<UStaticMesh>(nullptr,*(Base+N+TEXT(".")+N));};
    Horse->SetSkeletalMesh(Skin(TEXT("SK_SampleHorse")));Rider->SetSkeletalMesh(Skin(TEXT("SK_SampleKnight")));
    const bool ContactCandidate=FParse::Param(FCommandLine::Get(),TEXT("MountedFootPlacement"));bFootPlacementCandidate=ContactCandidate;
    Horse->SetAnimInstanceClass(LoadClass<UAnimInstance>(nullptr,*(Base+(ContactCandidate?TEXT("FootContactCandidate/ABP_SampleHorse_Planted.ABP_SampleHorse_Planted_C"):TEXT("ABP_SampleHorse.ABP_SampleHorse_C")))));
    Rider->SetAnimInstanceClass(LoadClass<UAnimInstance>(nullptr,*(Base+TEXT("ABP_SampleRider.ABP_SampleRider_C"))));
    Poleaxe->SetStaticMesh(Static(TEXT("SM_SamplePoleaxe")));Shield->SetStaticMesh(Static(TEXT("SM_SampleShield")));
    // Only a player's complex blade trace sees the visible shield triangles.
    // It never becomes another locomotion collider for the horse or player.
    Shield->SetCollisionEnabled(ECollisionEnabled::QueryOnly);Shield->SetCollisionObjectType(ECC_WorldDynamic);
    Shield->SetCollisionResponseToAllChannels(ECR_Ignore);Shield->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    Shield->SetCanEverAffectNavigation(false);
    ActionSet=LoadObject<UAshWellMountedActionSet>(nullptr,*(Base+TEXT("DA_MountedSampleActions.DA_MountedSampleActions")));
    if(ActionSet)Charge=ActionSet->Montages.FindRef(TEXT("charge"));
    Horse->SetComponentTickEnabled(false);Rider->SetComponentTickEnabled(false);
    if(Horse->GetSkeletalMeshAsset())
    {
        const auto& Ref=Horse->GetSkeletalMeshAsset()->GetRefSkeleton();const int32 Index=Ref.FindBoneIndex(TEXT("Bone_002"));
        auto Poses=Ref.GetRefBonePose();for(int32 I=0;I<Poses.Num();++I)if(Ref.GetParentIndex(I)>=0)Poses[I]*=Poses[Ref.GetParentIndex(I)];
        if(Poses.IsValidIndex(Index))SeatRest=Poses[Index];
    }
    bReady=Horse->GetAnimInstance()&&RiderAnimation()&&Poleaxe->GetStaticMesh()&&Shield->GetStaticMesh()&&Charge;
    UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_RIG ready=%d horse_abp=%s rider_abp=%s"),bReady,*GetNameSafe(Horse->GetAnimInstance()),*GetNameSafe(Rider->GetAnimInstance()));
    EvaluatePose(0,0);
}
UAshWellMountedSampleAnimInstance* AAshWellMountedSampleRig::RiderAnimation() const{return Cast<UAshWellMountedSampleAnimInstance>(Rider->GetAnimInstance());}
void AAshWellMountedSampleRig::EvaluatePose(float Dt,float Speed,bool DeferHorse)
{
    if(!bReady)return;
    if(Dt>0)PreviousChargeElapsed=ChargeElapsed;
    const FQuat Tilt=FRotator(LegacyPitch,0,0).Quaternion();
    Horse->SetRelativeRotation(Tilt*FRotator(0,90,0).Quaternion());
    Horse->SetRelativeLocation(FVector(-79,0,0)-Tilt.RotateVector(FVector(-79,0,0)));
    if(auto* A=Cast<UAshWellMountedSampleAnimInstance>(Horse->GetAnimInstance()))
    {
        A->GroundSpeed=Speed/FMath::Max(.01f,float(GetActorScale3D().X));
        // Individual BlendSpace samples carry their calibrated cadence. A second
        // speed multiplier here made the idle/walk transition slow down twice.
        A->StrideRate=1.f;
        A->HorseContactAlpha=bGroundContactEnabled&&!bDeathPose&&FMath::Abs(LegacyPitch)<1.f?1.f:0.f;
    }
    if(DeferHorse)PendingHorseDelta+=Dt;
    else
    {
        // Foot Placement needs the completed actor move and the actual frame
        // delta. Advance the rider's Montage first for combat timing, then solve
        // the horse once after movement instead of evaluating its springs twice.
        Horse->TickAnimation(Dt+PendingHorseDelta,false);Horse->RefreshBoneTransforms();PendingHorseDelta=0;
    }
    const FTransform Bone=Horse->GetSocketTransform(TEXT("Bone_002"),RTS_Component);
    const FQuat Delta=Bone.GetRotation()*SeatRest.GetRotation().Inverse();
    // FBX scene conversion makes imported component forward -Y. The component's
    // +90 degree yaw restores the boss +X convention; contacts use imported space.
    const FVector Seat=Bone.TransformPosition(SeatRest.InverseTransformPosition(FVector(0,10,128)));
    const FQuat SeatWorldRotation=Horse->GetComponentQuat()*Delta;
    const FVector RiderScale=Rider->GetComponentScale();
    Rider->SetWorldLocationAndRotation(Horse->GetComponentTransform().TransformPosition(Seat)-SeatWorldRotation.RotateVector(FVector(-.733457,-2.028657,89.98887)*RiderScale),SeatWorldRotation);
    // Keep the pelvis on the saddle and the boot soles on the stirrups when
    // changing rider size; the native AnimBP still solves the legs.
    const FVector AnkleOffset=SeatWorldRotation.RotateVector(FVector(0,0,13.4f*RiderScale.Z/1.35f));
    const FVector LeftTarget=Horse->GetSocketLocation(TEXT("SampleStirrupLeft"))+AnkleOffset;
    const FVector RightTarget=Horse->GetSocketLocation(TEXT("SampleStirrupRight"))+AnkleOffset;
    if(auto* A=RiderAnimation())
    {
        A->RiderContactAlpha=FMath::FInterpConstantTo(A->RiderContactAlpha,bDeathPose?0.f:1.f,Dt,5.f);
        A->LeftFootTarget=Rider->GetComponentTransform().InverseTransformPosition(LeftTarget);A->RightFootTarget=Rider->GetComponentTransform().InverseTransformPosition(RightTarget);
        A->LegacyAlpha=FMath::FInterpConstantTo(A->LegacyAlpha,bLegacyPose&&!bChargeStarted?1.f:0.f,Dt,8.f);
        A->LegacyRightHand=Rider->GetComponentTransform().InverseTransformPosition(LegacyGrip);
        A->LegacyLeftHand=Rider->GetComponentTransform().InverseTransformPosition(LegacyShieldHand);
        A->LegacyPelvisOffset=Rider->GetComponentTransform().InverseTransformVectorNoScale(GetActorQuat().RotateVector(LegacyPelvisOffset));
        const FQuat Basis=Rider->GetComponentQuat().Inverse()*GetActorQuat();
        A->LegacyTorsoRotation=(Basis*LegacyTorso*Basis.Inverse()).Rotator();
        if(const auto* Socket=Rider->GetSkeletalMeshAsset()->FindSocket(TEXT("SampleWeaponGrip")))
            A->LegacyRightHandRotation=(Rider->GetComponentQuat().Inverse()*FRotationMatrix::MakeFromY(-LegacyDirection).ToQuat()*Socket->RelativeRotation.Quaternion().Inverse()).Rotator();
        if(const auto* Socket=Rider->GetSkeletalMeshAsset()->FindSocket(TEXT("SampleShieldGrip")))
            A->LegacyLeftHandRotation=(FQuat(FVector::UpVector,PI)*Socket->RelativeRotation.Quaternion().Inverse()).Rotator();
    }
    Rider->TickAnimation(Dt,false);Rider->RefreshBoneTransforms();
    if(bChargeStarted)
    {
        auto* A=RiderAnimation();const float End=Charge->GetPlayLength();
        ChargeElapsed=A->Montage_IsActive(Charge)?FMath::Max(ChargeElapsed,A->Montage_GetPosition(Charge)):End;
        // A held native Montage stops just short of the final sample. Canonicalize
        // only its sub-millisecond endpoint, never the earlier blend-out interval.
        if(!A->Montage_IsPlaying(Charge)&&ChargeElapsed>=End-.0001f)ChargeElapsed=End;
    }
    // Grip sockets inherit scale; these props deliberately keep absolute scale
    // so rider-only proportion edits do not silently resize them.
    Poleaxe->SetWorldScale3D(GetActorScale3D()*(280.f/245.f));
    Shield->SetWorldScale3D(GetActorScale3D()*(150.f/105.f));
    Poleaxe->UpdateComponentToWorld();Shield->UpdateComponentToWorld();
    if(FParse::Param(FCommandLine::Get(),TEXT("MountedAssetReview"))&&FParse::Param(FCommandLine::Get(),TEXT("MountedReviewOrbit")))
    {
        // A-only inspection fixture: camera moves, animation remains at real time.
        ReviewTime+=Dt;const float Angle=ReviewTime*PI/10.f;
        const float Scale=GetActorScale3D().Z;
        const FVector Focus=GetActorLocation()+FVector(0,0,(bDeathPose?90:210)*Scale);
        const FVector Eye=Focus+FVector(FMath::Cos(Angle)*740*Scale,FMath::Sin(Angle)*740*Scale,65*Scale);
        ReviewCamera->SetWorldLocationAndRotation(Eye,(Focus-Eye).Rotation());
        if(auto* PC=GetWorld()->GetFirstPlayerController())PC->SetViewTarget(this);
    }
    ReportTime+=Dt;
    if(ReportTime>1.f&&!DeferHorse)
    {
        ReportTime=0;auto* A=RiderAnimation();
        if(bChargeStarted&&HorseCharge)
        {auto* H=Horse->GetAnimInstance();UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_PAIR rider=%.4f horse=%.4f drift=%.4f"),GetChargeTime(),H->Montage_GetPosition(HorseCharge),FMath::Abs(GetChargeTime()-H->Montage_GetPosition(HorseCharge)));}
        const FVector L=Rider->GetSocketTransform(TEXT("LeftFoot"),RTS_Component).GetLocation();const FVector R=Rider->GetSocketTransform(TEXT("RightFoot"),RTS_Component).GetLocation();
        UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_POSE speed=%.1f montage=%.3f window=%d footL=%s footR=%s contactL=%.3f contactR=%.3f phase=%s"),Speed,GetChargeTime(),A->bWeaponWindow,*L.ToCompactString(),*R.ToCompactString(),FVector::Distance(Rider->GetSocketLocation(TEXT("LeftFoot")),LeftTarget),FVector::Distance(Rider->GetSocketLocation(TEXT("RightFoot")),RightTarget),*A->ActionPhase.ToString());
    }
}
void AAshWellMountedSampleRig::SetLegacyPose(FVector Grip,FVector Direction,FVector ShieldHand,FQuat Torso,float Pitch,bool Enabled,FVector PelvisOffset)
{LegacyGrip=Grip;LegacyDirection=Direction;LegacyShieldHand=ShieldHand;LegacyTorso=Torso;LegacyPitch=Pitch;bLegacyPose=Enabled;LegacyPelvisOffset=PelvisOffset;}
bool AAshWellMountedSampleRig::HasAuthoredAction(FName Action) const{return ActionSet&&IsValid(ActionSet->Montages.FindRef(Action));}
const FMountedAuthoredAction* AAshWellMountedSampleRig::GetActionDefinition(FName Action) const
{return ActionSet?ActionSet->AuthoredActions.Find(Action):nullptr;}
float AAshWellMountedSampleRig::GetAuthoredFrameSpeed(float Dt) const
{
    const auto* Definition=GetActionDefinition(ActiveAction);
    if(!bChargeStarted||!Definition||!Definition->ForwardDistance||Dt<=SMALL_NUMBER)return 0;
    return FMath::Max(0.f,(Definition->ForwardDistance->GetFloatValue(ChargeElapsed)-Definition->ForwardDistance->GetFloatValue(PreviousChargeElapsed))/Dt);
}
bool AAshWellMountedSampleRig::PlayCharge(){return PlayAction(TEXT("charge"));}
bool AAshWellMountedSampleRig::PlayDeath()
{
    StopCharge();
    auto* A=RiderAnimation();auto* H=Horse->GetAnimInstance();
    if(!A||!H||!ActionSet||!ActionSet->RiderDeath||!ActionSet->HorseDeath)
    {UE_LOG(LogTemp,Error,TEXT("AW_SAMPLE_DEATH_BLOCKED missing paired death assets"));return false;}
    Charge=ActionSet->RiderDeath;HorseCharge=ActionSet->HorseDeath;ActiveAction=TEXT("death");
    bDeathPose=true;ChargeElapsed=PreviousChargeElapsed=0;
    bChargeStarted=A->Montage_Play(Charge,1.f)>0&&H->Montage_Play(HorseCharge,1.f)>0;
    UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_DEATH ready=%d"),bChargeStarted);return bChargeStarted;
}
bool AAshWellMountedSampleRig::PlayAction(FName Action)
{
    auto* A=RiderAnimation();if(!A||!HasAuthoredAction(Action))return false;
    StopCharge();Charge=ActionSet->Montages.FindRef(Action);A->ClearActionState();A->bActionNotifiesEnabled=true;
    ChargeElapsed=PreviousChargeElapsed=0;ActiveAction=Action;
    bChargeStarted=A->Montage_Play(Charge,1.f)>0;
    if(const auto* D=GetActionDefinition(Action))
    {
        HorseCharge=D->HorseMontage;
        auto* H=Horse->GetAnimInstance();
        if(!HorseCharge||!D->ForwardDistance||!H||H->Montage_Play(HorseCharge,1.f)<=0)
        {UE_LOG(LogTemp,Error,TEXT("AW_SAMPLE_BLOCKED missing paired horse montage or displacement curve"));StopCharge();return false;}
    }
    return bChargeStarted;
}
void AAshWellMountedSampleRig::StopCharge(){bChargeStarted=bDeathPose=false;if(auto* H=Horse->GetAnimInstance())if(HorseCharge)H->Montage_Stop(.15f,HorseCharge);HorseCharge=nullptr;ActiveAction=NAME_None;if(auto* A=RiderAnimation()){A->Montage_Stop(.15f,Charge);A->ClearActionState();}}
float AAshWellMountedSampleRig::GetChargeTime() const {return ChargeElapsed;}
bool AAshWellMountedSampleRig::IsChargePlaying() const {auto* A=RiderAnimation();return A&&Charge&&A->Montage_IsPlaying(Charge);}
bool AAshWellMountedSampleRig::HasWeaponWindow() const {auto* A=RiderAnimation();return A&&A->bWeaponWindow;}
FVector AAshWellMountedSampleRig::GetGrip() const{return Poleaxe->GetComponentLocation();}
FVector AAshWellMountedSampleRig::GetTip() const{return Poleaxe->GetComponentTransform().TransformPosition(FVector(0,-171.5f,0));}
void AAshWellMountedSampleRig::EndPlay(const EEndPlayReason::Type Reason){StopCharge();Super::EndPlay(Reason);}
