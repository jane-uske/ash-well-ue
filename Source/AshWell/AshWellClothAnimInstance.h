#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "AshWellClothAnimInstance.generated.h"
UCLASS()
class ASHWELL_API UAshWellClothAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
};
