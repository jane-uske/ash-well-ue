#include "AshWellBattleFX.h"
#include "AshWellCombatArena.h"
#include "Engine/World.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"

AAshWellBattleFX::AAshWellBattleFX(){PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.bTickEvenWhenPaused=true;SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));}
AAshWellBattleFX* AAshWellBattleFX::Find(UWorld* W){if(W){TActorIterator<AAshWellBattleFX> I(W);if(I)return *I;}return nullptr;}
void AAshWellBattleFX::BeginPlay()
{
 Super::BeginPlay();
 auto* Glow=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/BattlePolish/M_BattleGlow.M_BattleGlow"));
 auto* Shape=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere"));
 auto* Ring=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/BattlePolish/SM_BattleShockRing.SM_BattleShockRing"));
 for(int I=0;I<72;++I){auto* C=NewObject<UStaticMeshComponent>(this);AddInstanceComponent(C);C->SetupAttachment(RootComponent);C->SetStaticMesh(I>=64&&Ring?Ring:Shape);C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetCastShadow(false);C->SetVisibility(false);C->RegisterComponent();Bits.Add(C);auto* M=Glow?UMaterialInstanceDynamic::Create(Glow,this):nullptr;if(M)C->SetMaterial(0,M);Materials.Add(M);States.Add(FBit());}
 Flash=NewObject<UPointLightComponent>(this);AddInstanceComponent(Flash);Flash->SetupAttachment(RootComponent);Flash->IntensityUnits=ELightUnits::Lumens;Flash->SetAttenuationRadius(700);Flash->SetLightColor(FLinearColor(1,.32,.05));Flash->SetCastShadows(false);Flash->RegisterComponent();Flash->SetIntensity(0);
}
void AAshWellBattleFX::Spawn(FVector P,FVector V,float Size,float Life,bool Ring)
{
 const int I=Ring?64+(Cursor++%8):Cursor++%64;if(!Bits.IsValidIndex(I))return;
 States[I]={V,0,Life,Size,Ring};Bits[I]->SetWorldLocation(P);Bits[I]->SetWorldRotation(FRotator::ZeroRotator);Bits[I]->SetVisibility(true);Bits[I]->SetWorldScale3D(FVector(Size));if(Materials[I])Materials[I]->SetScalarParameterValue(TEXT("Alpha"),1);
}
void AAshWellBattleFX::Burst(FVector P,float Power,bool Hit,bool Finisher)
{
 if(Hit||Power>=2){TActorIterator<AAshWellCombatArena> I(GetWorld());if(I)I->DuckForImpact();}
 ++BurstCount;FlashAge=0;Flash->SetWorldLocation(P+FVector(0,0,50));Flash->SetIntensity(Power*2400);ShakeAmount=FMath::Max(ShakeAmount,FMath::Min(1.f,Power*.22f));
 for(int I=0;I<int(12*Power);++I){const float A=I*2.399963f;Spawn(P,FVector(FMath::Cos(A)*FMath::FRandRange(100.f,330.f),FMath::Sin(A)*FMath::FRandRange(100.f,330.f),FMath::FRandRange(80.f,260.f))*FMath::Sqrt(Power),.025f*FMath::FRandRange(.6,1.5),FMath::FRandRange(.16,.38),false);}
 if(Power>=2){P.Z=4;Spawn(P,FVector::ZeroVector,Power*.20f,.30f,true);}
 if(Finisher||(Hit&&Cooldown<=0)){SlowRemaining=Finisher?.65f:.075f;UGameplayStatics::SetGlobalTimeDilation(GetWorld(),Finisher?.28f:.16f);Cooldown=Finisher?2.f:.14f;}
}
void AAshWellBattleFX::Trail(FVector A,FVector B)
{
 if(FVector::DistSquared(A,B)<16)return;const FVector D=B-A;const int N=FMath::Clamp(FMath::CeilToInt(D.Size()/12),1,6);for(int I=0;I<N;++I)Spawn(FMath::Lerp(A,B,float(I)/N),FVector(0,0,-10),.018f,.065f,false);
}
void AAshWellBattleFX::Tick(float Dt)
{
 Super::Tick(Dt);const float RealDt=FMath::Clamp(float(FApp::GetDeltaTime()),0.f,.1f);Cooldown=FMath::Max(0.f,Cooldown-RealDt);ShakeAmount=FMath::Max(0.f,ShakeAmount-RealDt*3.2f);FlashAge+=RealDt;if(FlashAge>.055f)Flash->SetIntensity(FMath::Max(0.f,Flash->Intensity-RealDt*90000));
 if(SlowRemaining>0){SlowRemaining-=RealDt;if(SlowRemaining<=0)UGameplayStatics::SetGlobalTimeDilation(GetWorld(),1.f);}
 for(int I=0;I<States.Num();++I){auto& S=States[I];if(S.Age>=S.Life)continue;S.Age+=Dt;const float A=FMath::Clamp(1-S.Age/S.Life,0.f,1.f);if(S.Ring)Bits[I]->SetWorldScale3D(FVector(S.Size*(1+6*(1-A))));else {S.Velocity.Z-=700*Dt;Bits[I]->AddWorldOffset(S.Velocity*Dt);Bits[I]->SetWorldScale3D(FVector(S.Size*A,S.Size*A,S.Size*2*A));}if(Materials[I])Materials[I]->SetScalarParameterValue(TEXT("Alpha"),A);if(A<=0)Bits[I]->SetVisibility(false);}
}
void AAshWellBattleFX::EndPlay(const EEndPlayReason::Type Reason){if(SlowRemaining>0)UGameplayStatics::SetGlobalTimeDilation(GetWorld(),1.f);Super::EndPlay(Reason);}
