#include "AshWellMountedSampleRig.h"
#include "AshWellMountedSampleAnimation.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Animation/AnimMontage.h"
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
    Rider=CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SampleRider"));Rider->SetupAttachment(Root);Rider->SetRelativeScale3D(FVector(1.35f));
    Poleaxe=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SamplePoleaxe"));Poleaxe->SetupAttachment(Rider,TEXT("SampleWeaponGrip"));Poleaxe->SetAbsolute(false,false,true);
    Shield=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SampleShield"));Shield->SetupAttachment(Rider,TEXT("SampleShieldGrip"));Shield->SetAbsolute(false,false,true);
    // Match the retained combat reach with visible geometry (196 cm grip-to-tip),
    // rather than increasing the hit tolerance around a shorter new weapon.
    Poleaxe->SetRelativeScale3D(FVector(280.f/245.f));
    Shield->SetRelativeScale3D(FVector(180.f/105.f));
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
    Horse->SetAnimInstanceClass(LoadClass<UAnimInstance>(nullptr,*(Base+TEXT("ABP_SampleHorse.ABP_SampleHorse_C"))));
    Rider->SetAnimInstanceClass(LoadClass<UAnimInstance>(nullptr,*(Base+TEXT("ABP_SampleRider.ABP_SampleRider_C"))));
    Poleaxe->SetStaticMesh(Static(TEXT("SM_SamplePoleaxe")));Shield->SetStaticMesh(Static(TEXT("SM_SampleShield")));
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
void AAshWellMountedSampleRig::EvaluatePose(float Dt,float Speed)
{
    if(!bReady)return;
    const FQuat Tilt=FRotator(LegacyPitch,0,0).Quaternion();
    Horse->SetRelativeRotation(Tilt*FRotator(0,90,0).Quaternion());
    Horse->SetRelativeLocation(FVector(-79,0,0)-Tilt.RotateVector(FVector(-79,0,0)));
    if(auto* A=Cast<UAshWellMountedSampleAnimInstance>(Horse->GetAnimInstance()))
    {A->GroundSpeed=Speed;A->StrideRate=Speed>250?FMath::Clamp(Speed/550.f,.65f,1.7f):Speed>15?FMath::Clamp(Speed/150.f,.55f,1.2f):1.f;}
    Horse->TickAnimation(Dt,false);Horse->RefreshBoneTransforms();
    const FTransform Bone=Horse->GetSocketTransform(TEXT("Bone_002"),RTS_Component);
    const FQuat Delta=Bone.GetRotation()*SeatRest.GetRotation().Inverse();
    // FBX scene conversion makes imported component forward -Y. The component's
    // +90 degree yaw restores the boss +X convention; contacts use imported space.
    const FVector Seat=Bone.TransformPosition(SeatRest.InverseTransformPosition(FVector(0,10,128)));
    const FQuat SeatWorldRotation=Horse->GetComponentQuat()*Delta;
    Rider->SetWorldLocationAndRotation(Horse->GetComponentTransform().TransformPosition(Seat)-SeatWorldRotation.RotateVector(FVector(-.733457,-2.028657,89.98887)*1.35f),SeatWorldRotation);
    const FVector LeftTarget=Horse->GetSocketLocation(TEXT("SampleStirrupLeft"))+SeatWorldRotation.RotateVector(FVector(0,0,13.4f));
    const FVector RightTarget=Horse->GetSocketLocation(TEXT("SampleStirrupRight"))+SeatWorldRotation.RotateVector(FVector(0,0,13.4f));
    if(auto* A=RiderAnimation())
    {
        A->LeftFootTarget=Rider->GetComponentTransform().InverseTransformPosition(LeftTarget);A->RightFootTarget=Rider->GetComponentTransform().InverseTransformPosition(RightTarget);
        A->LegacyAlpha=FMath::FInterpConstantTo(A->LegacyAlpha,bLegacyPose&&!bChargeStarted?1.f:0.f,Dt,8.f);
        A->LegacyRightHand=Rider->GetComponentTransform().InverseTransformPosition(LegacyGrip);
        A->LegacyLeftHand=Rider->GetComponentTransform().InverseTransformPosition(LegacyShieldHand);
        const FQuat Basis=Rider->GetComponentQuat().Inverse()*GetActorQuat();
        A->LegacyTorsoRotation=(Basis*LegacyTorso*Basis.Inverse()).Rotator();
        if(const auto* Socket=Rider->GetSkeletalMeshAsset()->FindSocket(TEXT("SampleWeaponGrip")))
            A->LegacyRightHandRotation=(Rider->GetComponentQuat().Inverse()*FRotationMatrix::MakeFromY(-LegacyDirection).ToQuat()*Socket->RelativeRotation.Quaternion().Inverse()).Rotator();
        if(const auto* Socket=Rider->GetSkeletalMeshAsset()->FindSocket(TEXT("SampleShieldGrip")))
            A->LegacyLeftHandRotation=(FQuat(FVector::UpVector,PI)*Socket->RelativeRotation.Quaternion().Inverse()).Rotator();
    }
    Rider->TickAnimation(Dt,false);Rider->RefreshBoneTransforms();
    if(bChargeStarted)
    {auto* A=RiderAnimation();ChargeElapsed=A->Montage_IsActive(Charge)?FMath::Max(ChargeElapsed,A->Montage_GetPosition(Charge)):Charge->GetPlayLength();}
    Poleaxe->UpdateComponentToWorld();Shield->UpdateComponentToWorld();
    if(FParse::Param(FCommandLine::Get(),TEXT("MountedAssetReview"))&&FParse::Param(FCommandLine::Get(),TEXT("MountedReviewOrbit")))
    {
        // A-only inspection fixture: camera moves, animation remains at real time.
        ReviewTime+=Dt;const float Angle=ReviewTime*PI/10.f;
        const FVector Focus=GetActorLocation()+FVector(0,0,210);
        const FVector Eye=Focus+FVector(FMath::Cos(Angle)*740,FMath::Sin(Angle)*740,65);
        ReviewCamera->SetWorldLocationAndRotation(Eye,(Focus-Eye).Rotation());
        if(auto* PC=GetWorld()->GetFirstPlayerController())PC->SetViewTarget(this);
    }
    ReportTime+=Dt;
    if(ReportTime>1.f)
    {
        ReportTime=0;auto* A=RiderAnimation();
        const FVector L=Rider->GetSocketTransform(TEXT("LeftFoot"),RTS_Component).GetLocation();const FVector R=Rider->GetSocketTransform(TEXT("RightFoot"),RTS_Component).GetLocation();
        UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_POSE speed=%.1f montage=%.3f window=%d footL=%s footR=%s contactL=%.3f contactR=%.3f phase=%s"),Speed,GetChargeTime(),A->bWeaponWindow,*L.ToCompactString(),*R.ToCompactString(),FVector::Distance(Rider->GetSocketLocation(TEXT("LeftFoot")),LeftTarget),FVector::Distance(Rider->GetSocketLocation(TEXT("RightFoot")),RightTarget),*A->ActionPhase.ToString());
    }
}
void AAshWellMountedSampleRig::SetLegacyPose(FVector Grip,FVector Direction,FVector ShieldHand,FQuat Torso,float Pitch,bool Enabled)
{LegacyGrip=Grip;LegacyDirection=Direction;LegacyShieldHand=ShieldHand;LegacyTorso=Torso;LegacyPitch=Pitch;bLegacyPose=Enabled;}
bool AAshWellMountedSampleRig::HasAuthoredAction(FName Action) const{return ActionSet&&IsValid(ActionSet->Montages.FindRef(Action));}
bool AAshWellMountedSampleRig::PlayCharge(){return PlayAction(TEXT("charge"));}
bool AAshWellMountedSampleRig::PlayAction(FName Action)
{
    auto* A=RiderAnimation();if(!A||!HasAuthoredAction(Action))return false;
    StopCharge();Charge=ActionSet->Montages.FindRef(Action);A->ClearActionState();A->bActionNotifiesEnabled=true;
    ChargeElapsed=0;bChargeStarted=A->Montage_Play(Charge,1.f)>0;return bChargeStarted;
}
void AAshWellMountedSampleRig::StopCharge(){bChargeStarted=false;if(auto* A=RiderAnimation()){A->Montage_Stop(.15f,Charge);A->ClearActionState();}}
float AAshWellMountedSampleRig::GetChargeTime() const {return ChargeElapsed;}
bool AAshWellMountedSampleRig::IsChargePlaying() const {auto* A=RiderAnimation();return A&&Charge&&A->Montage_IsPlaying(Charge);}
bool AAshWellMountedSampleRig::HasWeaponWindow() const {auto* A=RiderAnimation();return A&&A->bWeaponWindow;}
FVector AAshWellMountedSampleRig::GetGrip() const{return Poleaxe->GetComponentLocation();}
FVector AAshWellMountedSampleRig::GetTip() const{return Poleaxe->GetComponentTransform().TransformPosition(FVector(0,-171.5f,0));}
void AAshWellMountedSampleRig::EndPlay(const EEndPlayReason::Type Reason){StopCharge();Super::EndPlay(Reason);}
