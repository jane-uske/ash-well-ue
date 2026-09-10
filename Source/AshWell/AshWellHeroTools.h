#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AshWellHeroTools.generated.h"
class USkeletalMesh;
UCLASS()
class ASHWELL_API UAshWellHeroTools : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="AshWell|Assets")
    static bool BuildHeroClothing(USkeletalMesh* Mesh);
};
