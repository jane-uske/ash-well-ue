#include "AshWellHeroTools.h"
#if WITH_EDITOR
#include "ClothingAssetFactory.h"
#include "ClothingAsset.h"
#include "ClothLODData.h"
#include "ChaosCloth/ChaosClothConfig.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#endif
bool UAshWellHeroTools::BuildHeroClothing(USkeletalMesh* Mesh)
{
#if WITH_EDITOR
    if(!Mesh||!Mesh->GetImportedModel())return false;
    // Keep the binding transaction scoped until user section metadata is written.
    // An inner BindToSkeletalMesh post-edit rebuild otherwise discards its render mapping.
    FScopedSkeletalMeshPostEditChange ScopedPostEditChange(Mesh);
    Mesh->Modify();
    if(Mesh->GetMeshClothingAssets().Num())
    {
        auto* Existing=Cast<UClothingAssetCommon>(Mesh->GetMeshClothingAssets()[0]);if(!Existing)return false;
        Existing->UnbindFromSkeletalMesh(Mesh,0,0);
        if(!Existing->BindToSkeletalMesh(Mesh,0,0,0))return false;
        auto& Model=Mesh->GetImportedModel()->LODModels[0];
        auto& User=Model.UserSectionsData.FindOrAdd(Model.Sections[0].OriginalDataSectionIndex);
        User.CorrespondClothAssetIndex=0;User.ClothingData.AssetGuid=Existing->GetAssetGuid();User.ClothingData.AssetLodIndex=0;
        Mesh->InvalidateDeriveDataCacheGUID();Mesh->MarkPackageDirty();return true;
    }
    auto* Physics=NewObject<UPhysicsAsset>(Mesh,TEXT("HeroClothCollision"),RF_Transactional);
    const auto& Ref=Mesh->GetRefSkeleton();
    TArray<FTransform> Transforms=Ref.GetRefBonePose();
    for(int32 I=0;I<Transforms.Num();++I)if(Ref.GetParentIndex(I)>=0)Transforms[I]*=Transforms[Ref.GetParentIndex(I)];
    auto Capsule=[&](FName Bone,FVector Start,FVector End,float Radius)
    {
        int32 Index=Ref.FindBoneIndex(Bone);if(Index==INDEX_NONE)return;
        auto* Body=NewObject<USkeletalBodySetup>(Physics);Body->BoneName=Bone;
        FKSphylElem Shape;Shape.Radius=Radius;Shape.Length=FVector::Distance(Start,End);
        Shape.Center=Transforms[Index].InverseTransformPosition((Start+End)*.5f);
        Shape.Rotation=FRotationMatrix::MakeFromZ(Transforms[Index].InverseTransformVectorNoScale(End-Start)).Rotator();
        Body->AggGeom.SphylElems.Add(Shape);Physics->SkeletalBodySetups.Add(Body);
    };
    Capsule(TEXT("spine_02"),FVector(1,0,108),FVector(2,0,140),15);
    Capsule(TEXT("pelvis"),FVector(1,-7,91),FVector(1,7,91),17);
    Capsule(TEXT("thigh_L"),FVector(1,12,82),FVector(1,13,57),11);
    Capsule(TEXT("thigh_R"),FVector(1,-12,82),FVector(1,-13,57),11);
    Physics->UpdateBodySetupIndexMap();Physics->UpdateBoundsBodiesArray();
    FSkeletalMeshClothBuildParams Params;Params.AssetName=TEXT("TravellerWindCloth");Params.LodIndex=0;Params.SourceSection=0;Params.bRemoveFromMesh=false;Params.PhysicsAsset=Physics;
    auto* Factory=NewObject<UClothingAssetFactory>();
    auto* Asset=Cast<UClothingAssetCommon>(Factory->CreateFromSkeletalMesh(Mesh,Params));
    if(!Asset||Asset->LodData.IsEmpty())return false;
    auto& Lod=Asset->LodData[0];auto& Mask=Lod.PointWeightMaps.AddDefaulted_GetRef();
    Mask.Initialize(Lod.PhysicalMeshData.Vertices.Num());Mask.Name=TEXT("Pinned shoulders and free hem");Mask.CurrentTarget=(uint8)EWeightMapTargetCommon::MaxDistance;Mask.bEnabled=true;
    for(int32 I=0;I<Mask.Values.Num();++I)
    {
        const auto& P=Lod.PhysicalMeshData.Vertices[I];
        const float T=FMath::Clamp((142.f-P.Z)/77.f,0.f,1.f);
        Mask.Values[I]=(P.X>-10.f||P.Z>142.f)?0.f:75.f*T*T;
    }
    if(auto* Config=Asset->GetClothConfig<UChaosClothConfig>())
    {
        Config->DampingCoefficient=.18f;Config->LocalDampingCoefficient=.12f;
        Config->EdgeStiffnessWeighted={.85f,.85f};Config->BendingStiffnessWeighted={.08f,.08f};
        Config->Drag={.12f,.12f};Config->Lift={.03f,.03f};Config->CollisionThickness=2.f;
        Config->LinearVelocityScale=FVector(.7f);Config->AngularVelocityScale=.5f;
    }
    Asset->ApplyParameterMasks();Asset->InvalidateAllCachedData();
    Mesh->AddClothingAsset(Asset);
    if(!Asset->BindToSkeletalMesh(Mesh,0,0,0))return false;
    auto& Model=Mesh->GetImportedModel()->LODModels[0];
    auto& User=Model.UserSectionsData.FindOrAdd(Model.Sections[0].OriginalDataSectionIndex);
    User.CorrespondClothAssetIndex=0;User.ClothingData.AssetGuid=Asset->GetAssetGuid();User.ClothingData.AssetLodIndex=0;
    Mesh->InvalidateDeriveDataCacheGUID();Mesh->MarkPackageDirty();return true;
#else
    return false;
#endif
}
