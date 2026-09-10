#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellBattleFX.generated.h"
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UPointLightComponent;
UCLASS()
class ASHWELL_API AAshWellBattleFX : public AActor
{
    GENERATED_BODY()
public:
    AAshWellBattleFX();
    virtual void BeginPlay() override;
    virtual void Tick(float Dt) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    static AAshWellBattleFX* Find(UWorld* W);
    void Burst(FVector P,float Power,bool Hit=false,bool Finisher=false);
    void ClearMountedEffects();
    void Trail(FVector A,FVector B);
    float Shake() const {return ShakeAmount;}
    bool IsSlowing() const {return SlowRemaining>0;}
    int32 GetBurstCount() const{return BurstCount;}
private:
    struct FBit {FVector Velocity=FVector::ZeroVector;float Age=1,Life=0,Size=1;bool Ring=false;};
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Bits;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> Materials;
    UPROPERTY(Transient) TObjectPtr<UPointLightComponent> Flash;
    TArray<FBit> States;
    int32 Cursor=0,BurstCount=0;
    float SlowRemaining=0,ShakeAmount=0,Cooldown=0,FlashAge=1;
    void Spawn(FVector P,FVector V,float Size,float Life,bool Ring);
};
