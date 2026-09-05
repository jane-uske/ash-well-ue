#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AshWellIntroCharacter.generated.h"
class USpringArmComponent;
class UCameraComponent;
class UPointLightComponent;
class UAnimSequence;
class USoundBase;
class USoundAttenuation;
class UReverbEffect;
UCLASS()
class ASHWELL_API AAshWellIntroCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    AAshWellIntroCharacter();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    void SetAutoTour(bool bEnabled);
    bool IsAutoTour() const { return bAutoTour; }
    bool IsQuietWalking() const { return bQuiet; }
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> CameraBoom;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> FollowCamera;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> LanternLight;
    UPROPERTY(EditAnywhere, Category="Intro") TObjectPtr<USkeletalMesh> HeroMesh;
    UPROPERTY(EditAnywhere, Category="Intro") TObjectPtr<UAnimSequence> WalkAnimation;
    UPROPERTY(EditAnywhere, Category="Intro") TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, Category="Intro") TArray<TObjectPtr<USoundBase>> FootstepSounds;
    UPROPERTY(EditAnywhere, Category="Intro") TArray<TObjectPtr<USoundBase>> GearSounds;
protected:
    virtual bool ShouldUpdateLocomotion() const { return true; }
    virtual float GetLocomotionReferenceSpeed() const { return AnimationWalkSpeed; }
    virtual float GetFootstepSpacing() const { return 36.0f; }
private:
    static constexpr float NormalWalkSpeed = 90.0f;
    static constexpr float QuietWalkSpeed = 45.0f;
    static constexpr float AnimationWalkSpeed = 51.4f;
    UPROPERTY(Transient) TObjectPtr<USoundAttenuation> StepAttenuation;
    UPROPERTY(Transient) TObjectPtr<UReverbEffect> WellReverb;
    void MoveForward(float Value);
    void MoveRight(float Value);
    void LookYaw(float Value);
    void LookPitch(float Value);
    void QuietDown();
    void QuietUp();
    void PlayFootstep();
    void WriteTelemetry();
    bool bQuiet=false;
    bool bAutoTour=false;
    bool bWasWalking=false;
    float TourElapsed=0;
    float StepDistance=0;
    float TotalDistance=0;
    float TelemetryElapsed=0;
    float StartTime=0;
    FVector PreviousLocation=FVector::ZeroVector;
    int32 StepCount=0;
    int32 QACaptureIndex=0;
    bool bQACapture=false;
};
