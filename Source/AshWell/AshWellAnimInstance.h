#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "AshWellAnimInstance.generated.h"

/** Small native pose crossfade; gameplay remains the owner of action timing. */
UCLASS(Transient)
class ASHWELL_API UAshWellAnimInstance : public UAnimSingleNodeInstance
{
    GENERATED_BODY()
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
};
