#pragma once
#include "CoreMinimal.h"
#include "AshWellIntroCharacter.h"
#include "AshWellCombatCharacter.generated.h"

class AAshWellCombatArena;
class AAshWellWarden;
class UStaticMeshComponent;

UCLASS()
class ASHWELL_API AAshWellCombatCharacter : public AAshWellIntroCharacter
{
    GENERATED_BODY()
public:
    AAshWellCombatCharacter();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual float TakeDamage(float Damage,const FDamageEvent& Event,AController* Instigator,AActor* Causer) override;
    float GetHealthFraction() const { return Health/100.0f; }
    float GetStaminaFraction() const { return Stamina/100.0f; }
    float GetDamageFlash() const { return DamageFlash; }
    bool IsLockedOn() const { return bLockedOn; }
    bool IsDead() const;
    bool HasWon() const;
    bool IsEncounterActive() const { return bEncounterActive; }
    bool HasPower() const;
    FVector GetConsolePoint() const;
    bool IsInvulnerable() const;
    FString GetCombatState() const;
    FString GetPrompt() const;
    AAshWellWarden* GetWarden() const { return Warden; }
    void Attack();
    void Dodge();
    void ToggleLock();
    void Interact();
protected:
    virtual bool ShouldUpdateLocomotion() const override;
    virtual float GetLocomotionReferenceSpeed() const override { return bCombatWalkLoaded?240.0f:51.4f; }
    virtual float GetFootstepSpacing() const override { return bCombatWalkLoaded?72.0f:36.0f; }
private:
    enum class EAction : uint8 { Idle,Attack,Dodge,Hit,Dead };
    void MoveForwardCombat(float Value);
    void MoveRightCombat(float Value);
    void LookYawCombat(float Value);
    void LookPitchCombat(float Value);
    void SlowDown();
    void SlowUp();
    void SetAction(EAction Action);
    void UpdateAttack();
    void UpdateCamera(float DeltaSeconds);
    void WriteCombatSnapshot();
    void RunCombatQA(float DeltaSeconds);
    FVector InputDirection() const;
    UPROPERTY(Transient) TObjectPtr<AAshWellCombatArena> Arena;
    UPROPERTY(Transient) TObjectPtr<AAshWellWarden> Warden;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> AttackAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> DodgeAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HitAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> DeathAnimation;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> CombatCompanion;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CompanionStopAnimation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> WeaponHandle;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> WeaponHead;
    UPROPERTY(Transient) TObjectPtr<USoundBase> AttackSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> ImpactSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> DodgeSound;
    EAction ActionState=EAction::Idle;
    float StateTime=0,Health=100,Stamina=100,RegenDelay=0,DamageFlash=0;
    float ForwardInput=0,RightInput=0,SnapshotTimer=0,PowerTime=0;
    float AttackBuffer=0,DodgeBuffer=0,FeedbackTime=0;
    FVector ActionDirection=FVector::ForwardVector;
    FVector PreviousInputDirection=FVector::ForwardVector;
    FVector PreviousWeaponPosition=FVector::ZeroVector;
    int32 QACaptureIndex=0;
    bool bLockedOn=false,bEncounterActive=false,bAttackConnected=false,bCombatWalkLoaded=false,bSlow=false;
    bool bQA=false,bQAComplete=false;
    float QAElapsed=0;
    int32 AttackCount=0,HitCount=0,DodgeCount=0,DamageTakenCount=0,EvadedHits=0;
    FString Feedback;
};
