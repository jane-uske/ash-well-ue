#include "AshWellChapterDirector.h"
#include "AshWellCombatCharacter.h"
#include "AshWellCombatArena.h"
#include "AshWellSession.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"

AAshWellChapterDirector::AAshWellChapterDirector(){PrimaryActorTick.bCanEverTick=true;}
AAshWellChapterDirector* AAshWellChapterDirector::Find(UWorld* W)
{if(W){TActorIterator<AAshWellChapterDirector> It(W);if(It)return *It;}return nullptr;}
void AAshWellChapterDirector::BeginPlay()
{
    Super::BeginPlay();bQA=FParse::Param(FCommandLine::Get(),TEXT("ChapterQA"));
    if(DepartureGate)GateClosed=DepartureGate->GetActorLocation();
    CompanionWalk=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Companion_Walk.A_Intro_Companion_Walk"));
    CompanionIdle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Companion_Idle.A_Intro_Companion_Idle"));
}
bool AAshWellChapterDirector::HandleInteract(AAshWellCombatCharacter* P)
{
    if(bAtStation)return false;
    if(!bPumpFixed&&FVector::Dist2D(P->GetActorLocation(),PumpPoint)<240)
    {
        bPumpFixed=true;Caption=TEXT("闻舟：水通了。拿好检修单，我们下井。");CaptionTime=7;
        if(DepartureGate)DepartureGate->SetActorEnableCollision(false);
        UE_LOG(LogTemp,Display,TEXT("AW_CHAPTER pump_repaired gate_released"));
    }
    return true;
}
FString AAshWellChapterDirector::Prompt(const AAshWellCombatCharacter* P) const
{
    if(!bPumpFixed)return FVector::Dist2D(P->GetActorLocation(),PumpPoint)<240?TEXT("E  疏通配水泵，领取七号检修单"):TEXT("找到配水窗口旁的泵阀  ·  靠近后按 E");
    if(P->GetActorLocation().X<-7500)return TEXT("前往铁门  ·  和闻舟一起下井");
    if(P->GetActorLocation().X<-3900)return TEXT("沿着维护灯下行  ·  七号检修站");
    return TEXT("沿栈桥前往七号检修站  ·  留意对面的灯");
}
FString AAshWellChapterDirector::Subtitle() const {return CaptionTime>0?Caption:FString();}
FString AAshWellChapterDirector::Zone() const
{
    if(!Player)return TEXT("第一章 · 下井");
    const float X=Player->GetActorLocation().X;
    return bAtStation?TEXT("第一章 / 七号检修站"):X<-7500?TEXT("第一章 / 配给街"):X<-3900?TEXT("第一章 / 下行矿道"):TEXT("第一章 / 断崖栈桥");
}
void AAshWellChapterDirector::Capture(const FString& Name) const
{
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("Screenshots/Chapter01/");IFileManager::Get().MakeDirectory(*Dir,true);
    FScreenshotRequest::RequestScreenshot(Dir+Name+TEXT(".png"),true,false);
}
void AAshWellChapterDirector::Tick(float Dt)
{
    Super::Tick(Dt);Elapsed+=Dt;ReportTime+=Dt;CaptionTime=FMath::Max(0.f,CaptionTime-Dt);
    if(!Player)Player=Cast<AAshWellCombatCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));
    if(!Player||RoutePoints.Num()<2)return;
    if(!bInitialized)
    {
        bInitialized=true;PreviousPosition=Player->GetActorLocation();
        if(auto* S=Cast<UAshWellSession>(GetGameInstance()))if(S->bChapterReachedStation){bAtStation=true;bPumpFixed=true;RouteIndex=RoutePoints.Num();}
        if(bAtStation&&DepartureGate)DepartureGate->SetActorEnableCollision(false);
        if(!bAtStation){Caption=TEXT("闻舟：修好七号站，这条街就能多供三天水。");CaptionTime=9;}
    }
    if(bPumpFixed&&DepartureGate)DepartureGate->SetActorLocation(FMath::VInterpTo(DepartureGate->GetActorLocation(),GateClosed+FVector(0,0,420),Dt,1.5f));
    const FVector P=Player->GetActorLocation();
    if(!bAtStation&&P.X>2755&&P.Z<250)
    {
        bAtStation=true;RouteIndex=RoutePoints.Num();if(auto* S=Cast<UAshWellSession>(GetGameInstance()))S->bChapterReachedStation=true;
        Caption=TEXT("闻舟：里面没有回音。打开铁门，慢一点。");CaptionTime=7;
        if(Player->CombatCompanion){Player->CombatCompanion->PlayAnimation(CompanionIdle,true);Player->CombatCompanion->SetPlayRate(1.f);bCompanionWalking=false;}
        UE_LOG(LogTemp,Display,TEXT("AW_CHAPTER checkpoint_station"));
    }
    if(bQA&&bAtStation&&!Player->HasPower()&&!Player->IsEncounterActive()&&Player->Arena)
    {
        if(!Player->Arena->IsEntryOpen())
        {
            const FVector Gate=Player->Arena->GetEntryPoint();
            if(FVector::Dist2D(P,Gate)<300)Player->Interact();else Player->AddMovementInput((Gate-P).GetSafeNormal2D(),1,true);
        }
        const FVector D=Player->Arena->GetConsoleLocation()+FVector(-110,0,-10)-P;
        if(!Player->Arena->IsEntryOpen()){}else if(D.Size2D()>60)Player->AddMovementInput(D.GetSafeNormal2D(),1,true);else Player->Interact();
    }
    // Companion follows the same authored walkway, never cuts across the shaft.
    if(!bAtStation&&Player->CombatCompanion)
    {
        float Best=MAX_flt;FVector Ahead=RoutePoints[0];
        for(int32 I=0;I<RoutePoints.Num()-1;++I)
        {
            const FVector D=RoutePoints[I+1]-RoutePoints[I];const float T=FMath::Clamp(FVector::DotProduct(P-RoutePoints[I],D)/D.SizeSquared(),0.,1.);
            const FVector Q=RoutePoints[I]+D*T;const float Dist=FVector::DistSquared(P,Q);
            if(Dist<Best){Best=Dist;Ahead=RoutePoints[I]+D*FMath::Min(1.,T+240./D.Size());}
        }
        Ahead.Z-=90;const FVector From=Player->CombatCompanion->GetComponentLocation();const FVector D=Ahead-From;
        const bool Moving=D.Size()>20;
        if(From.X>0&&P.X<-7500)Player->CombatCompanion->SetWorldLocation(Ahead);
        else if(Moving){Player->CombatCompanion->SetWorldLocation(FMath::VInterpConstantTo(From,Ahead,Dt,220));Player->CombatCompanion->SetWorldRotation(FRotator(0,D.Rotation().Yaw,0));}
        if(Moving!=bCompanionWalking){bCompanionWalking=Moving;Player->CombatCompanion->PlayAnimation(Moving?CompanionWalk:CompanionIdle,true);Player->CombatCompanion->SetPlayRate(Moving?2.6f:1.f);}
    }
    if(!bAtStation&&P.X>-3900&&P.X<-3300&&Caption!=TEXT("闻舟：等等……对面那扇窗，刚才有人经过？"))
    {Caption=TEXT("闻舟：等等……对面那扇窗，刚才有人经过？");CaptionTime=8;}
    if(bQA&&!bFailed&&!bAtStation)
    {
        if(Elapsed>2&&!bPumpFixed)
        {
            const FVector D=PumpPoint-P;
            if(D.Size2D()<185)HandleInteract(Player);else Player->AddMovementInput(D.GetSafeNormal2D(),1,true);
        }
        else if(bPumpFixed&&RouteIndex<RoutePoints.Num())
        {
            const FVector D=RoutePoints[RouteIndex]-P;
            if(D.Size2D()<65&&FMath::Abs(D.Z)<65)
            {Capture(FString::Printf(TEXT("route-%02d"),RouteIndex));++RouteIndex;StuckTime=0;}
            else
            {
                Player->AddMovementInput(D.GetSafeNormal2D(),1,true);
                if(Player->GetController())Player->GetController()->SetControlRotation(FRotator(-12,D.Rotation().Yaw,0));
                if(FVector::Dist2D(P,PreviousPosition)<.2)StuckTime+=Dt;else StuckTime=0;
            }
        }
        if(StuckTime>8||P.Z<-100||Elapsed>220){bFailed=true;Failure=TEXT("Route movement stalled, fell, or timed out");WriteReport();if(FParse::Param(FCommandLine::Get(),TEXT("QAExit")))FPlatformMisc::RequestExit(false);}
    }
    PreviousPosition=P;
    if(ReportTime>1){ReportTime=0;WriteReport();}
}
void AAshWellChapterDirector::WriteReport() const
{
    if(!Player)return;
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();O->SetStringField(TEXT("map"),GetWorld()->GetMapName());O->SetBoolField(TEXT("qa"),bQA);
    O->SetNumberField(TEXT("elapsed"),Elapsed);O->SetNumberField(TEXT("route_index"),RouteIndex);O->SetNumberField(TEXT("route_points"),RoutePoints.Num());
    O->SetBoolField(TEXT("pump_fixed"),bPumpFixed);O->SetBoolField(TEXT("station_reached"),bAtStation);O->SetBoolField(TEXT("failed"),bFailed);O->SetStringField(TEXT("failure"),Failure);
    O->SetBoolField(TEXT("grounded"),Player->GetCharacterMovement()->IsMovingOnGround());O->SetBoolField(TEXT("victory"),Player->HasWon());O->SetBoolField(TEXT("chapter_complete"),Player->HasFinishedSlice());
    const FVector P=Player->GetActorLocation();O->SetNumberField(TEXT("x"),P.X);O->SetNumberField(TEXT("y"),P.Y);O->SetNumberField(TEXT("z"),P.Z);
    FString S;auto Writer=TJsonWriterFactory<>::Create(&S);FJsonSerializer::Serialize(O,Writer);
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("Chapter01/");IFileManager::Get().MakeDirectory(*Dir,true);FFileHelper::SaveStringToFile(S,*(Dir+TEXT("runtime.json")));
}
