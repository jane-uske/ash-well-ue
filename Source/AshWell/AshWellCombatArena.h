#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AshWellCombatArena.generated.h"

class UAudioComponent;
class UMaterialInterface;
class UPointLightComponent;
class USceneComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;

/** A small, self-contained maintenance deck built inside the existing well. */
UCLASS()
class ASHWELL_API AAshWellCombatArena : public AActor
{
    GENERATED_BODY()

public:
    AAshWellCombatArena();
    virtual void Tick(float DeltaSeconds) override;

    /** Coordinates include the actor transform; spawn at the world origin by default. */
    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    FVector GetArenaCenter() const;

    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    FVector GetPlayerStart() const;

    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    FVector GetEnemyStart() const;

    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    FVector2D GetHalfExtents() const { return FVector2D(700.f, 650.f); }

    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    FVector GetConsoleLocation() const;

    UFUNCTION(BlueprintCallable, Category = "Combat Prototype")
    void PowerOn();

    UFUNCTION(BlueprintPure, Category = "Combat Prototype")
    bool IsPowered() const { return bPowered; }

protected:
    virtual void BeginPlay() override;

private:
    UStaticMeshComponent* AddMesh(const FString& Name, UStaticMesh* Mesh,
        const FVector& Position, const FVector& Scale, const FRotator& Rotation,
        UMaterialInterface* Material, bool bSolid = false, USceneComponent* Parent = nullptr,
        bool bMovable = false);
    UPointLightComponent* AddLamp(const FString& Name, const FVector& Position,
        const FLinearColor& Color, float Intensity, float Radius);
    void AddBarrier(const FString& Name, const FVector& Position,
        const FVector& HalfSize, const FRotator& Rotation = FRotator::ZeroRotator);
    void AddRail(const FString& Name, const FVector& Start, const FVector& End);
    void BuildDeck();
    void BuildConnection();
    void BuildSwitchgear();
    void BuildTurbine();

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(Transient)
    TObjectPtr<USceneComponent> Rotor;
    UPROPERTY(Transient)
    TObjectPtr<USceneComponent> LeverPivot;
    UPROPERTY(Transient)
    TObjectPtr<UAudioComponent> MachineryAudio;
    UPROPERTY(Transient)
    TObjectPtr<UPointLightComponent> ConsoleLamp;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UPointLightComponent>> SequenceLamps;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> Cube;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> Cylinder;
    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> Sphere;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> Steel;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> Rust;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> Stone;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> Concrete;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> Amber;
    UPROPERTY(Transient)
    TObjectPtr<USoundBase> RelaySound;
    UPROPERTY(Transient)
    TObjectPtr<USoundBase> LoadShiftSound;

    const FVector LocalCenter = FVector(3600.f, 1100.f, 0.f);
    bool bPowered = false;
    float PowerElapsed = 0.f;
    int32 RelaysFired = 0;
};
