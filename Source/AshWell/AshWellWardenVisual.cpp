#include "AshWellWarden.h"
#include "BattleMotionSamples.inl"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"

// All exported meshes use a shared, feet-centred origin and centimetre vertices.
// The manifest-generated rest landmarks are independent of the gameplay capsule.
#include "WardenHQRestPose.inl"

namespace
{
void RigidLink(UStaticMeshComponent* Part, const FVector& RestA, const FVector& RestB,
    const FVector& A, const FVector& B)
{
    const FQuat Rotation = FQuat::FindBetweenNormals((RestB-RestA).GetSafeNormal(),(B-A).GetSafeNormal());
    Part->SetRelativeTransform(FTransform(Rotation,A-Rotation.RotateVector(RestA),FVector::OneVector));
}

// Solve two rigid segments instead of stretching the generated armour or pulling
// cut seams apart. The rest bend is transported with the shoulder-to-hand vector.
void SolveLimb(const FVector& RestRoot, const FVector& RestJoint, const FVector& RestEnd,
    const FVector& Root, FVector DesiredEnd, FVector& Joint, FVector& End)
{
    const float Upper = FVector::Distance(RestRoot,RestJoint);
    const float Lower = FVector::Distance(RestJoint,RestEnd);
    const FVector RestDirection=(RestEnd-RestRoot).GetSafeNormal();
    const FVector Direction=(DesiredEnd-Root).GetSafeNormal();
    const float Distance=FMath::Clamp(float(FVector::Distance(Root,DesiredEnd)),FMath::Abs(Upper-Lower)+0.01f,Upper+Lower-0.01f);
    End=Root+Direction*Distance;
    FVector Bend=(RestJoint-RestRoot)-RestDirection*FVector::DotProduct(RestJoint-RestRoot,RestDirection);
    if(Bend.IsNearlyZero())Bend=FVector(-1,0,0);
    Bend=FQuat::FindBetweenNormals(RestDirection,Direction).RotateVector(Bend.GetSafeNormal());
    const float Along=(Upper*Upper-Lower*Lower+Distance*Distance)/(2*Distance);
    const float Height=FMath::Sqrt(FMath::Max(0.f,Upper*Upper-Along*Along));
    Joint=Root+Direction*Along+Bend*Height;
}
}

