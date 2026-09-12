#include "AshWellMountedSampleAnimation.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkeletalMeshSocket.h"
#include "Animation/Skeleton.h"
#if WITH_EDITOR
#include "Animation/AnimBlueprint.h"
#include "Animation/BlendSpace.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphSchema.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_SequencePlayer.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_Slot.h"
#include "AnimGraphNode_LocalToComponentSpace.h"
#include "AnimGraphNode_ComponentToLocalSpace.h"
#include "AnimGraphNode_TwoBoneIK.h"
#include "AnimGraphNode_ModifyBone.h"
#include "K2Node_VariableGet.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "KismetCompiler.h"
#include "UObject/Package.h"
#endif

void UAshWellMountedPhaseNotify::Notify(USkeletalMeshComponent* Mesh,UAnimSequenceBase*,const FAnimNotifyEventReference&)
{
    if(auto* A=Mesh?Cast<UAshWellMountedSampleAnimInstance>(Mesh->GetAnimInstance()):nullptr)
    {if(!A->bActionNotifiesEnabled)return;A->ActionPhase=Phase;++A->PhaseNotifyCount;UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_NOTIFY phase=%s count=%d"),*Phase.ToString(),A->PhaseNotifyCount);}
}

bool UAshWellMountedSampleTools::ConfigureHorseBlendSpace(UBlendSpace* B,UAnimSequence* Idle,UAnimSequence* Walk,UAnimSequence* Gallop)
{
#if WITH_EDITOR
    if(!B||!Idle||!Walk||!Gallop)return false;
    B->SetSkeleton(Idle->GetSkeleton());
    // One dimensional speed blend. Foot drift is assessed in runtime, not inferred from this setup.
    auto* Property=FindFProperty<FStructProperty>(UBlendSpace::StaticClass(),TEXT("BlendParameters"));if(!Property)return false;
    auto* Axis=Property->ContainerPtrToValuePtr<FBlendParameter>(B,0);
    Axis->DisplayName=TEXT("Ground speed (cm/s)");Axis->Min=0;Axis->Max=850;Axis->GridNum=10;
    B->AddSample(Idle,FVector(0,0,0));B->AddSample(Walk,FVector(150,0,0));B->AddSample(Gallop,FVector(550,0,0));B->AddSample(Gallop,FVector(850,0,0));
    B->ValidateSampleData();B->ResampleData();B->PostEditChange();B->MarkPackageDirty();return true;
#else
    return false;
#endif
}

bool UAshWellMountedSampleTools::ConfigureRiderSockets(USkeletalMesh* Mesh)
{
#if WITH_EDITOR
    if(!Mesh||!Mesh->GetSkeleton())return false;
    auto* Skeleton=Mesh->GetSkeleton();const auto& Ref=Mesh->GetRefSkeleton();auto Transforms=Ref.GetRefBonePose();
    for(int32 I=0;I<Transforms.Num();++I)if(Ref.GetParentIndex(I)>=0)Transforms[I]*=Transforms[Ref.GetParentIndex(I)];
    for(int I=0;I<2;++I)
    {
        const FName Name=I==0?TEXT("SampleWeaponGrip"):TEXT("SampleShieldGrip");const FName Bone=I==0?TEXT("RightHand"):TEXT("LeftHand");
        int32 Index=Ref.FindBoneIndex(Bone);if(Index==INDEX_NONE)return false;
        auto* Socket=Skeleton->FindSocket(Name);if(!Socket){Socket=NewObject<USkeletalMeshSocket>(Skeleton);Socket->SocketName=Name;Skeleton->Sockets.Add(Socket);}
        Socket->BoneName=Bone;
        const FQuat Desired=I==0?FRotationMatrix::MakeFromY(FVector(0,.28,-.96)).ToQuat():FQuat(FVector::UpVector,PI);
        Socket->RelativeRotation=(Transforms[Index].GetRotation().Inverse()*Desired).Rotator();
        Socket->RelativeLocation=Transforms[Index].InverseTransformVectorNoScale(I==0?FVector::ZeroVector:FVector(-8,0,-24));
    }
    Skeleton->RegisterSlotNode(TEXT("MountedFullBody"));Skeleton->MarkPackageDirty();return true;
#else
    return false;
#endif
}

bool UAshWellMountedSampleTools::ConfigureHorseSockets(USkeletalMesh* Mesh,FVector LeftStirrup,FVector RightStirrup)
{
#if WITH_EDITOR
    if(!Mesh||!Mesh->GetSkeleton())return false;
    auto* S=Mesh->GetSkeleton();const auto& Ref=Mesh->GetRefSkeleton();auto P=Ref.GetRefBonePose();
    for(int32 I=0;I<P.Num();++I)if(Ref.GetParentIndex(I)>=0)P[I]*=P[Ref.GetParentIndex(I)];
    for(int I=0;I<2;++I)
    {
        const FName Bone=I==0?TEXT("Bone_021"):TEXT("Bone_023");const FName Name=I==0?TEXT("SampleStirrupLeft"):TEXT("SampleStirrupRight");
        int32 Index=Ref.FindBoneIndex(Bone);if(Index==INDEX_NONE)return false;
        auto* Socket=S->FindSocket(Name);if(!Socket){Socket=NewObject<USkeletalMeshSocket>(S);Socket->SocketName=Name;S->Sockets.Add(Socket);}
        Socket->BoneName=Bone;Socket->RelativeLocation=P[Index].InverseTransformPosition(I==0?LeftStirrup:RightStirrup);
    }
    S->MarkPackageDirty();return true;
#else
    return false;
#endif
}

UAnimMontage* UAshWellMountedSampleTools::BuildChargeMontage(UAnimSequence* S,const FString& Path)
{
#if WITH_EDITOR
    if(!S)return nullptr;
    UPackage* Package=CreatePackage(*Path);const FName Name(*FPaths::GetBaseFilename(Path));
    auto* M=NewObject<UAnimMontage>(Package,Name,RF_Public|RF_Standalone|RF_Transactional);
    M->SetSkeleton(S->GetSkeleton());M->SetCompositeLength(S->GetPlayLength());
    auto& Slot=M->SlotAnimTracks.AddDefaulted_GetRef();Slot.SlotName=TEXT("MountedFullBody");
    auto& Segment=Slot.AnimTrack.AnimSegments.AddDefaulted_GetRef();Segment.SetAnimReference(S,true);Segment.StartPos=0;Segment.AnimStartTime=0;Segment.AnimEndTime=S->GetPlayLength();Segment.AnimPlayRate=1;Segment.LoopingCount=1;
    M->BlendIn.SetBlendTime(.16f);M->BlendOut.SetBlendTime(.18f);
    const TPair<FName,float> Beats[]={{TEXT("Prepare"),0},{TEXT("Launch"),1.15f},{TEXT("Strike"),1.73f},{TEXT("Pass"),2.10f},{TEXT("Brake"),2.20f},{TEXT("Recover"),2.85f}};
    for(const auto& Beat:Beats)
    {
        M->AddAnimCompositeSection(Beat.Key,Beat.Value);
        auto* N=NewObject<UAshWellMountedPhaseNotify>(M);N->Phase=Beat.Key;
        auto& Event=M->Notifies.AddDefaulted_GetRef();Event.Notify=N;Event.NotifyName=Beat.Key;Event.Link(M,Beat.Value==0?.001f:Beat.Value);Event.TriggerTimeOffset=0;
    }
    auto& W=M->Notifies.AddDefaulted_GetRef();W.NotifyStateClass=NewObject<UAshWellMountedWeaponNotifyState>(M);W.NotifyName=TEXT("Visible blade contact");W.Link(M,1.73f);W.SetDuration(.47f);W.EndLink.Link(M,2.20f);
    M->PostEditChange();M->MarkPackageDirty();return M;
#else
    return nullptr;
#endif
}
void UAshWellMountedWeaponNotifyState::NotifyBegin(USkeletalMeshComponent* Mesh,UAnimSequenceBase*,float,const FAnimNotifyEventReference&)
{
    if(auto* A=Mesh?Cast<UAshWellMountedSampleAnimInstance>(Mesh->GetAnimInstance()):nullptr)
    {if(!A->bActionNotifiesEnabled)return;A->bWeaponWindow=true;++A->WindowBeginCount;UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_WINDOW begin=%d"),A->WindowBeginCount);}
}
void UAshWellMountedWeaponNotifyState::NotifyEnd(USkeletalMeshComponent* Mesh,UAnimSequenceBase*,const FAnimNotifyEventReference&)
{
    if(auto* A=Mesh?Cast<UAshWellMountedSampleAnimInstance>(Mesh->GetAnimInstance()):nullptr)
    {A->bWeaponWindow=false;++A->WindowEndCount;UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_WINDOW end=%d"),A->WindowEndCount);}
}

FString UAshWellMountedSampleTools::BuildAnimationGraph(UAnimBlueprint* BP,UAnimSequence* Idle,UBlendSpace* Locomotion,bool FeetIK,FVector LeftFoot,FVector RightFoot)
{
#if WITH_EDITOR
    if(!BP||!BP->TargetSkeleton||!Idle)return TEXT("ERROR: missing blueprint/skeleton/sequence");
    TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);UEdGraph* Graph=nullptr;UAnimGraphNode_Root* Root=nullptr;
    for(auto* G:Graphs)for(auto N:G->Nodes)if(auto* R=Cast<UAnimGraphNode_Root>(N)){Graph=G;Root=R;break;}
    if(!Graph||!Root)return TEXT("ERROR: animation graph has no root");
    BP->Modify();Graph->Modify();const auto Old=Graph->Nodes;
    for(auto N:Old)if(N!=Root)Graph->RemoveNode(N);
    Root->BreakAllNodeLinks();Root->NodePosX=1000;Root->NodePosY=0;
    auto Create=[&]<typename T>(int32 X,int32 Y,auto Configure)->T*
    {FGraphNodeCreator<T> C(*Graph);T* N=C.CreateNode();Configure(N);N->NodePosX=X;N->NodePosY=Y;C.Finalize();return N;};
    auto PosePin=[](UEdGraphNode* N,EEdGraphPinDirection D)->UEdGraphPin*
    {for(auto* P:N->Pins)if(P->Direction==D&&P->PinType.PinSubCategoryObject.IsValid()&&P->PinType.PinSubCategoryObject->GetName().Contains(TEXT("PoseLink")))return P;return nullptr;};
    bool LinksOK=true;
    auto Link=[&](UEdGraphNode* A,UEdGraphNode* B)
    {auto* Out=PosePin(A,EGPD_Output);auto* In=PosePin(B,EGPD_Input);LinksOK&=Out&&In&&Graph->GetSchema()->TryCreateConnection(Out,In);};
    UEdGraphNode* Source=nullptr;
    if(Locomotion)
    {
        auto* Player=Create.template operator()<UAnimGraphNode_BlendSpacePlayer>(-1000,0,[&](auto* N){N->Node.SetBlendSpace(Locomotion);});Source=Player;
        for(int32 I=0;I<Player->ShowPinForProperties.Num();++I)if(Player->ShowPinForProperties[I].PropertyName==FName(TEXT("PlayRate")))Player->SetPinVisibility(true,I);
        for(auto Pair:{TPair<FName,FName>(TEXT("GroundSpeed"),TEXT("X")),TPair<FName,FName>(TEXT("StrideRate"),TEXT("PlayRate"))})
        {
            auto* Getter=Create.template operator()<UK2Node_VariableGet>(-1300,Pair.Key==FName(TEXT("GroundSpeed"))?0:150,[&](auto* N){N->VariableReference.SetSelfMember(Pair.Key);});
            auto* In=Player->FindPin(Pair.Value);auto* Out=Getter->GetValuePin();LinksOK&=In&&Out&&Graph->GetSchema()->TryCreateConnection(Out,In);
        }
    }
    else Source=Create.template operator()<UAnimGraphNode_SequencePlayer>(-1000,0,[&](auto* N){N->Node.SetSequence(Idle);N->Node.SetLoopAnimation(true);});
    auto* Slot=Create.template operator()<UAnimGraphNode_Slot>(-650,0,[](auto* N){N->Node.SlotName=TEXT("MountedFullBody");});Link(Source,Slot);Source=Slot;
    if(FeetIK)
    {
        auto* ToComponent=Create.template operator()<UAnimGraphNode_LocalToComponentSpace>(-400,0,[](auto*){});Link(Source,ToComponent);Source=ToComponent;
        auto Input=[&](UEdGraphNode* Node,FName Pin,FName Variable,int Y)
        {
            auto* Getter=Create.template operator()<UK2Node_VariableGet>(Node->NodePosX,Y,[&](auto* N){N->VariableReference.SetSelfMember(Variable);});
            auto* In=Node->FindPin(Pin);auto* Out=Getter->GetValuePin();LinksOK&=In&&Out&&Graph->GetSchema()->TryCreateConnection(Out,In);
        };
        auto RotationControl=[&](FName Bone,FName Variable,bool Additive,int X)
        {
            auto* N=Create.template operator()<UAnimGraphNode_ModifyBone>(X,-450,[&](auto* Node)
            {Node->Node.BoneToModify.BoneName=Bone;Node->Node.RotationMode=Additive?BMM_Additive:BMM_Replace;Node->Node.RotationSpace=BCS_ComponentSpace;});
            for(int I=0;I<N->ShowPinForProperties.Num();++I)if(N->ShowPinForProperties[I].PropertyName==FName(TEXT("Rotation"))||N->ShowPinForProperties[I].PropertyName==FName(TEXT("Alpha")))N->SetPinVisibility(true,I);
            Link(Source,N);Source=N;Input(N,TEXT("Rotation"),Variable,-180);Input(N,TEXT("Alpha"),TEXT("LegacyAlpha"),-100);
        };
        RotationControl(TEXT("Spine02"),TEXT("LegacyTorsoRotation"),true,-250);
        for(int I=0;I<2;++I)
        {
            auto* IK=Create.template operator()<UAnimGraphNode_TwoBoneIK>(100+I*700,-450,[&](auto* N)
            {N->Node.IKBone.BoneName=I==0?TEXT("LeftHand"):TEXT("RightHand");N->Node.EffectorLocationSpace=BCS_ComponentSpace;N->Node.JointTargetLocationSpace=BCS_ComponentSpace;N->Node.JointTargetLocation=FVector(I==0?-100:100,30,100);N->Node.bAllowStretching=false;N->Node.bMaintainEffectorRelRot=true;});
            for(int J=0;J<IK->ShowPinForProperties.Num();++J)if(IK->ShowPinForProperties[J].PropertyName==FName(TEXT("Alpha")))IK->SetPinVisibility(true,J);
            Link(Source,IK);Source=IK;Input(IK,TEXT("EffectorLocation"),I==0?TEXT("LegacyLeftHand"):TEXT("LegacyRightHand"),-180);Input(IK,TEXT("Alpha"),TEXT("LegacyAlpha"),-100);
            RotationControl(I==0?TEXT("LeftHand"):TEXT("RightHand"),I==0?TEXT("LegacyLeftHandRotation"):TEXT("LegacyRightHandRotation"),false,450+I*700);
        }
        for(int32 I=0;I<2;++I)
        {
            auto* IK=Create.template operator()<UAnimGraphNode_TwoBoneIK>(-150+I*350,0,[&](auto* N)
            {N->Node.IKBone.BoneName=I==0?TEXT("LeftFoot"):TEXT("RightFoot");N->Node.EffectorLocationSpace=BCS_ComponentSpace;N->Node.JointTargetLocationSpace=BCS_ComponentSpace;
             N->Node.EffectorLocation=I==0?LeftFoot:RightFoot;N->Node.JointTargetLocation=N->Node.EffectorLocation+FVector(0,-70,55);N->Node.bMaintainEffectorRelRot=true;N->Node.bAllowStretching=false;});
            Link(Source,IK);Source=IK;
            auto* Target=Create.template operator()<UK2Node_VariableGet>(-150+I*350,250,[&](auto* N){N->VariableReference.SetSelfMember(I==0?TEXT("LeftFootTarget"):TEXT("RightFootTarget"));});
            auto* In=IK->FindPin(TEXT("EffectorLocation"));auto* Out=Target->GetValuePin();LinksOK&=In&&Out&&Graph->GetSchema()->TryCreateConnection(Out,In);
        }
        auto* ToLocal=Create.template operator()<UAnimGraphNode_ComponentToLocalSpace>(650,0,[](auto*){});Link(Source,ToLocal);Source=ToLocal;
    }
    Link(Source,Root);
    if(!LinksOK)
    {
        FString Details=TEXT("ERROR: graph links failed; ");
        for(auto N:Graph->Nodes){Details+=N->GetClass()->GetName()+TEXT("[");for(auto* P:N->Pins)Details+=P->PinName.ToString()+TEXT(":")+FString::FromInt(P->LinkedTo.Num())+TEXT(",");Details+=TEXT("] ");}
        return Details;
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FCompilerResultsLog Log;FKismetEditorUtilities::CompileBlueprint(BP,EBlueprintCompileOptions::None,&Log);BP->MarkPackageDirty();
    return FString::Printf(TEXT("nodes=%d errors=%d warnings=%d status=%d"),Graph->Nodes.Num(),Log.NumErrors,Log.NumWarnings,int32(BP->Status));
#else
    return TEXT("ERROR: requires editor build");
#endif
}
