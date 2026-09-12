#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellMountedBoss.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UPoseableMeshComponent;
class UAnimSequence;
class USoundBase;
class UAudioComponent;
class FJsonObject;
class AAshWellMountedSampleRig;

UENUM()
enum class EMountedBossState : uint8 { Idle, Approach, Windup, Active, Recovery, PhaseChange, Return, Dead };
UENUM()
enum class EMountedBossAttack : uint8 { Sweep, Overhead, Charge, BodyCheck, Rear, LeapShield };

USTRUCT(BlueprintType)
struct FMountedAttackSpec
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere) float Windup=.8f;
    UPROPERTY(EditAnywhere) float Active=.32f;
    UPROPERTY(EditAnywhere) float Recovery=1.f;
    UPROPERTY(EditAnywhere) float CommitLead=.28f;
    UPROPERTY(EditAnywhere) float Damage=27.f;
    UPROPERTY(EditAnywhere) float Cooldown=2.f;
    FMountedAttackSpec()=default;
    FMountedAttackSpec(float W,float A,float R,float C,float D,float CD):Windup(W),Active(A),Recovery(R),CommitLead(C),Damage(D),Cooldown(CD){}
};

/** Independent mounted combat experiment. Actor origin is the horse's ground centre; forward is +X. */
UCLASS(Config=Game)
class ASHWELL_API AAshWellMountedBoss : public AActor
{
    GENERATED_BODY()
public:
    AAshWellMountedBoss();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    int32 GetAttackSerial() const {return AttackSerial;}
    bool IsHitWindowOpen() const;
    void DebugCancelAttack();
    void SetDebugPaused(bool bPaused);
    UPROPERTY(Config,EditAnywhere,Category="Mounted Combat") TArray<FMountedAttackSpec> AttackTuning;
    void ActivateEncounter(APawn* Player);
    bool ReceiveMeleeHit(float Damage, const FVector& Source, uint64 AttackId=0);
    void ResetEncounter();
    void SetArenaBounds(FVector Center, FVector2D HalfExtents);
    float GetHealthFraction() const { return Health / MaximumHealth; }
    float GetHealth() const { return Health; }
    bool HasSampleRig() const {return SampleRig!=nullptr;}
    float GetGroundHeight() const {return GroundHeight;}
    float GroundHeightAt(const FVector& Point) const;
    FVector GetAimPoint() const;
    bool IsDead() const { return State == EMountedBossState::Dead; }
    bool IsAttacking() const { return State == EMountedBossState::Windup || State == EMountedBossState::Active; }
    bool IsPhaseTwo() const { return bPhaseTwo; }
    bool IsComboPending() const { return bComboPending; }
    bool IsEncounterRunning() const { return State != EMountedBossState::Idle && State != EMountedBossState::Return && State != EMountedBossState::Dead; }
    bool IsReturning() const { return State == EMountedBossState::Return; }
    FString GetStateLabel() const;
    FString GetAttackLabel() const;
    float GetStateTime() const { return StateTime; }
    float GetAttackDuration() const {return Spec().Windup+Spec().Active+Spec().Recovery;}
    float GetAttackProgress() const;
    float GetSpeed() const { return Speed; }
    float GetCommittedYawDrift() const { return MaximumCommittedYawDrift; }
    int32 GetStrikeCount() const { return StrikeCount; }
    int32 GetContactCount() const { return ContactCount; }
    FVector GetWeaponTip() const { return WeaponTip; }
    FVector GetShieldPoint() const {return ShieldPoint;}
    FVector GetAttackContact() const;
    EMountedBossState GetCombatState() const { return State; }
    EMountedBossAttack GetAttackKind() const { return AttackKind; }
    bool HasHorseVisual() const { return bHorseVisual; }
    bool HasRiderVisual() const { return bRiderVisual; }
    TSharedRef<FJsonObject> GetTelemetry() const;
    FString GetTelemetryJson() const;
    // Deterministic rendered fixtures only; these return false outside explicit QA launches.
    bool ForceAttack(const FString& Name);
    void SetQAStationary(bool bStationary);
    void SetQAHealth(float NewHealth);
    FSimpleMulticastDelegate OnDefeated;

