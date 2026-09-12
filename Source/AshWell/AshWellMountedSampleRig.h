#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellMountedSampleRig.generated.h"
class USkeletalMeshComponent;
class UStaticMeshComponent;
class UAnimMontage;
class UAshWellMountedSampleAnimInstance;
class UCameraComponent;
class UAshWellMountedActionSet;
struct FMountedAuthoredAction;

/** Independent skeletal rider/horse visual, evaluated through editable AnimBPs. */
UCLASS()
class ASHWELL_API AAshWellMountedSampleRig : public AActor
{
    GENERATED_BODY()
public:
    AAshWellMountedSampleRig();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    void EvaluatePose(float DeltaSeconds,float GroundSpeed,bool DeferHorse=false);
    void SetLegacyPose(FVector Grip,FVector Direction,FVector ShieldHand,FQuat Torso,float HorsePitch,bool Enabled,FVector PelvisOffset=FVector::ZeroVector);
    bool PlayCharge();
    bool PlayDeath();
    bool HasAuthoredAction(FName Action) const;
    const FMountedAuthoredAction* GetActionDefinition(FName Action) const;
    float GetAuthoredFrameSpeed(float DeltaSeconds) const;
    bool PlayAction(FName Action);
    void StopCharge();
    float GetChargeTime() const;
    bool IsChargePlaying() const;
    bool HasWeaponWindow() const;
    bool IsReady() const{return bReady;}
    bool UsesFootPlacement() const{return bFootPlacementCandidate;}
    void SetGroundContactEnabled(bool Enabled){bGroundContactEnabled=Enabled;}
    FVector GetGrip() const;
    FVector GetTip() const;
    UAshWellMountedSampleAnimInstance* RiderAnimation() const;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Horse;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> Rider;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Poleaxe;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Shield;
private:
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> Charge;
    UPROPERTY(Transient) TObjectPtr<UAnimMontage> HorseCharge;
    UPROPERTY(Transient) TObjectPtr<UAshWellMountedActionSet> ActionSet;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> ReviewCamera;
    float ReviewTime=0;
    FVector LegacyGrip,LegacyDirection=FVector::ForwardVector,LegacyShieldHand;
    FVector LegacyPelvisOffset;
    FQuat LegacyTorso=FQuat::Identity;
    float LegacyPitch=0,ChargeElapsed=0;
    bool bLegacyPose=false,bChargeStarted=false;
    FTransform SeatRest;
    bool bReady=false;
    bool bFootPlacementCandidate=false;
    bool bGroundContactEnabled=true;
    bool bDeathPose=false;
    float PendingHorseDelta=0;
    float ReportTime=0;
    float PreviousChargeElapsed=0;
    FName ActiveAction;
};
