#include "AshWellReferenceEnvironmentTools.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "StaticMeshResources.h"
#if WITH_EDITOR
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#endif

void UAshWellReferenceEnvironmentTools::FinishAssetCompilation()
{
#if WITH_EDITOR
    FAssetCompilingManager::Get().FinishAllCompilation();
    if(GShaderCompilingManager)GShaderCompilingManager->FinishAllCompilation();
#endif
}

TArray<FVector> UAshWellReferenceEnvironmentTools::InspectFallbackVertices(UStaticMesh* Mesh,const TArray<FVector>& Queries)
{
    TArray<FVector> Result;
#if WITH_EDITOR
    if(!Mesh||!Mesh->GetRenderData()||Mesh->GetRenderData()->LODResources.IsEmpty())return Result;
    const auto& Vertices=Mesh->GetRenderData()->LODResources[0].VertexBuffers.PositionVertexBuffer;
    UE_LOG(LogTemp,Display,TEXT("AW_REFERENCE_FALLBACK vertices=%d"),Vertices.GetNumVertices());
    for(const auto& Point:Queries)
    {
        double Best=MAX_dbl;FVector Nearest=FVector::ZeroVector;
        for(uint32 I=0;I<Vertices.GetNumVertices();++I)
        {const FVector V(Vertices.VertexPosition(I));const double D=FVector::DistSquared2D(V,Point);if(D<Best){Best=D;Nearest=V;}}
        Result.Add(Nearest);
    }
#endif
    return Result;
}

int32 UAshWellReferenceEnvironmentTools::AddFoliageInstances(AActor* Owner,UStaticMesh* Mesh,const TArray<FTransform>& Transforms,int32 CullDistance,bool Shadows)
{
#if WITH_EDITOR
    if(!IsValid(Owner)||!IsValid(Mesh)||Owner->GetWorld()->IsGameWorld())return -1;
    Owner->Modify();
    if(!Owner->GetRootComponent())
    {
        auto* Root=NewObject<USceneComponent>(Owner,TEXT("FoliageRoot"),RF_Transactional);
        Owner->AddInstanceComponent(Root);Owner->SetRootComponent(Root);Root->SetMobility(EComponentMobility::Static);Root->RegisterComponent();
    }
    auto* Instances=NewObject<UHierarchicalInstancedStaticMeshComponent>(Owner,NAME_None,RF_Transactional);
    Owner->AddInstanceComponent(Instances);Instances->SetupAttachment(Owner->GetRootComponent());
    Instances->SetMobility(EComponentMobility::Static);Instances->SetStaticMesh(Mesh);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);Instances->SetGenerateOverlapEvents(false);
    Instances->SetCanEverAffectNavigation(false);Instances->SetCastShadow(Shadows);
    Instances->SetCullDistances(FMath::Max(0,CullDistance-400),CullDistance);
    Instances->bAutoRebuildTreeOnInstanceChanges=false;Instances->RegisterComponent();
    Instances->AddInstances(Transforms,false,true,false);
    Instances->bAutoRebuildTreeOnInstanceChanges=true;Instances->BuildTreeIfOutdated(false,true);
    Owner->MarkPackageDirty();return Instances->GetInstanceCount();
#else
    return -1;
#endif
}
