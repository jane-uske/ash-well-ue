#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellChapterDirector.generated.h"
class AAshWellCombatCharacter;
class UAnimSequence;

/** Chapter-specific progression; combat values and attack state machine remain shared. */
UCLASS()
class ASHWELL_API AAshWellChapterDirector : public AActor
{
    GENERATED_BODY()
public:
    AAshWellChapterDirector();
    virtual void BeginPlay() override;
    virtual void Tick(float Dt) override;
    static AAshWellChapterDirector* Find(UWorld* World);
    UPROPERTY(EditAnywhere) TArray<FVector> RoutePoints;
    UPROPERTY(EditAnywhere) FVector PumpPoint=FVector(-10100,300,1600);
    UPROPERTY(EditAnywhere) TObjectPtr<AActor> DepartureGate;
    bool HandleInteract(AAshWellCombatCharacter* Player);
    bool IsAtStation() const { return bAtStation; }
    FString Prompt(const AAshWellCombatCharacter* Player) const;
    FString Subtitle() const;
    FString Zone() const;
private:
    bool bPumpFixed=false,bAtStation=false,bQA=false,bInitialized=false,bFailed=false;
    bool bCompanionWalking=false;
    float Elapsed=0,ReportTime=0,StuckTime=0,CaptionTime=0;
    int32 RouteIndex=1;
    FVector PreviousPosition=FVector::ZeroVector;
    FVector GateClosed=FVector::ZeroVector;
    FString Caption,Failure;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CompanionWalk;
    UPROPERTY(Transient) TObjectPtr<UAnimSequence> CompanionIdle;
    UPROPERTY(Transient) TObjectPtr<AAshWellCombatCharacter> Player;
    void WriteReport() const;
    void Capture(const FString& Name) const;
};
