#include "AshWellCombatCharacter.h"
#include "AshWellMountedBoss.h"
#include "AshWellWarden.h"
#include "AshWellIntroGameMode.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/BoxComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "UnrealClient.h"
#include "Engine/DamageEvents.h"

AActor* AAshWellCombatCharacter::GetCombatEnemy() const {return MountedBoss?static_cast<AActor*>(MountedBoss.Get()):static_cast<AActor*>(Warden.Get());}
FVector AAshWellCombatCharacter::GetCombatAimPoint() const {return MountedBoss?MountedBoss->GetAimPoint():Warden?Warden->GetAimPoint():GetActorLocation();}
float AAshWellCombatCharacter::GetCombatEnemyHealthFraction() const {return MountedBoss?MountedBoss->GetHealthFraction():Warden?Warden->GetHealthFraction():0;}
FString AAshWellCombatCharacter::GetCombatEnemyName() const {return MountedBoss?(MountedBoss->IsPhaseTwo()?TEXT("暮庭骑卫 · 奋战"):TEXT("暮庭骑卫")):(Warden&&Warden->IsPhaseTwo()?TEXT("七号守井者 · 过载"):TEXT("七号守井者"));}
void AAshWellCombatCharacter::TickMountedEncounter(float Dt)
{
    if(!MountedBoss)return;
    if(!IsDead()&&!HasWon())
    {
        if(!bEncounterActive&&!MountedBoss->IsReturning()&&GetActorLocation().X>-1400&&FVector::Dist2D(GetActorLocation(),MountedBoss->GetActorLocation())<1850)
        {bEncounterActive=true;MountedBoss->ActivateEncounter(this);}
        if(bEncounterActive&&!MountedBoss->IsEncounterRunning())
        {bEncounterActive=false;bLockedOn=false;Feedback=TEXT("已脱战；骑卫与生命恢复，E 可再次挑战");FeedbackTime=3;Health=100;Stamina=100;}
        // Buffer remains a late-recovery action, never cancelling a visible damage window.
    }
    if(HasWon())bEncounterActive=false;
}
void AAshWellCombatCharacter::WriteMountedSnapshot(bool Complete)
{
    if(!GetWorld()||!GetWorld()->IsGameWorld()||!MountedBoss)return;
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();
    O->SetBoolField(TEXT("retry_observed"),MountedProbe==TEXT("retry")&&MountedQAStep==2);
    O->SetBoolField(TEXT("complete"),Complete);O->SetStringField(TEXT("probe"),MountedProbe);
    O->SetNumberField(TEXT("time"),MountedQATime);O->SetStringField(TEXT("map"),UGameplayStatics::GetCurrentLevelName(this,true));
    O->SetNumberField(TEXT("health"),Health);O->SetNumberField(TEXT("stamina"),Stamina);O->SetNumberField(TEXT("min_stamina"),MountedMinStamina);
    O->SetNumberField(TEXT("attacks"),AttackCount);O->SetNumberField(TEXT("hits"),HitCount);O->SetNumberField(TEXT("dodges"),DodgeCount);O->SetNumberField(TEXT("damage_count"),DamageTakenCount);O->SetNumberField(TEXT("evaded"),EvadedHits);
    O->SetBoolField(TEXT("hero_v02"),bHeroComplete);O->SetBoolField(TEXT("dead"),IsDead());O->SetBoolField(TEXT("won"),HasWon());O->SetBoolField(TEXT("engaged"),bEncounterActive);O->SetBoolField(TEXT("locked"),bLockedOn);
    O->SetNumberField(TEXT("min_dilation"),MountedMinDilation);O->SetNumberField(TEXT("camera_overlap_seconds"),MountedCameraOverlap);
    O->SetNumberField(TEXT("failures"),MountedQAFailures);O->SetNumberField(TEXT("minimum_separation"),ProbeMinimumSeparation);O->SetNumberField(TEXT("body_min_gap_cm"),MountedMinBodyGap);O->SetNumberField(TEXT("body_penetration_seconds"),MountedBodyPenetration);O->SetBoolField(TEXT("phase_observed"),bMountedPhaseObserved);
    O->SetNumberField(TEXT("camera_samples"),MountedCameraSamples);O->SetNumberField(TEXT("camera_visible"),MountedCameraVisible);
    O->SetNumberField(TEXT("step"),MountedQAStep);O->SetNumberField(TEXT("player_x"),GetActorLocation().X);O->SetNumberField(TEXT("player_y"),GetActorLocation().Y);O->SetNumberField(TEXT("player_z"),GetActorLocation().Z);
    O->SetStringField(TEXT("action"),GetCombatState());
    O->SetObjectField(TEXT("boss"),MountedBoss->GetTelemetry());
    FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(O,Writer);
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("MountedBoss");IFileManager::Get().MakeDirectory(*Dir,true);
    const FString File=Dir/(Complete?FString(TEXT("probe-"))+MountedProbe+TEXT(".json"):TEXT("runtime.json"));
    FFileHelper::SaveStringToFile(Text,*(File+TEXT(".tmp")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);IFileManager::Get().Move(*File,*(File+TEXT(".tmp")),true);
}
void AAshWellCombatCharacter::RunMountedQA(float Dt)
{
#if !UE_BUILD_SHIPPING
    if(!MountedBoss)return;
    static bool RetryIssued=false;
    MountedQATime+=Dt;MountedMinStamina=FMath::Min(MountedMinStamina,Stamina);MountedMinDilation=FMath::Min(MountedMinDilation,UGameplayStatics::GetGlobalTimeDilation(this));
    bMountedPhaseObserved|=MountedBoss->IsPhaseTwo();
    auto Finish=[&]()
    {
        bMountedQAComplete=true;WriteMountedSnapshot(true);
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("MountedBoss")/(MountedProbe+TEXT(".png")),true,false);
    };
    if(MountedProbe==TEXT("retry")&&RetryIssued){if(MountedQATime>.8f){MountedQAStep=2;Finish();}return;}
    FCollisionQueryParams Q(SCENE_QUERY_STAT(MountedCameraQA),false,this);Q.AddIgnoredActor(MountedBoss);
    if(GetWorld()->OverlapBlockingTestByChannel(FollowCamera->GetComponentLocation(),FQuat::Identity,ECC_Camera,FCollisionShape::MakeSphere(8),Q))MountedCameraOverlap+=Dt;
    if(FParse::Param(FCommandLine::Get(),TEXT("MountedCapture"))&&MountedQATime>1&&MountedQATime<14)
    {
        const int Frame=int((MountedQATime-1)*15);
        if(Frame>QACaptureIndex){QACaptureIndex=Frame;const FString Dir=FPaths::ProjectSavedDir()/TEXT("MountedBoss/Capture")/MountedProbe;IFileManager::Get().MakeDirectory(*Dir,true);FScreenshotRequest::RequestScreenshot(Dir/FString::Printf(TEXT("frame-%04d.png"),Frame),false,false);}
    }
    const bool NaturalCharge=MountedProbe==TEXT("natural_charge");
    const bool SampleCleanup=MountedProbe==TEXT("sample_cleanup");
    const bool Cleanup=SampleCleanup||MountedProbe==TEXT("cleanup");
    const bool HitCase=MountedProbe.StartsWith(TEXT("hit_"));
    const bool DodgeCase=MountedProbe.StartsWith(TEXT("dodge_"));
    const FString AttackName=(HitCase||DodgeCase)?MountedProbe.RightChop(HitCase?4:6):TEXT("");
    auto Place=[&](FVector P, float Yaw)
    {SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(FRotator(0,Yaw,0));GetCharacterMovement()->StopMovementImmediately();};
    if(MountedQAStep==0&&MountedQATime>.7f)
    {
        Interact();bLockedOn=true;MountedBoss->SetQAStationary(true);MountedBoss->SetActorLocation(FVector::ZeroVector);MountedBoss->SetActorRotation(FRotator::ZeroRotator);
        MountedQAStep=1;
        if(MountedProbe==TEXT("scene")){Place(FVector(-700,500,88),-25);if(Controller)Controller->SetControlRotation(FRotator(-10,-25,0));}
        else if(MountedProbe==TEXT("light")||MountedProbe==TEXT("heavy")||MountedProbe==TEXT("victory"))Place(FVector(0,150,88),-90);
        else if(MountedProbe==TEXT("miss"))Place(FVector(-750,0,88),0);
        else if(MountedProbe==TEXT("body"))Place(FVector(430,0,88),180);
        else if(NaturalCharge||MountedProbe==TEXT("loop")){Place(FVector(650,0,88),180);MountedBoss->SetQAStationary(false);}
        else if(HitCase||DodgeCase)
        {
            FVector P(230,120,88);
            if(AttackName==TEXT("overhead"))P=FVector(255,0,88);
            if(AttackName==TEXT("charge"))P=FVector(560,65,88);
            if(AttackName==TEXT("charge")&&FParse::Param(FCommandLine::Get(),TEXT("MountedChargeSample")))P.Y=105;
            if(AttackName==TEXT("body_check"))P=FVector(170,-35,88);
            if(AttackName==TEXT("rear"))P=FVector(185,130,88);
            if(AttackName==TEXT("leap_shield"))P=FVector(380,-80,88);
            Place(P,(-P).Rotation().Yaw);
        }
        else Place(FVector(-850,0,88),0);
        if(MountedProbe==TEXT("movement"))MountedBoss->SetQAStationary(false);
        if(MountedProbe==TEXT("death")){Place(FVector(230,100,88),180);MountedBoss->SetQAStationary(false);}
    }
    if(MountedQAStep==1&&MountedQATime>1.2f)
    {
        if(MountedProbe==TEXT("light")||MountedProbe==TEXT("miss")||MountedProbe==TEXT("victory")){Attack();MountedQAStep=2;}
        else if(MountedProbe==TEXT("heavy")){HeavyAttack();MountedQAStep=2;}
        else if(NaturalCharge||MountedProbe==TEXT("loop")){if(!MountedBoss->ForceAttack(TEXT("charge")))++MountedQAFailures;MountedQAStep=2;}
        else if(HitCase||DodgeCase){if(!MountedBoss->ForceAttack(AttackName))++MountedQAFailures;MountedQAStep=2;}
        else if(MountedProbe==TEXT("disengage")){MountedBoss->SetQAStationary(false);Place(FVector(-2070,0,88),0);MountedQAStep=2;}
        else if(MountedProbe==TEXT("phase")){MountedBoss->SetQAHealth(440);MountedBoss->ForceAttack(TEXT("sweep"));MountedQAStep=2;}
        else if(MountedProbe==TEXT("retry")){TakeDamage(200,FDamageEvent(),nullptr,MountedBoss);if(!IsDead())++MountedQAFailures;MountedQAStep=1;}
        else if(Cleanup){Place(FVector(1000,0,88),180);MountedBoss->ForceAttack(SampleCleanup?TEXT("charge"):TEXT("leap_shield"));MountedQAStep=2;}
        else if(MountedProbe==TEXT("sample_pre_cancel")){Place(FVector(1000,0,88),180);MountedBoss->ForceAttack(TEXT("charge"));MountedQAStep=2;}
        else if(MountedProbe==TEXT("input")){Stamina=100;Attack();Attack();HeavyAttack();if(AttackCount!=1||Stamina!=88)++MountedQAFailures;MountedQAStep=2;}
    }
    if(MountedProbe==TEXT("retry")&&IsDead()&&MountedQATime>2)
    {RetryIssued=true;if(auto* PC=Cast<AAshWellIntroPlayerController>(Controller))PC->IntroRestart();return;}
    if(NaturalCharge&&MountedBoss->GetCombatState()==EMountedBossState::Recovery)MountedBoss->SetQAStationary(true);
    if(DodgeCase&&MountedQAStep==2)
    {
        const bool RollNow=AttackName==TEXT("leap_shield")?(MountedBoss->GetCombatState()==EMountedBossState::Active&&MountedBoss->GetStateTime()>.49f):AttackName==TEXT("charge")?(MountedBoss->GetCombatState()==EMountedBossState::Active&&MountedBoss->GetStateTime()>.20f):(MountedBoss->GetCombatState()==EMountedBossState::Windup&&MountedBoss->GetStateTime()>MountedBoss->GetTelemetry()->GetNumberField(TEXT("windup_seconds"))-.13f);
        if(RollNow){if(AttackName==TEXT("charge"))RightInput=1;Dodge();RightInput=0;MountedQAStep=3;}
    }
    if(MountedProbe==TEXT("sample_pre_cancel"))
    {
        if(MountedQAStep==2&&MountedBoss->GetCombatState()==EMountedBossState::Active&&MountedBoss->GetStateTime()>.45f)
        {if(MountedBoss->IsHitWindowOpen())++MountedQAFailures;MountedBoss->DebugCancelAttack();MountedQAStep=3;}
        if(MountedQAStep==3&&MountedQATime>4.2f)
        {if(MountedBoss->GetTelemetry()->GetBoolField(TEXT("notify_window"))||MountedBoss->GetTelemetry()->GetNumberField(TEXT("window_begins"))!=0)++MountedQAFailures;MountedQAStep=4;}
    }
    if(Cleanup)
    {
        const bool InCancelWindow=SampleCleanup?MountedBoss->IsHitWindowOpen():(MountedBoss->GetCombatState()==EMountedBossState::Active&&MountedBoss->GetStateTime()>.3f);
        if(MountedQAStep==2&&InCancelWindow)
        {MountedBoss->SetDebugPaused(true);if(MountedBoss->IsHitWindowOpen())++MountedQAFailures;MountedBoss->SetDebugPaused(false);MountedBoss->DebugCancelAttack();MountedQAStep=3;}
        else if(MountedQAStep==3&&MountedQATime>3){MountedBoss->ForceAttack(SampleCleanup?TEXT("charge"):TEXT("leap_shield"));MountedQAStep=4;}
        else if(MountedQAStep==4&&InCancelWindow){MountedBoss->SetQAHealth(0);MountedQAStep=5;}
        if(MountedQAStep==5&&MountedQATime>6)
        {
            if(!MountedBoss->IsDead()||MountedBoss->GetActorLocation().Z>.5f||MountedBoss->IsHitWindowOpen())++MountedQAFailures;
            MountedBoss->ResetEncounter();MountedBoss->ReceiveMeleeHit(1,GetActorLocation(),987654);if(MountedBoss->ReceiveMeleeHit(1,GetActorLocation(),987654))++MountedQAFailures;MountedBoss->ResetEncounter();MountedQAStep=6;
        }
        if(MountedQAStep==6&&MountedQATime>7){if(MountedBoss->IsHitWindowOpen()||MountedBoss->GetTelemetry()->GetNumberField(TEXT("active_audio_components"))>0)++MountedQAFailures;MountedQAStep=7;}
    }
    if(MountedProbe==TEXT("loop")&&MountedQAStep>=2&&!IsDead()&&!HasWon())
    {
        const auto S=MountedBoss->GetCombatState();const auto K=MountedBoss->GetAttackKind();
        if(MountedQAStep==2&&S==EMountedBossState::Active&&K==EMountedBossAttack::Charge&&MountedBoss->GetStateTime()>.2f)
        {RightInput=1;Dodge();RightInput=0;MountedQAStep=3;}
        if(MountedQAStep>=3)
        {
            const FVector Delta=MountedBoss->GetActorLocation()-GetActorLocation();
            if(ActionState==EAction::Idle)
            {
                if(Delta.Size2D()>175)AddMovementInput(Delta.GetSafeNormal2D(),1);
                else if(S==EMountedBossState::Recovery||S==EMountedBossState::Approach){Attack();MountedQAStep=4;}
            }
        }
    }
    if(MountedProbe==TEXT("body")&&MountedQATime>1.2f&&MountedQATime<4.5f)
    {
        AddMovementInput(FVector(-1,0,0),1);const float Separation=FVector::Dist2D(GetActorLocation(),MountedBoss->GetActorLocation());ProbeMinimumSeparation=FMath::Min(ProbeMinimumSeparation,Separation);
        MountedMinBodyGap=FMath::Min(MountedMinBodyGap,Separation-float(MountedBoss->BodyCollision->GetScaledBoxExtent().X)-GetCapsuleComponent()->GetScaledCapsuleRadius());
        FCollisionQueryParams BodyQuery(SCENE_QUERY_STAT(MountedBodyQA),false,this);
        if(GetWorld()->OverlapBlockingTestByChannel(GetActorLocation(),GetActorQuat(),ECC_Pawn,FCollisionShape::MakeCapsule(GetCapsuleComponent()->GetScaledCapsuleRadius()-.25f,GetCapsuleComponent()->GetScaledCapsuleHalfHeight()-.25f),BodyQuery))MountedBodyPenetration+=Dt;
    }
    if(MountedProbe==TEXT("movement"))
    {
        if(MountedQATime>1&&MountedQATime<14)
        {
            const float A=MountedQATime*.18f;Place(FVector(FMath::Cos(A)*1350,FMath::Sin(A)*1150,88),180);
            Health=100;if(IsDead()){GetCharacterMovement()->SetMovementMode(MOVE_Walking);SetAction(EAction::Idle);}
        }
    }
    if(MountedProbe==TEXT("camera")&&MountedQATime>1.2f)
    {
        const int Index=FMath::Clamp(int((MountedQATime-1.2f)/2.8f),0,4);
        const FVector P[]={FVector(-250,0,88),FVector(0,200,88),FVector(900,0,88),FVector(0,-900,88),FVector(-1100,400,88)};
        Place(P[Index],(-P[Index]).Rotation().Yaw);
        if(FMath::Fmod(MountedQATime-1.2f,2.8f)>2.3f)
        {++MountedCameraSamples;FVector2D Screen;int X,Y;auto* PC=Cast<APlayerController>(Controller);PC->GetViewportSize(X,Y);if(PC->ProjectWorldLocationToScreen(MountedBoss->GetAimPoint(),Screen)&&Screen.X>20&&Screen.X<X-20&&Screen.Y>20&&Screen.Y<Y-20)++MountedCameraVisible;}
        MountedQAStep=Index+1;
    }
    if(MountedProbe==TEXT("victory")&&MountedQAStep>=2&&!HasWon()&&ActionState==EAction::Idle&&MountedQATime>2.1f)
    {Place(FVector(0,150,88),-90);Attack();++MountedQAStep;}
    if(MountedProbe==TEXT("input"))
    {
        if(MountedQAStep==2&&ActionState==EAction::Attack&&StateTime>.71f){Dodge();MountedQAStep=3;}
        if(MountedQAStep==3&&DodgeCount==1&&ActionState==EAction::Idle){if(AttackCount!=1)++MountedQAFailures;Stamina=0;Attack();HeavyAttack();Dodge();if(AttackCount!=1||DodgeCount!=1)++MountedQAFailures;MountedQAStep=4;}
    }
    const float Duration=Cleanup?8.f:MountedProbe==TEXT("loop")?90.f:(MountedProbe==TEXT("movement")||MountedProbe==TEXT("camera"))?16.f:(MountedProbe==TEXT("disengage")||MountedProbe==TEXT("death"))?20.f:MountedProbe==TEXT("victory")?35.f:6.f;
    if(MountedProbe==TEXT("victory")&&HasWon()&&EndingTime>.8f){Finish();return;}
    if(MountedProbe==TEXT("loop")&&((IsDead()&&StateTime>1.f)||(HasWon()&&EndingTime>1.f))){Finish();return;}
    if(MountedQATime>Duration)Finish();
#endif
}