void AAshWellWarden::InitializeGeneratedVisual()
{
    if(FParse::Param(FCommandLine::Get(),TEXT("WardenPrimitive")))return;
    const TCHAR* Names[]={TEXT("Body"),TEXT("RightUpperArm"),TEXT("RightForearm"),
        TEXT("LeftUpperArm"),TEXT("LeftForearm"),TEXT("RightThigh"),TEXT("RightShin"),
        TEXT("RightFoot"),TEXT("LeftThigh"),TEXT("LeftShin"),TEXT("LeftFoot"),TEXT("Hammer")};
    TArray<UStaticMesh*> Meshes;
    for(const TCHAR* Name:Names)
    {
        const FString Asset=FString(TEXT("SM_WardenHQ_"))+Name;
        UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/WardenHQ/"))+Asset+TEXT(".")+Asset));
        if(!Mesh)
        {
            UE_LOG(LogTemp,Warning,TEXT("Warden generated visual incomplete: %s. Using prototype visual."),Name);
            return;
        }
        Meshes.Add(Mesh);
    }
    UMaterialInterface* Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/WardenHQ/M_WardenHQ.M_WardenHQ"));
    if(!Material)return;
    for(int32 Index=0;Index<Meshes.Num();++Index)
    {
        auto* Part=NewObject<UStaticMeshComponent>(this,FName(*FString::Printf(TEXT("Generated_%s"),Names[Index])));
        AddInstanceComponent(Part);
        Part->SetupAttachment(Body);
        Part->SetMobility(EComponentMobility::Movable);
        Part->SetStaticMesh(Meshes[Index]);
        Part->SetMaterial(0,Material); // Preserve dark interior cap material in slot 1.
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCanEverAffectNavigation(false);
        Part->RegisterComponent();
        GeneratedParts.Add(Part);
    }
    // Preserve invisible pose drivers plus the existing warning, sparks and lights.
    for(UStaticMeshComponent* Part:Parts)
        if(Part!=WarningRing&&!Sparks.Contains(Part))Part->SetVisibility(false,false);
    bGeneratedVisual=true;
    if(!FParse::Param(FCommandLine::Get(),TEXT("WardenRigid")))
    {
        if(auto* Skin=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/WardenRig/SK_WardenRig.SK_WardenRig")))
        {
            SkinnedVisual=NewObject<UPoseableMeshComponent>(this,TEXT("WardenSkin"));
            AddInstanceComponent(SkinnedVisual);SkinnedVisual->SetupAttachment(Body);
            SkinnedVisual->SetSkinnedAssetAndUpdate(Skin);SkinnedVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            SkinnedVisual->SetMaterial(0,Material);
            SkinnedVisual->SetMaterial(1,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/WardenHQ/M_WardenHQ_Inner.M_WardenHQ_Inner")));
            SkinnedVisual->SetBoundsScale(2.8f);SkinnedVisual->RegisterComponent();
            bool Valid=true;
            for(int32 I=0;I<11;++I)
            {
                Valid&=SkinnedVisual->GetBoneIndex(Names[I])!=INDEX_NONE;
                SkinRestTransforms.Add(SkinnedVisual->GetBoneTransformByName(Names[I],EBoneSpaces::ComponentSpace));
            }
            if(Valid){for(int32 I=0;I<11;++I)GeneratedParts[I]->SetVisibility(false);}
            else{SkinnedVisual->DestroyComponent();SkinnedVisual=nullptr;SkinRestTransforms.Reset();}
        }
    }
    EyeLight->SetRelativeLocation(FVector(35,0,246));
    UE_LOG(LogTemp,Display,TEXT("ASHWELL_WARDEN_VISUAL generated_pbr loaded parts=%d; capsule and combat unchanged"),GeneratedParts.Num());
}

void AAshWellWarden::UpdateGeneratedVisual(const FVector& LegacyHand, const FVector& LegacyHead,
    float Gait, float LeftLift, float RightLift)
{
    if(!bGeneratedVisual)return;
    using namespace WardenHQRest;
    // The old primitive calls its negative-Y limb right. Preserve the approved
    // asset's anatomical handedness while keeping the attack's X/Z trajectory.
    const FVector Hand(LegacyHand.X,-LegacyHand.Y,LegacyHand.Z);
    const FVector Head(LegacyHead.X,-LegacyHead.Y,LegacyHead.Z);
    float ForwardLean=4.f;
    if(State==EWellWardenState::Windup)
    {
        float A=FMath::Clamp(StateTime/(WindupDuration()-.20f),0.f,1.f);A=A*A*(3-2*A);
        ForwardLean=FMath::Lerp(4.f,bBattlePolish?-14.f:-5.f,A);
    }
    else if(State==EWellWardenState::Strike)
    {
        const float A=FMath::Clamp(StateTime/(StrikeDuration()*.8f),0.f,1.f);
        ForwardLean=FMath::Lerp(bBattlePolish?-14.f:-5.f,48.f,A*A);
    }
    else if(State==EWellWardenState::Recovery)
    {
        const float A=FMath::Clamp((StateTime-.42f)/(RecoveryDuration()-.42f),0.f,1.f);
        ForwardLean=FMath::Lerp(48.f,4.f,A);
    }
    float Compression=0.f;
    if(State==EWellWardenState::Windup)Compression=6.f*FMath::SmoothStep(.05f,WindupDuration()-.25f,StateTime);
    else if(State==EWellWardenState::Strike)Compression=FMath::Lerp(6.f,12.f,FMath::Clamp(StateTime/StrikeDuration(),0.f,1.f));
    else if(State==EWellWardenState::Recovery)Compression=12.f*(1-FMath::SmoothStep(.35f,RecoveryDuration(),StateTime));
    if(State==EWellWardenState::Overload)
    {
        const float Load=FMath::SmoothStep(0.f,.35f,StateTime)*(1-FMath::SmoothStep(1.2f,2.f,StateTime));
        ForwardLean=4.f+18.f*Load+FMath::Sin(StateTime*21.f)*3.f*Load;
        Compression=10.f*Load;
    }
    float KickForward=0,KickLift=0;
    if(bBattlePolish&&AttackKind==EWellWardenAttack::Kick)
    {
        const float F=MotionAlpha()*70;const int I=FMath::Clamp(FMath::FloorToInt(F),0,69);const float A=F-I;
        KickForward=FMath::Lerp(BattleMotion::Kick[I].Forward,BattleMotion::Kick[I+1].Forward,A)*.72f;
        KickLift=FMath::Max(0.f,FMath::Lerp(BattleMotion::Kick[I].Lift,BattleMotion::Kick[I+1].Lift,A))*.72f;
        ForwardLean=4+FMath::Lerp(BattleMotion::Kick[I].Pitch-23.24f,BattleMotion::Kick[I+1].Pitch-23.24f,A)*.32f;
        Compression=0;
    }
    if(AttackKind==EWellWardenAttack::Charge)
    {ForwardLean=(IsAttacking()?22.f:4.f);Compression=IsAttacking()?9:0;}
    const FVector Waist(0,0,105);
    float Twist=0;
    if(AttackKind==EWellWardenAttack::Sweep&&State!=EWellWardenState::Overload)
    {
        ForwardLean=8;
        if(State==EWellWardenState::Windup)Twist=-20*FMath::SmoothStep(0.f,.70f,StateTime);
        else if(State==EWellWardenState::Strike)Twist=FMath::Lerp(-20.f,32.f,FMath::Clamp(StateTime/.35f,0.f,1.f));
        else if(State==EWellWardenState::Recovery)Twist=32*(1-FMath::SmoothStep(.30f,RecoveryDuration(),StateTime));
    }
    const FQuat TorsoRotation=FQuat(FVector(0,0,1),FMath::DegreesToRadians(Twist))*FQuat(FVector(0,1,0),FMath::DegreesToRadians(ForwardLean));
    const FTransform TorsoPose(TorsoRotation,Waist-TorsoRotation.RotateVector(Waist)-FVector(0,0,Compression),FVector::OneVector);
    GeneratedParts[0]->SetRelativeTransform(TorsoPose);
    const FVector Shoulder=TorsoPose.TransformPosition(RShoulder);
    FVector WeaponDirection=(Hand-Head).GetSafeNormal();
    const float WeaponLength=FVector::Distance(RHand,HammerHeadPoint);
    // The primitive shaft used to change length during its swing. Keep this
    // actual hammer rigid: adjust shaft orientation within the arm's reachable
    // cone, so the visible hammer head still follows the original hit trajectory.
    const FVector Axis=(Shoulder-Head).GetSafeNormal();
    const float Distance=FVector::Distance(Shoulder,Head);
    const float Reach=FVector::Distance(RShoulder,RElbow)+FVector::Distance(RElbow,RHand)-.5f;
    if(Distance>KINDA_SMALL_NUMBER)
    {
        const float Limit=FMath::Clamp((Distance*Distance+WeaponLength*WeaponLength-Reach*Reach)/(2*Distance*WeaponLength),-1.f,1.f);
        const float Cosine=FVector::DotProduct(WeaponDirection,Axis);
        if(Cosine<Limit)
        {
            FVector Tangent=(WeaponDirection-Axis*Cosine).GetSafeNormal();
            if(Tangent.IsNearlyZero())Tangent=FVector::CrossProduct(Axis,FVector(0,1,0)).GetSafeNormal();
            WeaponDirection=Axis*Limit+Tangent*FMath::Sqrt(FMath::Max(0.f,1-Limit*Limit));
        }
    }
    const FVector DesiredGrip=Head+WeaponDirection*WeaponLength;
    FVector Elbow,Grip;
    SolveLimb(RShoulder,RElbow,RHand,Shoulder,DesiredGrip,Elbow,Grip);
    RigidLink(GeneratedParts[1],RShoulder,RElbow,Shoulder,Elbow);
    RigidLink(GeneratedParts[2],RElbow,RHand,Elbow,Grip);
    const FQuat HammerRotation=FQuat::FindBetweenNormals((RHand-HammerHeadPoint).GetSafeNormal(),WeaponDirection);
    GeneratedParts[11]->SetRelativeTransform(FTransform(HammerRotation,Grip-HammerRotation.RotateVector(RHand),FVector::OneVector));
    const FVector VisibleHead=Grip+HammerRotation.RotateVector(HammerHeadPoint-RHand);
    GeneratedHammerError=FVector::Distance(VisibleHead,Head);
    WarningRing->SetRelativeLocation(VisibleHead+FVector(0,0,22));
    EyeLight->SetRelativeLocation(TorsoPose.TransformPosition(FVector(35,0,246)));

    FVector OtherElbow,OtherHand;
    const FVector OtherShoulder=TorsoPose.TransformPosition(LShoulder);
    SolveLimb(LShoulder,LElbow,LHand,OtherShoulder,TorsoPose.TransformPosition(LHand)+FVector(Gait*13,0,0)+(State==EWellWardenState::Overload?FVector(20,-22,35)*FMath::Sin(PI*FMath::Clamp(StateTime/2.f,0.f,1.f)):FVector::ZeroVector),OtherElbow,OtherHand);
    RigidLink(GeneratedParts[3],LShoulder,LElbow,OtherShoulder,OtherElbow);
    RigidLink(GeneratedParts[4],LElbow,LHand,OtherElbow,OtherHand);
    FVector Knee,Ankle;
    const FVector RightHip=TorsoPose.TransformPosition(RHip);
    SolveLimb(RHip,RKnee,RAnkle,RightHip,RAnkle+FVector(-Gait*36+KickForward,0,RightLift+KickLift),Knee,Ankle);
    RigidLink(GeneratedParts[5],RHip,RKnee,RightHip,Knee);
    RigidLink(GeneratedParts[6],RKnee,RAnkle,Knee,Ankle);
    // Keep the broad sole flat while planted, lift the toe for the actual kick.
    const FQuat FootRotation=FQuat(FVector(0,1,0),FMath::DegreesToRadians(-FMath::Clamp(KickLift*.40f,0.f,28.f)));
    GeneratedParts[7]->SetRelativeTransform(FTransform(FootRotation,Ankle-FootRotation.RotateVector(RAnkle),FVector::OneVector));
    const FVector LeftHip=TorsoPose.TransformPosition(LHip);
    SolveLimb(LHip,LKnee,LAnkle,LeftHip,LAnkle+FVector(Gait*36,0,LeftLift),Knee,Ankle);
    RigidLink(GeneratedParts[8],LHip,LKnee,LeftHip,Knee);
    RigidLink(GeneratedParts[9],LKnee,LAnkle,Knee,Ankle);
    GeneratedParts[10]->SetRelativeTransform(FTransform(FQuat::Identity,Ankle-LAnkle,FVector::OneVector));
    UpdateSkinnedVisual();
}

void AAshWellWarden::UpdateSkinnedVisual()
{
    if(!SkinnedVisual)return;
    const FName Names[]={TEXT("Body"),TEXT("RightUpperArm"),TEXT("RightForearm"),TEXT("LeftUpperArm"),TEXT("LeftForearm"),
        TEXT("RightThigh"),TEXT("RightShin"),TEXT("RightFoot"),TEXT("LeftThigh"),TEXT("LeftShin"),TEXT("LeftFoot")};
    for(int32 I=0;I<11;++I)
        SkinnedVisual->SetBoneTransformByName(Names[I],SkinRestTransforms[I]*GeneratedParts[I]->GetRelativeTransform(),EBoneSpaces::ComponentSpace);
}

FVector AAshWellWarden::GetHammerPosition() const
{
    return bGeneratedVisual?GeneratedParts[11]->GetComponentTransform().TransformPosition(WardenHQRest::HammerHeadPoint):HammerHead->GetComponentLocation();
}

FVector AAshWellWarden::GetAttackContact() const
{
    if(AttackKind==EWellWardenAttack::Kick&&bGeneratedVisual)
        return GeneratedParts[7]->GetComponentTransform().TransformPosition(WardenHQRest::RAnkle+FVector(20,0,0));
    return GetHammerPosition();
}
