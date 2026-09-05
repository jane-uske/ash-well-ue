#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "AshWellIntroHUD.generated.h"

class UFont;
class AAshWellCombatCharacter;

/** Small, transient captions for the First Descent opening. */
UCLASS()
class ASHWELL_API AAshWellIntroHUD : public AHUD
{
    GENERATED_BODY()

public:
    AAshWellIntroHUD();

    virtual void DrawHUD() override;

    /** Replaces the current caption; an empty string clears it immediately. */
    UFUNCTION(BlueprintCallable, Category = "First Descent|Presentation")
    void SetSubtitle(const FString& Text, float DurationSeconds = 4.0f);

    UFUNCTION(BlueprintCallable, Category = "First Descent|Presentation")
    void SetControlsVisible(bool bVisible);

    /** Elapsed opening time in seconds. A negative value resumes the world clock. */
    UFUNCTION(BlueprintCallable, Category = "First Descent|Presentation")
    void SetIntroProgress(float ElapsedSeconds);

    /** Optional runtime-cached font asset. Otherwise a CJK composite font is used. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Presentation")
    TObjectPtr<UFont> FontOverride;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "First Descent|Presentation")
    bool bShowFocusDot = false;

protected:
    virtual void BeginPlay() override;

private:
    void InitializeFont();
    void DrawCaption(const FString& Text, const FVector2D& Position, float FontSize,
                     const FLinearColor& Color, bool bCentered);
    void WriteRuntimeSnapshot() const;
    void DrawCombatHUD(AAshWellCombatCharacter* Player);
    double WorldTime() const;

    UPROPERTY(Transient)
    TObjectPtr<UFont> RuntimeCaptionFont;

    FString FontPath;
    FString Subtitle;
    FString LastDrawnCaption;
    FVector2D LastDrawnSize = FVector2D::ZeroVector;
    double IntroStartTime = 0.0;
    double SubtitleStartTime = 0.0;
    double LastSnapshotTime = -1.0;
    uint64 DrawHUDCount = 0;
    bool bBeginPlayCalled = false;
    float SubtitleDuration = 0.0f;
    float ProgressOverride = -1.0f;
    bool bControlsVisible = true;
};
