#include "AshWellClothAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "AnimNodes/AnimNode_CopyPoseFromMesh.h"
struct FAshWellClothProxy : FAnimInstanceProxy
{
    FAnimNode_CopyPoseFromMesh CopyPose;
    explicit FAshWellClothProxy(UAnimInstance* Instance):FAnimInstanceProxy(Instance){CopyPose.bUseAttachedParent=true;}
    virtual void Initialize(UAnimInstance* Instance) override
    {
        FAnimInstanceProxy::Initialize(Instance);CopyPose.Initialize_AnyThread(FAnimationInitializeContext(this));
    }
    virtual void PreUpdate(UAnimInstance* Instance,float Dt) override
    {
        FAnimInstanceProxy::PreUpdate(Instance,Dt);CopyPose.PreUpdate(Instance);
    }
    virtual void UpdateAnimationNode(const FAnimationUpdateContext& Context) override{CopyPose.Update_AnyThread(Context);}
    virtual bool Evaluate(FPoseContext& Output) override
    {
        CopyPose.CacheBones_AnyThread(FAnimationCacheBonesContext(this));CopyPose.Evaluate_AnyThread(Output);return true;
    }
};
FAnimInstanceProxy* UAshWellClothAnimInstance::CreateAnimInstanceProxy(){return new FAshWellClothProxy(this);}
