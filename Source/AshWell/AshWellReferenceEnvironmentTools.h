#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AshWellReferenceEnvironmentTools.generated.h"
class UStaticMesh;
class AActor;

/** Editor construction of native, serialized foliage instances for this sample. */
UCLASS()
class ASHWELL_API UAshWellReferenceEnvironmentTools : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="AshWell|Reference Environment")
    static int32 AddFoliageInstances(AActor* Owner,UStaticMesh* Mesh,const TArray<FTransform>& Transforms,int32 CullDistance,bool Shadows);
    UFUNCTION(BlueprintCallable,Category="AshWell|Reference Environment")
    static TArray<FVector> InspectFallbackVertices(UStaticMesh* Mesh,const TArray<FVector>& Queries);
    UFUNCTION(BlueprintCallable,Category="AshWell|Reference Environment")
    static void FinishAssetCompilation();
};
