#include "AshWellMountedSampleAnimation.h"
#include "AshWellMountedBoss.h"
#include "Sound/SoundCue.h"
#include "Sound/SoundNodeRandom.h"
#include "Sound/SoundNodeModulator.h"
#include "Sound/SoundNodeWavePlayer.h"
#include "Sound/SoundWave.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Curves/CurveFloat.h"
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
#include "AnimGraphNode_CopyBone.h"
#include "AnimGraphNode_LegIK.h"
#include "AnimGraph/AnimGraphNode_FootPlacement.h"
#include "K2Node_VariableGet.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "KismetCompiler.h"
#include "UObject/Package.h"
#endif

USoundCue* UAshWellMountedSampleTools::BuildCombatSoundCue(const FString& Path,const TArray<USoundWave*>& Variants,float Pitch)
{
#if WITH_EDITOR
    if(Variants.IsEmpty()||Variants.Contains(nullptr))return nullptr;
    auto* Cue=LoadObject<USoundCue>(nullptr,*(Path+TEXT(".")+FPaths::GetBaseFilename(Path)));
    if(Cue){Cue->Modify();Cue->ResetGraph();}
    else{Cue=NewObject<USoundCue>(CreatePackage(*Path),FName(*FPaths::GetBaseFilename(Path)),RF_Public|RF_Standalone|RF_Transactional);Cue->CreateGraph();}
    Cue->VolumeMultiplier=1.f;Cue->bOverrideAttenuation=true;
    Cue->AttenuationOverrides.bAttenuate=true;Cue->AttenuationOverrides.bSpatialize=true;
    Cue->AttenuationOverrides.AttenuationShapeExtents=FVector(700.f,0,0);Cue->AttenuationOverrides.FalloffDistance=2800.f;
    auto* Random=Cue->ConstructSoundNode<USoundNodeRandom>();Random->bRandomizeWithoutReplacement=true;
    TArray<USoundNode*> Players;
    for(auto* Wave:Variants){auto* P=Cue->ConstructSoundNode<USoundNodeWavePlayer>();P->SetSoundWave(Wave);Players.Add(P);}
    Random->SetChildNodes(Players);Random->Weights.Init(1.f,Players.Num());Random->HasBeenUsed.Init(false,Players.Num());
    auto* Mod=Cue->ConstructSoundNode<USoundNodeModulator>();Mod->PitchMin=Pitch*.97f;Mod->PitchMax=Pitch*1.03f;Mod->VolumeMin=.93f;Mod->VolumeMax=1.f;
    TArray<USoundNode*> Child{Random};Mod->SetChildNodes(Child);Cue->FirstNode=Mod;
    // SetChildNodes changes the runtime tree, not the existing editor pins.
    // Reconstruct before linking; otherwise AudioEditor's invariant asserts.
    for(const auto& Node:Cue->AllNodes)
    {
        auto* GraphNode=Node->GetGraphNode();if(!GraphNode)return nullptr;
        GraphNode->ReconstructNode();int32 Inputs=0;
        for(auto* Pin:GraphNode->Pins)if(Pin->Direction==EGPD_Input)++Inputs;
        if(Inputs!=Node->ChildNodes.Num()){UE_LOG(LogTemp,Error,TEXT("AW_SOUND_GRAPH_BLOCKED input count mismatch"));return nullptr;}
    }
    Cue->LinkGraphNodesFromSoundNodes();Cue->PostEditChange();Cue->MarkPackageDirty();return Cue;
#else
    return nullptr;
#endif
}