    void PlayEncounterSound(USoundBase* S,const FVector& P,float V=.5f,float Pitch=1.f){PlaySound(S,P,V,Pitch);}
    void PlayAttackSwing();
    bool ReceiveShieldContact(const FHitResult& Hit,uint64 AttackId);
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> BodyCollision;

private:
    static constexpr float MaximumHealth = 900.f;
    const FMountedAttackSpec& Spec() const;
    void ClearAttackTransient();
    void ChangeState(EMountedBossState NewState);
    void BeginAttack(EMountedBossAttack Kind, bool bFollowup = false);
    void StepCombat(float Dt);
    void StepMovement(float Dt, const FVector& Goal, float DesiredSpeed, bool bAllowTurning);
    void MoveSwept(const FVector& Delta);
    bool QueryGround(const FVector& Point,FHitResult& Hit) const;
    void RefreshGroundSupport(float DeltaSeconds);
    void SelectAttack();
    void TryDamage();
    void CacheWeaponSweepPose();
    void FinishAttack();
    void InitializeVisuals();
    void UpdatePose(float Dt);
    void UpdateHorseAnimation(float Dt);
    void UpdateRiderPose(float Dt);
    void PlaySound(USoundBase* Sound, const FVector& Point, float Volume = .5f, float Pitch = 1.f);
    bool IsQAEnabled() const;
    bool UsesAuthoredAnimation() const;

    TWeakObjectPtr<APawn> Target;
    EMountedBossState State = EMountedBossState::Idle;
    EMountedBossAttack AttackKind = EMountedBossAttack::Sweep;
    FVector Home = FVector::ZeroVector, ArenaCenter = FVector::ZeroVector;
    float GroundHeight=0;
    bool bGroundSupported=false;
    FVector GroundNormal=FVector::UpVector;
    FQuat GroundTilt=FQuat::Identity;
    FVector2D ArenaHalfExtents = FVector2D(2400,1900);
    float Health = MaximumHealth, StateTime = 0, FightTime = 0;
    float Speed = 0, ActualSpeed = 0, DistanceTravelled = 0, GaitPhase = 0, LeashTime = 0;
    float AuthoredFrameSpeed=0;
    float CommittedYaw = 0, MaximumCommittedYawDrift = 0, DecisionDelay = .7f;
    float LastHitTime = -10, HitReaction = 0, HoofDistance = 0, LastTravel = 0;
    float Cooldowns[6] = {0,0,0,0,0,0};
    int32 AttackSerial=0,BodyContactCount=0,CancelledAttacks=0,DuplicateReceiveRejected=0;
    float LeapHeight=0,MaximumLeapHeight=0;
    bool bBodyContactPending=false,bLeapLanded=false,bAudioPaused=false;
    TSet<uint64> ReceivedAttackIds;
    UPROPERTY(Transient) TArray<TObjectPtr<UAudioComponent>> ActiveAudio;
    int32 StrikeCount = 0, ContactCount = 0, SelectionCount = 0, ResetCount = 0;
    int32 WeaponContactCount = 0, AreaContactCount = 0, ShieldContactCount = 0, BlockedTurnCount = 0, BladeEdgeContactCount = 0;
    bool bPhaseTwo = false, bPhasePending = false, bComboPending = false, bFollowup = false;
    bool bHeadingCommitted = false, bDamageConsumed = false, bImpactPlayed = false, bQAStationary = false;
    bool bHorseVisual = false, bRiderVisual = false;
    FVector WeaponGrip = FVector::ZeroVector, WeaponTip = FVector::ZeroVector;
    FVector PreviousGrip = FVector::ZeroVector, PreviousTip = FVector::ZeroVector;
    FTransform PreviousWeaponTransform = FTransform::Identity;
    bool bPreviousWeaponPoseValid = false, bResetWeaponSweep = true;
    FVector ShieldPoint = FVector::ZeroVector, PreviousShield = FVector::ZeroVector;
    float RiderBob = 0, HorsePitch = 0;
    FTransform HorseSeatRestBone = FTransform::Identity;
    bool bHorseSeatBone = false;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> HorseMesh;
    UPROPERTY(Transient) TObjectPtr<AAshWellMountedSampleRig> SampleRig;
    UPROPERTY(Transient) TObjectPtr<UPoseableMeshComponent> RiderMesh;
    UPROPERTY(Transient) TObjectPtr<USceneComponent> RiderRoot;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Weapon;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Shield;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Saddle;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> FallbackHorse;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> RiderParts;
    TArray<FTransform> RiderRestTransforms;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseIdle;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseWalk;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseRun;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseRear;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseDeath;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> HorseJump;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CurrentHorseAnimation;
    float HorseAnimationTime = 0, LastAnimationDistance = 0, TurnTravel = 0, LastAnimationTurnTravel = 0, TurnSpeed = 0;
    bool bHoofGrounded[4]={true,true,true,true},bHoofPrimed=false,bHoofBonesValid=false;
    FVector PreviousHoof[4];
    float SupportDriftDistance=0,SupportSampleTime=0;
    float MinimumSampleShieldGap=MAX_flt;
    void UpdateSampleHoofContacts(float DeltaSeconds);
    int32 HoofContacts=0;
    UPROPERTY(Transient) TObjectPtr<USoundBase> SwingSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> ImpactSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> HoofSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> WeaponHitSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> BodyHitSound;
    UPROPERTY(Transient) TObjectPtr<USoundBase> ShieldBlockSound;
    int32 ShieldBlocks=0;
};
