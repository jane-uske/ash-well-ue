#include "AshWellAnimInstance.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"

struct FAshWellPoseProxy : FAnimSingleNodeInstanceProxy
{
    explicit FAshWellPoseProxy(UAnimInstance* Instance):FAnimSingleNodeInstanceProxy(Instance){}
    TArray<FTransform> PreviousPose,TransitionPose;
    UAnimationAsset* LastAsset=nullptr;
    float BlendAge=1.f;
    virtual void PreUpdate(UAnimInstance* Instance,float Dt) override
    {
        FAnimSingleNodeInstanceProxy::PreUpdate(Instance,Dt);
        if(CurrentAsset!=LastAsset){TransitionPose=PreviousPose;BlendAge=0;LastAsset=CurrentAsset;}
        BlendAge+=Dt;
    }
    virtual bool Evaluate(FPoseContext& Output) override
    {
        const bool Valid=FAnimSingleNodeInstanceProxy::Evaluate(Output);
        const int32 Count=Output.Pose.GetNumBones();
        const float Alpha=FMath::SmoothStep(0.f,.10f,BlendAge);
        if(TransitionPose.Num()==Count&&Alpha<1.f)
            for(FCompactPoseBoneIndex I:Output.Pose.ForEachBoneIndex())
            {FTransform T;T.Blend(TransitionPose[I.GetInt()],Output.Pose[I],Alpha);Output.Pose[I]=T;}
        PreviousPose.SetNum(Count);
        for(FCompactPoseBoneIndex I:Output.Pose.ForEachBoneIndex())PreviousPose[I.GetInt()]=Output.Pose[I];
        return Valid;
    }
};
FAnimInstanceProxy* UAshWellAnimInstance::CreateAnimInstanceProxy(){return new FAshWellPoseProxy(this);}
