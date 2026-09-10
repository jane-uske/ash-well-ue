#pragma once
#include "CoreMinimal.h"
#include "AshWellIntroCharacter.h"
#include "AshWellCombatCharacter.generated.h"

class AAshWellCombatArena;
class AAshWellWarden;
class AAshWellBattleFX;
class UStaticMeshComponent;
class UWindDirectionalSourceComponent;

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
    FVector GetEntryPoint() const;
    bool IsEntryClosed() const;
    bool IsInvulnerable() const;
    FString GetCombatState() const;
    FString GetPrompt() const;
    AAshWellWarden* GetWarden() const { return Warden; }
    void Attack();
    void HeavyAttack();
    void Dodge();
    virtual void Jump() override;
    virtual void Landed(const FHitResult& Hit) override;
    virtual void OnJumped_Implementation() override;
    void ToggleLock();
    void Interact();
    float GetEndingTime() const { return EndingTime; }
    bool IsRecordVisible() const { return RecordTime>0; }
    bool HasFinishedSlice() const;
    FString GetStorySubtitle() const;
protected:
    virtual void PlayCharacterAnimation(UAnimSequence* Animation,bool bLoop) override;
    virtual bool ShouldUpdateLocomotion() const override;
    virtual bool ShouldFaceMovement() const override { return !bLockedOn && ActionState==EAction::Idle; }
    virtual UAnimSequence* SelectLocomotionAnimation(float Speed) const override;
    virtual float GetLocomotionReferenceSpeed() const override;
    virtual float GetFootstepSpacing() const override { return bHeroComplete&&!bSprint&&!IsSwordReady()?(bSlow?72.f:103.f):bSwordPass?(bSprint&&!bLockedOn?67.f:IsSwordReady()||bSlow?57.f:142.f):(bCombatWalkLoaded?72.0f:36.0f); }
private:
    friend class AAshWellChapterDirector;
    enum class EAction : uint8 { Idle,Attack,Heavy,Dodge,Hit,Dead };
    void MoveForwardCombat(float Value);
    void MoveRightCombat(float Value);
    void LookYawCombat(float Value);
    void LookPitchCombat(float Value);
    void SlowDown();
    void SlowUp();
    void SprintDown();
    void SprintUp();
    bool IsSwordReady() const;
    FVector SwordPoint(float Distance) const;
    void SetAction(EAction Action);
    void UpdateAttack();
    void UpdateCamera(float DeltaSeconds);
    void WriteCombatSnapshot();
    void RunCombatQA(float DeltaSeconds);
    void RunPolishProbe(float DeltaSeconds);
    FString QAProbe;
    int32 ProbeStep=0;
    float ProbeYaw=0;
    float ProbeYawDrift=0;
    float ProbeMinimumDilation=1,ProbeMinimumSeparation=100000;
    FVector InputDirection() const;
    UPROPERTY(Transient) TObjectPtr<AAshWellCombatArena> Arena;
    UPROPERTY(Transient) TObjectPtr<AAshWellWarden> Warden;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> AttackAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HeavyAnimation;
    UPROPERTY(Transient) TObjectPtr<AAshWellBattleFX> BattleFX;
    bool bBattlePolish=false;
    bool bSwordPass=false,bSprint=false,bTravellerVisual=false,bHeroComplete=false;
    int32 ClothProbeVertex=INDEX_NONE;
    UPROPERTY(Transient) TObjectPtr<UWindDirectionalSourceComponent> HeroWind;
    float ClothMotion=0;
    FVector PreviousClothPoint=FVector::ZeroVector;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> TravellerCloak;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> SwordScabbard;
    float SwordReadyTime=0;
    FVector PreviousSwordBase=FVector::ZeroVector;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordWalk;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordRun;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordSprint;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordIdle;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordGuard;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> SwordCombatWalk;
    int32 HeavyCount=0;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> JumpAnimation;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> DodgeAnimation;
    int32 JumpCount=0;
    float JumpStartHeight=0,JumpPeakHeight=0;
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
    bool bQA=false,bQAComplete=false,bPolishedWeapon=false,bSwingAudioPlayed=false;
    float QAElapsed=0;
    float EndingTime=-1,RecordTime=0;
    bool bReadRecord=false,bSawOverload=false;
    int32 AttackCount=0,HitCount=0,DodgeCount=0,DamageTakenCount=0,EvadedHits=0;
    FString Feedback;
};
