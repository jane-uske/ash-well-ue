#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "AshWellIntroGameMode.generated.h"
UCLASS()
class ASHWELL_API AAshWellIntroPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void SetupInputComponent() override;
    virtual void OnPossess(APawn* InPawn) override;
    UFUNCTION(Exec) void IntroTour();
    UFUNCTION(Exec) void IntroRestart();
    void TogglePause();
};
UCLASS()
class ASHWELL_API AAshWellIntroGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AAshWellIntroGameMode();
};