void UAshWellMountedPhaseNotify::Notify(USkeletalMeshComponent* Mesh,UAnimSequenceBase*,const FAnimNotifyEventReference&)
{
    if(auto* A=Mesh?Cast<UAshWellMountedSampleAnimInstance>(Mesh->GetAnimInstance()):nullptr)
    {if(!A->bActionNotifiesEnabled)return;A->ActionPhase=Phase;++A->PhaseNotifyCount;UE_LOG(LogTemp,Display,TEXT("AW_SAMPLE_NOTIFY phase=%s count=%d"),*Phase.ToString(),A->PhaseNotifyCount);
        if(Phase==FName(TEXT("Strike")))if(auto* Boss=Cast<AAshWellMountedBoss>(Mesh->GetOwner()->GetOwner()))Boss->PlayAttackSwing();
    }
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
    // Measured in evaluated, retargeted clips at the runtime 1.3 horse scale.
    // These are support-bone medians, not a claim of exact sole planting.
    constexpr float WalkSupportSpeed=140.25174f,GallopSupportSpeed=562.19050f;
    auto* SamplesProperty=FindFProperty<FArrayProperty>(UBlendSpace::StaticClass(),TEXT("SampleData"));if(!SamplesProperty)return false;
    while(B->GetNumberOfBlendSamples()>0)B->DeleteSample(B->GetNumberOfBlendSamples()-1);
    auto Add=[&](UAnimSequence* Clip,float Speed,float Rate)
    {
        const int32 Index=B->AddSample(Clip,FVector(Speed,0,0));
        FScriptArrayHelper Samples(SamplesProperty,SamplesProperty->ContainerPtrToValuePtr<void>(B));
        if(Index>=0&&Index<Samples.Num())reinterpret_cast<FBlendSample*>(Samples.GetRawPtr(Index))->RateScale=Rate;
    };
    Add(Idle,0,1);Add(Walk,45,45/WalkSupportSpeed);Add(Walk,180,180/WalkSupportSpeed);
    Add(Gallop,470,470/GallopSupportSpeed);Add(Gallop,850,850/GallopSupportSpeed);
    B->TargetWeightInterpolationSpeedPerSec=12.f;
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
        Socket->RelativeLocation=Transforms[Index].InverseTransformVectorNoScale(I==0?FVector::ZeroVector:FVector(-8,0,-18));
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

UCurveFloat* UAshWellMountedSampleTools::BuildDistanceCurve(const FString& Path,const TArray<FVector2D>& Samples)
{
#if WITH_EDITOR
    if(Samples.Num()<2)return nullptr;
    auto* C=LoadObject<UCurveFloat>(nullptr,*(Path+TEXT(".")+FPaths::GetBaseFilename(Path)));
    if(!C)C=NewObject<UCurveFloat>(CreatePackage(*Path),FName(*FPaths::GetBaseFilename(Path)),RF_Public|RF_Standalone|RF_Transactional);
    C->Modify();C->FloatCurve.Reset();
    for(const auto& Point:Samples){const auto Key=C->FloatCurve.AddKey(Point.X,Point.Y);C->FloatCurve.SetKeyInterpMode(Key,RCIM_Linear);}
    C->MarkPackageDirty();return C;
#else
    return nullptr;
#endif
}

UAnimMontage* UAshWellMountedSampleTools::BuildChargeMontage(UAnimSequence* S,const FString& Path)
{
    FMountedAuthoredAction A;A.Launch=1.15f;A.Strike=1.73f;A.Pass=2.1f;A.ContactEnd=2.2f;A.Brake=2.2f;A.Recover=2.85f;A.End=3.55f;
    return BuildReferenceMontage(S,Path,A,true);
}
UAnimMontage* UAshWellMountedSampleTools::BuildReferenceMontage(UAnimSequence* S,const FString& Path,FMountedAuthoredAction Action,bool WeaponNotifies)
{
#if WITH_EDITOR
    if(!S||FMath::Abs(S->GetPlayLength()-Action.End)>.025f)return nullptr;
    UPackage* Package=CreatePackage(*Path);const FName Name(*FPaths::GetBaseFilename(Path));
    auto* M=NewObject<UAnimMontage>(Package,Name,RF_Public|RF_Standalone|RF_Transactional);
    M->SetSkeleton(S->GetSkeleton());M->SetCompositeLength(S->GetPlayLength());
    auto& Slot=M->SlotAnimTracks.AddDefaulted_GetRef();Slot.SlotName=TEXT("MountedFullBody");
    auto& Segment=Slot.AnimTrack.AnimSegments.AddDefaulted_GetRef();Segment.SetAnimReference(S,true);Segment.StartPos=0;Segment.AnimStartTime=0;Segment.AnimEndTime=S->GetPlayLength();Segment.AnimPlayRate=1;Segment.LoopingCount=1;
    M->BlendIn.SetBlendTime(.16f);M->BlendOut.SetBlendTime(.18f);M->bEnableAutoBlendOut=false;
    const TPair<FName,float> Beats[]={{TEXT("Prepare"),0},{TEXT("Launch"),Action.Launch},{TEXT("Strike"),Action.Strike},{TEXT("Pass"),Action.Pass},{TEXT("Brake"),Action.Brake},{TEXT("Recover"),Action.Recover}};
    for(const auto& Beat:Beats)
    {
        if(Beat.Value>=S->GetPlayLength())continue;
        M->AddAnimCompositeSection(Beat.Key,Beat.Value);
        if(!WeaponNotifies)continue;
        auto* N=NewObject<UAshWellMountedPhaseNotify>(M);N->Phase=Beat.Key;
        auto& Event=M->Notifies.AddDefaulted_GetRef();Event.Notify=N;Event.NotifyName=Beat.Key;Event.Link(M,Beat.Value==0?.001f:Beat.Value);Event.TriggerTimeOffset=0;
    }
    if(WeaponNotifies){auto& W=M->Notifies.AddDefaulted_GetRef();W.NotifyStateClass=NewObject<UAshWellMountedWeaponNotifyState>(M);W.NotifyName=TEXT("Visible blade contact");W.Link(M,Action.Strike);W.SetDuration(Action.ContactEnd-Action.Strike);W.EndLink.Link(M,Action.ContactEnd);}
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

bool UAshWellMountedSampleTools::ConfigureHorseContactBones(USkeletalMesh* Mesh)
{
#if WITH_EDITOR
    if(!Mesh||!Mesh->GetSkeleton())return false;
    auto* S=Mesh->GetSkeleton();
    const TPair<FName,FName> Pairs[]={{TEXT("VB SampleGround"),TEXT("Bone_001")},{TEXT("VB SampleFL"),TEXT("Bone_053")},{TEXT("VB SampleFR"),TEXT("Bone_047")},{TEXT("VB SampleBL"),TEXT("Bone_032")},{TEXT("VB SampleBR"),TEXT("Bone_026")}};
    for(const auto& Pair:Pairs)
    {
        bool Found=false;for(const auto& V:S->GetVirtualBones())if(V.VirtualBoneName==Pair.Key)Found=true;
        if(!Found&&!S->AddNewNamedVirtualBone(TEXT("Bone_000"),Pair.Value,Pair.Key))return false;
    }
    S->MarkPackageDirty();return true;
#else
    return false;
#endif
}

FString UAshWellMountedSampleTools::BuildAnimationGraph(UAnimBlueprint* BP,UAnimSequence* Idle,UBlendSpace* Locomotion,bool FeetIK,FVector LeftFoot,FVector RightFoot,bool HorsePlant)
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
    if(HorsePlant&&Locomotion)
    {
        auto* CS=Create.template operator()<UAnimGraphNode_LocalToComponentSpace>(-350,0,[](auto*){});Link(Source,CS);Source=CS;
        auto* Ground=Create.template operator()<UAnimGraphNode_ModifyBone>(-100,0,[](auto* N)
        {N->Node.BoneToModify.BoneName=TEXT("VB SampleGround");N->Node.TranslationMode=BMM_Replace;N->Node.TranslationSpace=BCS_ComponentSpace;N->Node.RotationMode=BMM_Replace;N->Node.RotationSpace=BCS_ComponentSpace;});
        Link(Source,Ground);Source=Ground;
        const FName FK[]={TEXT("Bone_053"),TEXT("Bone_047"),TEXT("Bone_032"),TEXT("Bone_026")};
        const FName Ball[]={TEXT("Bone_052"),TEXT("Bone_046"),TEXT("Bone_031"),TEXT("Bone_025")};
        const FName IK[]={TEXT("VB SampleFL"),TEXT("VB SampleFR"),TEXT("VB SampleBL"),TEXT("VB SampleBR")};
        const FName Gates[]={TEXT("ContactGateFL"),TEXT("ContactGateFR"),TEXT("ContactGateBL"),TEXT("ContactGateBR")};
        for(int I=0;I<4;++I)
        {
            auto* Copy=Create.template operator()<UAnimGraphNode_CopyBone>(150+I*250,0,[&](auto* N)
            {N->Node.SourceBone.BoneName=FK[I];N->Node.TargetBone.BoneName=IK[I];N->Node.bCopyTranslation=true;N->Node.bCopyRotation=true;N->Node.ControlSpace=BCS_ComponentSpace;});
            Link(Source,Copy);Source=Copy;
        }
        auto* Plant=Create.template operator()<UAnimGraphNode_FootPlacement>(1200,0,[&](auto* N)
        {
            N->Node.IKFootRootBone.BoneName=TEXT("VB SampleGround");N->Node.PelvisBone.BoneName=TEXT("Bone_000");
            N->Node.PlantSpeedMode=EWarpingEvaluationMode::Manual;
            N->Node.PlantSettings.LockType=EFootPlacementLockType::LockRotation;
            N->Node.PlantSettings.SpeedThreshold=60;N->Node.PlantSettings.DistanceToGround=10;
            N->Node.PlantSettings.UnplantRadius=40;N->Node.PlantSettings.MaxExtensionRatio=.8f;
            N->Node.PelvisSettings.MaxOffset=12;N->Node.PelvisSettings.HorizontalRebalancingWeight=0;
            N->Node.PelvisSettings.MaxOffsetHorizontal=25;N->Node.PelvisSettings.HeelLiftRatio=.2f;
            N->Node.TraceSettings.MaxGroundPenetration=1;N->Node.TraceSettings.SweepRadius=2;
            // The retained body collider already ignores Camera while the arena
            // floor blocks it. Reuse that channel so the child rig cannot plant
            // its hooves on its owning Boss's body, without changing collisions.
            N->Node.TraceSettings.SimpleTraceChannel=UEngineTypes::ConvertToTraceType(ECC_Camera);
            N->Node.TraceSettings.ComplexTraceChannel=UEngineTypes::ConvertToTraceType(ECC_Camera);
            for(int I=0;I<4;++I){auto& L=N->Node.LegDefinitions.AddDefaulted_GetRef();L.FKFootBone.BoneName=FK[I];L.IKFootBone.BoneName=IK[I];L.BallBone.BoneName=Ball[I];L.NumBonesInLimb=4;L.SpeedCurveName=Gates[I];L.DisableLockCurveName=TEXT("AuthoredFootLock");}
        });
        for(int I=0;I<Plant->ShowPinForProperties.Num();++I)if(Plant->ShowPinForProperties[I].PropertyName==FName(TEXT("Alpha")))Plant->SetPinVisibility(true,I);
        auto* Alpha=Create.template operator()<UK2Node_VariableGet>(1200,300,[](auto* N){N->VariableReference.SetSelfMember(TEXT("HorseContactAlpha"));});
        auto* AlphaIn=Plant->FindPin(TEXT("Alpha"));LinksOK&=AlphaIn&&Graph->GetSchema()->TryCreateConnection(Alpha->GetValuePin(),AlphaIn);
        Link(Source,Plant);Source=Plant;
        auto* Solve=Create.template operator()<UAnimGraphNode_LegIK>(1550,0,[&](auto* N)
        {for(int I=0;I<4;++I){auto& L=N->Node.LegsDefinition.AddDefaulted_GetRef();L.FKFootBone.BoneName=FK[I];L.IKFootBone.BoneName=IK[I];L.NumBonesInLimb=4;L.bEnableKneeTwistCorrection=false;}});
        Link(Source,Solve);Source=Solve;
        auto* LS=Create.template operator()<UAnimGraphNode_ComponentToLocalSpace>(1900,0,[](auto*){});Link(Source,LS);Source=LS;Root->NodePosX=2200;
    }
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
        // A bounded seat shift lets the shield-side shoulder reach down without
        // stretching the arm. Feet are resolved afterward by the native IK nodes.
        auto* Pelvis=Create.template operator()<UAnimGraphNode_ModifyBone>(-300,-700,[](auto* N)
        {N->Node.BoneToModify.BoneName=TEXT("Hips");N->Node.TranslationMode=BMM_Additive;N->Node.TranslationSpace=BCS_ComponentSpace;});
        for(int I=0;I<Pelvis->ShowPinForProperties.Num();++I)if(Pelvis->ShowPinForProperties[I].PropertyName==FName(TEXT("Translation"))||Pelvis->ShowPinForProperties[I].PropertyName==FName(TEXT("Alpha")))Pelvis->SetPinVisibility(true,I);
        Link(Source,Pelvis);Source=Pelvis;Input(Pelvis,TEXT("Translation"),TEXT("LegacyPelvisOffset"),-1000);Input(Pelvis,TEXT("Alpha"),TEXT("LegacyAlpha"),-900);
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
            for(int J=0;J<IK->ShowPinForProperties.Num();++J)if(IK->ShowPinForProperties[J].PropertyName==FName(TEXT("Alpha")))IK->SetPinVisibility(true,J);
            Link(Source,IK);Source=IK;Input(IK,TEXT("Alpha"),TEXT("RiderContactAlpha"),-100);
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
