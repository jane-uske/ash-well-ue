#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellWarden.generated.h"

class UCapsuleComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UPointLightComponent;
class USoundBase;

UENUM()
enum class EWellWardenState : uint8
{
    Dormant, Chase, Windup, Strike, Recovery, Stagger, Dead
};

/** A deliberately readable, single-attack combat opponent. Actor origin is capsule centre, 135cm above its feet. */
UCLASS()
class ASHWELL_API AAshWellWarden : public AActor
{
    GENERATED_BODY()
public:
    AAshWellWarden();
    virtual void Tick(float DeltaSeconds) override;
    virtual void BeginPlay() override;

    void ActivateEncounter(APawn* Player);
    bool ReceiveMeleeHit(float Damage, const FVector& Source);
    void SetArenaBounds(FVector Center, FVector2D HalfExtents);
    float GetHealthFraction() const { return Health / MaximumHealth; }
    float GetHealth() const { return Health; }
    FString GetStateLabel() const;
    bool IsDead() const { return State == EWellWardenState::Dead; }
    bool IsAttacking() const { return State == EWellWardenState::Windup || State == EWellWardenState::Strike; }
    FVector GetAimPoint() const;
    float GetAttackProgress() const;
    EWellWardenState GetCombatState() const { return State; }
    FSimpleMulticastDelegate OnDefeated;

    UPROPERTY(VisibleAnywhere) TObjectPtr<UCapsuleComponent> Capsule;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> Body;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> EyeLight;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> ImpactLight;

private:
    static constexpr float MaximumHealth = 240.0f;
    static constexpr float WindupSeconds = 1.05f;
    static constexpr float StrikeSeconds = 0.22f;
    static constexpr float RecoverySeconds = 1.25f;
    static constexpr float AttackDamage = 35.0f;
    static constexpr float WalkSpeed = 125.0f;

    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Parts;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Sparks;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightUpperArm;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightForearm;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftUpperArm;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftForearm;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> HammerShaft;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> HammerHead;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> HammerBand;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftThigh;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftShin;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightThigh;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightShin;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftFoot;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightFoot;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> WarningRing;
    UPROPERTY(Transient) TObjectPtr<USoundBase> SwingSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> SlamSound;
    TWeakObjectPtr<APawn> Target;
    EWellWardenState State = EWellWardenState::Dormant;
    float Health = MaximumHealth;
    float StateTime = 0.0f;
    float TotalTime = 0.0f;
    float GaitPhase = 0.0f;
    float HitFlash = 0.0f;
    float SparkTime = 1.0f;
    float LastStaggerTime = -10.0f;
    float RecoveryAfterStagger = 0.0f;
    bool bStrikeHit = false;
    bool bHasBounds = false;
    FVector ArenaCenter = FVector::ZeroVector;
    FVector2D ArenaHalfExtents = FVector2D(1000, 1000);
    FVector SparkOrigin = FVector::ZeroVector;
    TArray<FVector> SparkVelocities;

    UStaticMeshComponent* AddPart(const TCHAR* Name, UStaticMesh* Mesh, UMaterialInterface* Material,
        FVector Position, FVector Dimensions, FRotator Rotation = FRotator::ZeroRotator);
    void ChangeState(EWellWardenState NewState);
    void FaceTarget(float DeltaSeconds, float DegreesPerSecond);
    void StepTowardTarget(float DeltaSeconds);
    void TryStrike();
    void UpdatePose(float DeltaSeconds);
    void UpdateSparks(float DeltaSeconds);
    void EmitSparks(const FVector& WorldPosition);
    static void SetLink(UStaticMeshComponent* Part, const FVector& A, const FVector& B, float Width);
};
