#include "AshWellIntroGameMode.h"
#include "AshWellIntroCharacter.h"
#include "AshWellCombatCharacter.h"
#include "AshWellIntroHUD.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"
#include "Components/InputComponent.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
AAshWellIntroGameMode::AAshWellIntroGameMode()
{
    DefaultPawnClass=FParse::Param(FCommandLine::Get(),TEXT("CombatPrototype"))?AAshWellCombatCharacter::StaticClass():AAshWellIntroCharacter::StaticClass();
    PlayerControllerClass=AAshWellIntroPlayerController::StaticClass();
    HUDClass=AAshWellIntroHUD::StaticClass();
}
void AAshWellIntroPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    SetControlRotation(FRotator(-5,7,0));
    bShowMouseCursor=false;
    SetInputMode(FInputModeGameOnly());
    if(PlayerCameraManager){PlayerCameraManager->ViewPitchMin=-38;PlayerCameraManager->ViewPitchMax=24;}
}
void AAshWellIntroPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    InputComponent->BindAction("Restart",IE_Pressed,this,&AAshWellIntroPlayerController::IntroRestart).bExecuteWhenPaused=true;
    InputComponent->BindAction("Tour",IE_Pressed,this,&AAshWellIntroPlayerController::IntroTour);
    InputComponent->BindAction("Pause",IE_Pressed,this,&AAshWellIntroPlayerController::TogglePause).bExecuteWhenPaused=true;
}
void AAshWellIntroPlayerController::IntroTour(){if(Cast<AAshWellCombatCharacter>(GetPawn()))return;if(auto* P=Cast<AAshWellIntroCharacter>(GetPawn()))P->SetAutoTour(!P->IsAutoTour());}
void AAshWellIntroPlayerController::IntroRestart(){UGameplayStatics::OpenLevel(this,FName(*UGameplayStatics::GetCurrentLevelName(this,true)));}
void AAshWellIntroPlayerController::TogglePause()
{
    const bool bPaused=!UGameplayStatics::IsGamePaused(this);SetPause(bPaused);bShowMouseCursor=bPaused;
    if(bPaused){SetInputMode(FInputModeGameAndUI());if(auto* H=Cast<AAshWellIntroHUD>(GetHUD()))H->SetSubtitle(TEXT("已暂停 · Esc 继续"),120);}
    else{SetInputMode(FInputModeGameOnly());if(auto* H=Cast<AAshWellIntroHUD>(GetHUD()))H->SetSubtitle(TEXT(""),0);}
}
