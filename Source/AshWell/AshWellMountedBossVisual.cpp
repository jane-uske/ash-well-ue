#include "AshWellMountedBoss.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "WardenHQRestPose.inl"
#include "Misc/PackageName.h"
#include "MountedGallopDistance.inl"

namespace
{
const FName RiderNames[]={TEXT("Body"),TEXT("RightUpperArm"),TEXT("RightForearm"),TEXT("LeftUpperArm"),TEXT("LeftForearm"),TEXT("RightThigh"),TEXT("RightShin"),TEXT("RightFoot"),TEXT("LeftThigh"),TEXT("LeftShin"),TEXT("LeftFoot")};

FTransform MapLink(const FVector& RA,const FVector& RB,const FVector& A,const FVector& B)
{
    const FQuat Q=FQuat::FindBetweenNormals((RB-RA).GetSafeNormal(),(B-A).GetSafeNormal());
    return FTransform(Q,A-Q.RotateVector(RA),FVector::OneVector);
}

void Limb(const FVector& RestA,const FVector& RestB,const FVector& RestC,const FVector& A,const FVector& DesiredC,const FVector& BendHint,FVector& B,FVector& C)
{
    const float Upper=FVector::Distance(RestA,RestB),Lower=FVector::Distance(RestB,RestC);
    const FVector Direction=(DesiredC-A).GetSafeNormal();
    const float Distance=FMath::Clamp(float(FVector::Distance(A,DesiredC)),FMath::Abs(Upper-Lower)+.1f,Upper+Lower-.1f);
    C=A+Direction*Distance;
    FVector Bend=(BendHint-Direction*FVector::DotProduct(BendHint,Direction)).GetSafeNormal();
    if(Bend.IsNearlyZero())Bend=FVector::RightVector;
    const float Along=(Upper*Upper-Lower*Lower+Distance*Distance)/(2*Distance);
    B=A+Direction*Along+Bend*FMath::Sqrt(FMath::Max(0.f,Upper*Upper-Along*Along));
}
}

