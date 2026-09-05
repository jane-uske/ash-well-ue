#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellIntroDirector.generated.h"

class APawn;
class UAnimSequence;
class UAudioComponent;
class UPointLightComponent;
class USceneComponent;
class USkeletalMesh;
class USkeletalMeshComponent;
class USoundAttenuation;
class USoundBase;

/** The companion's short walk and listening beat. It never moves the player. */
UCLASS()
class ASHWELL_API AAshWellIntroDirector : public AActor
{
    GENERATED_BODY()

public:
    AAshWellIntroDirector();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintPure, Category = "First Descent")
    FString GetPhaseName() const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "First Descent")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "First Descent")
    TObjectPtr<USkeletalMeshComponent> CompanionVisual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "First Descent")
    TObjectPtr<UPointLightComponent> CompanionLantern;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "First Descent")
    TObjectPtr<UAudioComponent> Machinery;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "First Descent")
    TObjectPtr<UAudioComponent> Air;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    TObjectPtr<USkeletalMesh> CompanionMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    TObjectPtr<UAnimSequence> WalkAnimation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    TObjectPtr<UAnimSequence> IdleAnimation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    TObjectPtr<UAnimSequence> StopAnimation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    FVector VisualScale = FVector(1.0, -1.0, 1.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    FRotator VisualRotation = FRotator::ZeroRotator;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Companion")
    FName LanternBone = FName(TEXT("lantern"));

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Audio")
    TObjectPtr<USoundBase> MachinerySound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Audio")
    TObjectPtr<USoundBase> AirSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Audio")
    TObjectPtr<USoundBase> HushSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Audio")
    TObjectPtr<USoundBase> DistantMetalSound;

protected:
    virtual void BeginPlay() override;

private:
    enum class EIntroPhase : uint8 { Waiting, Walking, AwaitingPlayer, Hush, Listening };

    static FVector RoutePosition(float Parameter);
    void PositionCompanion();
    void BeginWalk();
    void BeginHush();
    void BeginListening();
    void SetCaption(const FString& Text, float Duration);
    void UpdateLantern();
    void WriteRuntimeSnapshot() const;
    double ElapsedTime() const;

    UPROPERTY(Transient)
    TObjectPtr<USoundAttenuation> CloseAttenuation;

    UPROPERTY(Transient)
    TObjectPtr<USoundAttenuation> DistantAttenuation;
    UPROPERTY(Transient)
    TArray<TObjectPtr<USoundBase>> CompanionSteps;

    TWeakObjectPtr<APawn> Player;
    EIntroPhase Phase = EIntroPhase::Waiting;
    float RouteParameter = 18.0f;
    float SnapshotCountdown = 0.0f;
    double StartTime = 0.0;
    double HushStartTime = 0.0;
    bool bStopPoseHeld = false;
    float FootTravel = 0.f;
    int32 FootCount = 0;
    static constexpr float MachineryVolume = 0.60f;
};
