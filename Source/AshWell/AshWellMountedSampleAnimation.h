#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Engine/DataAsset.h"
#include "AshWellMountedSampleAnimation.generated.h"

class UAnimBlueprint;
class UAnimSequence;
class UBlendSpace;
class UAnimMontage;
class USkeletalMesh;

/** Authored action candidates are registered explicitly. Missing entries retain their
 * existing compatibility driver, so adding one move never migrates the others. */
UCLASS(BlueprintType)
class ASHWELL_API UAshWellMountedActionSet : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="Mounted Actions") TMap<FName,TObjectPtr<UAnimMontage>> Montages;
};

/** Graph inputs and observable notify state. The AnimBP evaluates the pose. */
UCLASS(Transient, Blueprintable)
class ASHWELL_API UAshWellMountedSampleAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") float GroundSpeed=0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") float StrideRate=1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") float HorseContactAlpha=1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FVector LeftFootTarget=FVector(-35,-12,35);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FVector RightFootTarget=FVector(35,-12,35);
    // Compatibility inputs from the existing five action drivers. New authored
    // montages bypass these controls; this is not a migration of their timing.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") float LegacyAlpha=0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FVector LegacyRightHand;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FVector LegacyLeftHand;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FRotator LegacyTorsoRotation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FVector LegacyPelvisOffset;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FRotator LegacyRightHandRotation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mounted Sample") FRotator LegacyLeftHandRotation;
    UPROPERTY(BlueprintReadOnly, Category="Mounted Sample") FName ActionPhase=NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Mounted Sample") bool bWeaponWindow=false;
    UPROPERTY(BlueprintReadOnly, Category="Mounted Sample") int32 PhaseNotifyCount=0;
    UPROPERTY(BlueprintReadOnly, Category="Mounted Sample") int32 WindowBeginCount=0;
    UPROPERTY(BlueprintReadOnly, Category="Mounted Sample") int32 WindowEndCount=0;
    bool bActionNotifiesEnabled=false;
    void ClearActionState(){ActionPhase=NAME_None;bWeaponWindow=false;bActionNotifiesEnabled=false;}
};

UCLASS(meta=(DisplayName="Mounted action phase"))
class ASHWELL_API UAshWellMountedPhaseNotify : public UAnimNotify
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Mounted Sample") FName Phase;
    virtual void Notify(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& Reference) override;
};

UCLASS(meta=(DisplayName="Mounted weapon window"))
class ASHWELL_API UAshWellMountedWeaponNotifyState : public UAnimNotifyState
{
    GENERATED_BODY()
public:
    virtual void NotifyBegin(USkeletalMeshComponent* Mesh,UAnimSequenceBase* Animation,float Duration,const FAnimNotifyEventReference& Reference) override;
    virtual void NotifyEnd(USkeletalMeshComponent* Mesh,UAnimSequenceBase* Animation,const FAnimNotifyEventReference& Reference) override;
};

/** Editor construction of real, editable engine animation graphs. */
UCLASS()
class ASHWELL_API UAshWellMountedSampleTools : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static FString BuildAnimationGraph(UAnimBlueprint* Blueprint,UAnimSequence* Idle,UBlendSpace* Locomotion,bool FeetIK,FVector LeftFoot,FVector RightFoot,bool HorsePlant=false);
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static bool ConfigureHorseBlendSpace(UBlendSpace* BlendSpace,UAnimSequence* Idle,UAnimSequence* Walk,UAnimSequence* Gallop);
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static UAnimMontage* BuildChargeMontage(UAnimSequence* Sequence,const FString& PackagePath);
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static bool ConfigureRiderSockets(USkeletalMesh* Mesh);
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static bool ConfigureHorseSockets(USkeletalMesh* Mesh,FVector LeftStirrup,FVector RightStirrup);
    UFUNCTION(BlueprintCallable,Category="AshWell|Mounted Sample")
    static bool ConfigureHorseContactBones(USkeletalMesh* Mesh);
};
