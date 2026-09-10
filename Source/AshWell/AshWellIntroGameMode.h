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
    int32 GetSettingsRow() const { return SettingsRow; }
private:
    int32 SettingsRow=0;
    void SettingsUp();void SettingsDown();void SettingsLeft();void SettingsRight();void QuitGame();
};
UCLASS()
class ASHWELL_API AAshWellIntroGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AAshWellIntroGameMode();
};
