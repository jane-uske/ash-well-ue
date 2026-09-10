#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "AshWellSession.generated.h"

UCLASS(Config=GameUserSettings)
class ASHWELL_API UAshWellSession : public UGameInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(Config) float MasterVolume=.8f;
    UPROPERTY(Config) float MouseSensitivity=1.f;
    UPROPERTY(Config) bool bSubtitles=true;
    bool bSeenAwakening=false;
    bool bRetry=false;
    bool bChapterReachedStation=false;
    int32 Attempts=1;
    virtual void Init() override;
    void ApplyAudio(UWorld* World) const;
    void RecordFrame(float DeltaSeconds,UWorld* World);
private:
    TArray<float> FrameTimes;
    double RunStart=0,LastReport=0;
    uint64 WarmMemory=0,PeakMemory=0;
public:
    void Adjust(int32 Row,int32 Direction,UWorld* World);
};