void AAshWellMountedBoss::InitializeVisuals()
{
    auto* Dark=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Materials/M_DarkSteel.M_DarkSteel"));
    auto* Rust=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Materials/V2/M_Rust.M_Rust"));
    auto Static=[&](const TCHAR* Name,UStaticMesh* Mesh,USceneComponent* Parent,UMaterialInterface* Mat)
    {
        auto* P=NewObject<UStaticMeshComponent>(this,Name);AddInstanceComponent(P);P->SetupAttachment(Parent);
        P->SetStaticMesh(Mesh);if(Mat)P->SetMaterial(0,Mat);P->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        P->SetGenerateOverlapEvents(false);P->SetCanEverAffectNavigation(false);P->RegisterComponent();return P;
    };
    auto HorseClip=[](const TCHAR* Name){const FString N=FString(TEXT("A_Horse_"))+Name;return LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/MountedBoss/"))+N+TEXT(".")+N));};
    HorseIdle=HorseClip(TEXT("Idle"));HorseWalk=HorseClip(TEXT("Walk"));HorseRun=HorseClip(TEXT("Gallop"));
    HorseRear=nullptr; // The inspected CC0 pack has no rear clip; this attack is explicitly procedural.
    HorseDeath=HorseClip(TEXT("Death"));HorseJump=HorseClip(TEXT("Jump"));
    if(auto* Skin=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/MountedBoss/SK_Horse.SK_Horse")))
    {
        HorseMesh=NewObject<USkeletalMeshComponent>(this,TEXT("MountedHorse"));AddInstanceComponent(HorseMesh);HorseMesh->SetupAttachment(SceneRoot);
        HorseMesh->SetSkeletalMesh(Skin);HorseMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        HorseMesh->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        HorseMesh->RegisterComponent();HorseMesh->RefreshBoneTransforms();bHorseVisual=HorseIdle&&HorseWalk&&HorseRun;
        bHorseSeatBone=HorseMesh->GetBoneIndex(TEXT("Torso2"))!=INDEX_NONE;
        if(bHorseSeatBone)HorseSeatRestBone=HorseMesh->GetSocketTransform(TEXT("Torso2"),RTS_Component);
    }
    else
    {
        // This visible fallback is only for collision/debugging; telemetry never calls it an imported horse.
        auto* Sphere=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere"));
        auto* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
        struct FPart{FVector P,S;};const FPart Forms[]={{{0,0,127},{1.9,.66,.88}},{{82,0,171},{.57,.43,1.13}},{{106,0,209},{.78,.40,.45}},{{69,30,64},{.18,.18,1.12}},{{69,-30,64},{.18,.18,1.12}},{{-79,30,64},{.21,.21,1.12}},{{-79,-30,64},{.21,.21,1.12}}};
        for(int32 I=0;I<7;++I){auto* P=Static(*FString::Printf(TEXT("HorsePlaceholder%d"),I),I<3?Sphere:Cube,SceneRoot,Dark);P->SetRelativeLocation(Forms[I].P);P->SetRelativeScale3D(Forms[I].S);FallbackHorse.Add(P);}
    }
    RiderRoot=NewObject<USceneComponent>(this,TEXT("MountedRiderSaddleFrame"));AddInstanceComponent(RiderRoot);RiderRoot->SetupAttachment(SceneRoot);RiderRoot->SetRelativeLocation(FVector(0,0,103.6f));RiderRoot->SetRelativeScale3D(FVector(.68f));RiderRoot->RegisterComponent();
    auto* RiderMat=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/WardenHQ/M_WardenHQ.M_WardenHQ"));
    auto* Inner=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/WardenHQ/M_WardenHQ_Inner.M_WardenHQ_Inner"));
    const TCHAR* RiderPath=FPackageName::DoesPackageExist(TEXT("/Game/AshWell/Combat/MountedBoss/SK_MountedRider"))?TEXT("/Game/AshWell/Combat/MountedBoss/SK_MountedRider.SK_MountedRider"):TEXT("/Game/AshWell/Combat/WardenRig/SK_WardenRig.SK_WardenRig");
    if(auto* Skin=LoadObject<USkeletalMesh>(nullptr,RiderPath))
    {
        RiderMesh=NewObject<UPoseableMeshComponent>(this,TEXT("MountedRiderSkin"));AddInstanceComponent(RiderMesh);RiderMesh->SetupAttachment(RiderRoot);
        RiderMesh->SetSkinnedAssetAndUpdate(Skin);RiderMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        RiderMesh->SetMaterial(0,RiderMat);RiderMesh->SetMaterial(1,Inner);RiderMesh->SetBoundsScale(2.8f);RiderMesh->RegisterComponent();
        bRiderVisual=true;
        for(const FName& Name:RiderNames){bRiderVisual&=RiderMesh->GetBoneIndex(Name)!=INDEX_NONE;RiderRestTransforms.Add(RiderMesh->GetBoneTransformByName(Name,EBoneSpaces::ComponentSpace));}
        if(!bRiderVisual){RiderMesh->DestroyComponent();RiderMesh=nullptr;RiderRestTransforms.Reset();}
    }
    if(!bRiderVisual)
    {
        for(const FName& Name:RiderNames)
        {
            const FString N=TEXT("SM_WardenHQ_")+Name.ToString();
            auto* M=LoadObject<UStaticMesh>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/WardenHQ/"))+N+TEXT(".")+N));
            const FString ComponentName=FString(TEXT("MountedRigid_"))+Name.ToString();
            RiderParts.Add(Static(*ComponentName,M,RiderRoot,RiderMat));
        }
    }
    auto* Pole=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/MountedBoss/SM_MountedHalberd.SM_MountedHalberd"));
    Weapon=Static(TEXT("MountedHalberd"),Pole?Pole:LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")),SceneRoot,Pole?nullptr:Dark);
    if(!Pole)Weapon->SetRelativeScale3D(FVector(2.8f,.045f,.045f));
    auto* Seat=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/MountedBoss/SM_MountedSaddle.SM_MountedSaddle"));
    Saddle=Static(TEXT("MountedSaddle"),Seat?Seat:LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")),SceneRoot,Seat?nullptr:Rust);
    Saddle->SetRelativeLocation(FVector(0,0,170));
    // The reused rider has short armoured legs. Lift the stirrup bars to the
    // solved boot soles while keeping the saddle seat at its existing origin.
    Saddle->SetRelativeScale3D(Seat?FVector(1.f,1.f,.925f):FVector(.63f,.72f,.16f));
    Shield=Static(TEXT("MountedShield"),LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder")),SceneRoot,Dark);
    Shield->SetRelativeScale3D(FVector(1.3f,1.8f,.095f));
    UE_LOG(LogTemp,Display,TEXT("AW_MOUNTED_VISUAL horse=%d rider=%d rear_clip=%d"),bHorseVisual,bRiderVisual,HorseRear!=nullptr);
}

void AAshWellMountedBoss::UpdateHorseAnimation(float Dt)
{
    if(!HorseMesh)return;
    const float Travel=DistanceTravelled-LastAnimationDistance;LastAnimationDistance=DistanceTravelled;
    const float Turn=TurnTravel-LastAnimationTurnTravel;LastAnimationTurnTravel=TurnTravel;
    const bool RearPose=AttackKind==EMountedBossAttack::Rear&&(State==EMountedBossState::Windup||State==EMountedBossState::Active||State==EMountedBossState::Recovery);
    const bool LeapPose=AttackKind==EMountedBossAttack::LeapShield&&(State==EMountedBossState::Windup||State==EMountedBossState::Active||State==EMountedBossState::Recovery);
    UAnimSequence* Wanted=IsDead()&&HorseDeath?HorseDeath.Get():LeapPose&&HorseJump?HorseJump.Get():RearPose&&HorseRear?HorseRear.Get():ActualSpeed>260.f&&HorseRun?HorseRun.Get():(ActualSpeed>12.f||TurnSpeed>10.f)&&HorseWalk?HorseWalk.Get():HorseIdle.Get();
    if(!Wanted)return;
    const bool Changed=CurrentHorseAnimation!=Wanted;
    if(Changed)
    {
        const float Phase=CurrentHorseAnimation&&CurrentHorseAnimation->GetPlayLength()>0?HorseAnimationTime/CurrentHorseAnimation->GetPlayLength():0;
        CurrentHorseAnimation=Wanted;HorseAnimationTime=(Wanted==HorseWalk||Wanted==HorseRun)?FMath::Fmod(Phase,1.f)*Wanted->GetPlayLength():0.f;
        HorseMesh->PlayAnimation(Wanted,false);if(auto* Instance=HorseMesh->GetSingleNodeInstance())Instance->SetPlaying(false);
    }
    if(IsDead())HorseAnimationTime=FMath::Min(StateTime,Wanted->GetPlayLength()-.001f);
    else if(LeapPose&&HorseJump)
    {
        HorseAnimationTime=State==EMountedBossState::Windup?FMath::Lerp(.1f,.35f,GetAttackProgress()):State==EMountedBossState::Active?FMath::Lerp(.35f,1.35f,FMath::Clamp(StateTime/.68f,0.f,1.f)):FMath::Lerp(1.35f,Wanted->GetPlayLength()-.001f,FMath::Clamp(StateTime/.5f,0.f,1.f));
    }
    else if(RearPose&&HorseRear)
    {
        // The asset adapter provides a bounded rear segment; its peak and landing follow gameplay phases.
        const float P=State==EMountedBossState::Windup?.60f*GetAttackProgress():State==EMountedBossState::Active?FMath::Lerp(.60f,.85f,GetAttackProgress()):FMath::Lerp(.85f,1.f,FMath::Clamp(StateTime/.70f,0.f,1.f));
        HorseAnimationTime=P*(Wanted->GetPlayLength()-.001f);
    }
    else
    {
        // Phase follows measured ground travel; blocked movement does not keep galloping in place.
        const float RefSpeed=Wanted==HorseRun?477.34f:Wanted==HorseWalk?114.13f:1.f;
        if(Wanted==HorseRun)
        {
            const float* S=MountedGallopDistance::Samples;
            const float Sample=FMath::Clamp(HorseAnimationTime*60.f,0.f,35.9999f);const int I=int(Sample);
            float Distance=FMath::Fmod(FMath::Lerp(S[I],S[I+1],Sample-I)+FMath::Max(Travel,Turn),S[36]);
            int J=0;while(J<35&&Distance>S[J+1])++J;
            HorseAnimationTime=(J+(Distance-S[J])/(S[J+1]-S[J]))/60.f;
        }
        else HorseAnimationTime=FMath::Fmod(HorseAnimationTime+((Wanted==HorseWalk||Wanted==HorseRun)?FMath::Max(Travel,Turn)/RefSpeed:Dt),Wanted->GetPlayLength());
    }
    HorseMesh->SetPosition(HorseAnimationTime,false);
    HorseMesh->TickAnimation(0.f,false);HorseMesh->RefreshBoneTransforms();
    static const FName HoofBones[]={TEXT("FF_L"),TEXT("FF_R"),TEXT("FFB_L"),TEXT("FFB_R")};
    bHoofBonesValid=true;
    for(int I=0;I<4;++I)
    {
        if(HorseMesh->GetBoneIndex(HoofBones[I])==INDEX_NONE){bHoofBonesValid=false;continue;}
        const FVector P=HorseMesh->GetSocketLocation(HoofBones[I]);
        const float Height=P.Z-Home.Z;
        const bool Ground=Height<(bHoofGrounded[I]?12.f:9.5f);
        if(bHoofPrimed&&!Changed&&!IsDead()&&!LeapPose&&(ActualSpeed>25.f||TurnSpeed>10.f)&&Ground&&!bHoofGrounded[I])
        {++HoofContacts;PlaySound(HoofSound,P,.055f,I<2?1.18f:1.02f);}
        if(bHoofPrimed&&!Changed&&Ground&&bHoofGrounded[I]&&ActualSpeed>30.f&&TurnSpeed<10.f&&!RearPose&&!LeapPose&&Dt>0)
        {SupportDriftDistance+=FVector::Dist2D(P,PreviousHoof[I]);SupportSampleTime+=Dt;}
        bHoofGrounded[I]=Ground;PreviousHoof[I]=P;
    }
    bHoofPrimed=true;
}

void AAshWellMountedBoss::UpdatePose(float Dt)
{
    const float Moving=FMath::Clamp(ActualSpeed/220.f,0.f,1.f);
    RiderBob=FMath::Sin(GaitPhase*4*PI)*1.7f*Moving;
    HorsePitch=0;
    const bool LeapPose=AttackKind==EMountedBossAttack::LeapShield&&(State==EMountedBossState::Windup||State==EMountedBossState::Active||State==EMountedBossState::Recovery);
    if(AttackKind==EMountedBossAttack::Rear&&(State==EMountedBossState::Windup||State==EMountedBossState::Active))
        HorsePitch=State==EMountedBossState::Windup?24.f*FMath::SmoothStep(.15f,.8f,GetAttackProgress()):24.f*(1-FMath::SmoothStep(0.f,.12f,StateTime));
    const FQuat RearRotation=FRotator(HorsePitch,0,0).Quaternion();const FVector RearPivot(-79,0,0);
    const FVector RearOffset=RearPivot-RearRotation.RotateVector(RearPivot);
    if(!HorseRear&&HorseMesh)
    {
        // Strip the jump clip's common torso lift: the combat actor owns all root travel.
        float ClipLift=0;
        if(LeapPose&&bHorseSeatBone)ClipLift=FMath::Max(0.f,float(HorseMesh->GetSocketTransform(TEXT("Torso2"),RTS_Component).GetLocation().Z-HorseSeatRestBone.GetLocation().Z));
        HorseMesh->SetRelativeRotation(RearRotation);HorseMesh->SetRelativeLocation(RearOffset-FVector(0,0,ClipLift));
    }
    if(!FallbackHorse.IsEmpty())
    {
        for(int32 I=3;I<7;++I)
        {
            const float Phase=GaitPhase*2*PI+((I==3||I==6)?0:PI);
            FallbackHorse[I]->SetRelativeRotation(FRotator(FMath::Sin(Phase)*24.f*Moving,0,0));
        }
    }
    FVector Seat=RearRotation.RotateVector(FVector(0,0,175+RiderBob))+RearOffset;FQuat SeatRotation=RearRotation;
    if(HorseMesh&&bHorseSeatBone)
    {
        const FTransform Bone=HorseMesh->GetSocketTransform(TEXT("Torso2"),RTS_Component);
        const FQuat DeltaRotation=Bone.GetRotation()*HorseSeatRestBone.GetRotation().Inverse();
        const FVector AnimatedSeat=Bone.GetLocation()+DeltaRotation.RotateVector(FVector(0,0,175)-HorseSeatRestBone.GetLocation());
        Seat=HorseMesh->GetRelativeTransform().TransformPosition(AnimatedSeat);
        SeatRotation=HorseMesh->GetRelativeRotation().Quaternion()*DeltaRotation;
    }
    if(RiderRoot){RiderRoot->SetRelativeLocation(Seat+SeatRotation.RotateVector(FVector(0,0,-71.4f)));RiderRoot->SetRelativeRotation(SeatRotation);}
    if(Saddle){Saddle->SetRelativeLocation(Seat);Saddle->SetRelativeRotation(SeatRotation);}
    UpdateRiderPose(Dt);
}

void AAshWellMountedBoss::UpdateRiderPose(float Dt)
{
    if(!RiderRoot)return;
    using namespace WardenHQRest;
    FVector Grip(42,61,228),Direction(.35f,.20f,-.92f),ShieldTarget(40,-76,220);
    float Lean=8.f+HitReaction*5.f,Twist=0,SideLean=0;
    const bool AttackPose=State==EMountedBossState::Windup||State==EMountedBossState::Active||State==EMountedBossState::Recovery;
    if(AttackPose)
    {
        const float A=GetAttackProgress();
        const float Recover=State==EMountedBossState::Recovery?1-FMath::SmoothStep(.20f,Spec().Recovery,StateTime):1.f;
        FVector PoseGrip=Grip,PoseDirection=Direction;
        if(AttackKind==EMountedBossAttack::Sweep)
        {
            const float Swing=State==EMountedBossState::Windup?FMath::Lerp(40.f,108.f,FMath::SmoothStep(0.f,.8f,A)):State==EMountedBossState::Active?FMath::Lerp(108.f,-58.f,A):-58.f;
            PoseGrip=State==EMountedBossState::Windup?FMath::Lerp(Grip,FVector(0,66,258),FMath::SmoothStep(0.f,.8f,A)):FVector(45,48,224);
            PoseDirection=FVector(FMath::Cos(FMath::DegreesToRadians(Swing)),FMath::Sin(FMath::DegreesToRadians(Swing)),State==EMountedBossState::Windup?-.10f:-.52f);
            Twist=(State==EMountedBossState::Windup?22.f:State==EMountedBossState::Active?FMath::Lerp(22.f,-22.f,A):-22.f)*Recover;
        }
        else if(AttackKind==EMountedBossAttack::Overhead)
        {
            const FVector Raised(-.32f,0,.95f),Down(.85f,-.16f,-.65f);
            if(State==EMountedBossState::Windup){const float P=FMath::SmoothStep(0.f,.75f,A);PoseGrip=FMath::Lerp(Grip,FVector(2,60,274),P);PoseDirection=FMath::Lerp(Direction,Raised,P);Lean=FMath::Lerp(8.f,-13.f,P);}
            else{const float P=State==EMountedBossState::Active?FMath::SmoothStep(0.f,.78f,A):1.f;PoseGrip=FMath::Lerp(FVector(2,60,274),FVector(62,46,212),P);PoseDirection=FMath::Lerp(Raised,Down,P);Lean=FMath::Lerp(-13.f,22.f,P)*Recover;}
        }
        else if(AttackKind==EMountedBossAttack::Charge)
        {
            const float P=State==EMountedBossState::Windup?FMath::SmoothStep(0.f,.75f,A):1.f;
            PoseGrip=FMath::Lerp(Grip,FVector(50,65,224),P);
            const float Sweep=State==EMountedBossState::Windup?65.f:State==EMountedBossState::Active?FMath::Lerp(65.f,-45.f,FMath::SmoothStep(.42f,1.05f,A)):-45.f;
            PoseDirection=FMath::Lerp(Direction,FVector(FMath::Cos(FMath::DegreesToRadians(Sweep)),FMath::Sin(FMath::DegreesToRadians(Sweep)),-.50f),P);
            Lean=20.f*P*Recover;Twist=FMath::Lerp(22.f,-18.f,State==EMountedBossState::Active?A:0.f)*Recover;
        }
        else if(AttackKind==EMountedBossAttack::BodyCheck)
        {
            const float P=State==EMountedBossState::Windup?FMath::SmoothStep(0.f,.75f,A):1.f;
            ShieldTarget=FMath::Lerp(ShieldTarget,State==EMountedBossState::Windup?FVector(8,-71,237):FVector(107,-83,162),P*Recover);
            PoseGrip=FVector(25,65,243);PoseDirection=FVector(-.15f,.30f,.94f);Lean=State==EMountedBossState::Active?25.f:7.f;
        }
        else if(AttackKind==EMountedBossAttack::LeapShield)
        {
            const float P=State==EMountedBossState::Windup?FMath::SmoothStep(0.f,.85f,A):1.f;
            const float Drop=State==EMountedBossState::Active?FMath::SmoothStep(.25f,.64f,StateTime):State==EMountedBossState::Recovery?1.f:0.f;
            ShieldTarget=FMath::Lerp(ShieldTarget,FMath::Lerp(FVector(20,-78,260),FVector(38,-78,153),Drop),P*Recover);
            PoseGrip=FVector(0,65,270);PoseDirection=FVector(-.4f,.15f,.95f);Lean=FMath::Lerp(-12.f,-40.f,Drop)*Recover;SideLean=-35.f*Drop*Recover;
        }
        else
        {PoseGrip=FVector(5,64,255);PoseDirection=FVector(-.25f,.1f,.96f);Lean=-5.f;}
        Grip=FMath::Lerp(Grip,PoseGrip,Recover);Direction=FMath::Lerp(Direction,PoseDirection,Recover);
    }
    if(IsDead())
    {
        const float A=FMath::SmoothStep(0.f,1.2f,StateTime);
        RiderRoot->SetRelativeLocation(FVector(-35*A,90*A,103.6f-74*A));RiderRoot->SetRelativeRotation(FRotator(12*A,0,75*A));Lean=24;
    }
    const FVector Waist(0,0,105);
    const FQuat TorsoRotation=FRotator(Lean,Twist,SideLean).Quaternion();
    const FTransform Torso(TorsoRotation,Waist-TorsoRotation.RotateVector(Waist),FVector::OneVector);
    FTransform Poses[11];Poses[0]=Torso;
    const FTransform Frame=RiderRoot->GetComponentTransform();
    // All weapon placement is derived from the same solved hand used by the visible rider.
    const FVector DesiredGrip=Frame.InverseTransformPosition(GetActorTransform().TransformPosition(Grip));
    FVector Elbow,Hand;Limb(RShoulder,RElbow,RHand,Torso.TransformPosition(RShoulder),DesiredGrip,FVector(-1,1,0),Elbow,Hand);
    Poses[1]=MapLink(RShoulder,RElbow,Torso.TransformPosition(RShoulder),Elbow);Poses[2]=MapLink(RElbow,RHand,Elbow,Hand);
    WeaponGrip=Frame.TransformPosition(Hand);
    const FVector WorldDirection=GetActorQuat().RotateVector(Direction.GetSafeNormal());WeaponTip=WeaponGrip+WorldDirection*195.f;
    if(Weapon)Weapon->SetWorldLocationAndRotation(WeaponGrip,FRotationMatrix::MakeFromX(WorldDirection).ToQuat());
    const FVector DesiredShield=Frame.InverseTransformPosition(GetActorTransform().TransformPosition(ShieldTarget));
    FVector LJoint,LGrip;Limb(LShoulder,LElbow,LHand,Torso.TransformPosition(LShoulder),DesiredShield,FVector(-1,-1,0),LJoint,LGrip);
    Poses[3]=MapLink(LShoulder,LElbow,Torso.TransformPosition(LShoulder),LJoint);Poses[4]=MapLink(LElbow,LHand,LJoint,LGrip);
    const bool LeapShield=AttackKind==EMountedBossAttack::LeapShield&&AttackPose;
    ShieldPoint=Frame.TransformPosition(LGrip)+GetActorQuat().RotateVector(FVector(12,-15,-55.f));

    if(Shield)Shield->SetWorldLocationAndRotation(ShieldPoint,GetActorQuat()*FRotator(0,0,90).Quaternion());
    FVector Knee,Ankle;
    // Targets stay inside the approximately 91 cm two-bone reach, producing
    // bent knees. The old 135 cm targets saturated the solver into straight legs.
    Limb(RHip,RKnee,RAnkle,RHip,FVector(20,63,38),FVector(1,.25,0),Knee,Ankle);
    Poses[5]=MapLink(RHip,RKnee,RHip,Knee);Poses[6]=MapLink(RKnee,RAnkle,Knee,Ankle);Poses[7]=FTransform(FQuat::Identity,Ankle-RAnkle,FVector::OneVector);
    Limb(LHip,LKnee,LAnkle,LHip,FVector(20,-63,38),FVector(1,-.25,0),Knee,Ankle);
    Poses[8]=MapLink(LHip,LKnee,LHip,Knee);Poses[9]=MapLink(LKnee,LAnkle,Knee,Ankle);Poses[10]=FTransform(FQuat::Identity,Ankle-LAnkle,FVector::OneVector);
    for(int32 I=0;I<11;++I)
    {
        if(RiderMesh&&RiderRestTransforms.IsValidIndex(I))RiderMesh->SetBoneTransformByName(RiderNames[I],RiderRestTransforms[I]*Poses[I],EBoneSpaces::ComponentSpace);
        else if(RiderParts.IsValidIndex(I)&&RiderParts[I])RiderParts[I]->SetRelativeTransform(Poses[I]);
    }
}
