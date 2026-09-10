#include "AshWellCombatCharacter.h"
#include "AshWellCombatArena.h"
#include "AshWellWarden.h"
#include "AshWellBattleFX.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "Engine/DamageEvents.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "UnrealClient.h"
#include "Camera/CameraComponent.h"
#include "Components/WindDirectionalSourceComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"

// Explicit -CombatQA -WardenProbe=... fixtures. Never enabled for normal play.
void AAshWellCombatCharacter::RunPolishProbe(float Dt)
{
    auto Finish=[this]()
    {
        bQAComplete=true;WriteCombatSnapshot();
        const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/");
        IFileManager::Get().Copy(*(Dir+TEXT("probe-")+QAProbe+TEXT(".json")),*(Dir+TEXT("combat-runtime.json")));
        const FString Shot=FPaths::ProjectSavedDir()/TEXT("Screenshots/Polish/")+QAProbe+TEXT(".png");
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Shot),true);
        FScreenshotRequest::RequestScreenshot(Shot,true,false);
        UE_LOG(LogTemp,Display,TEXT("AW_PROBE_COMPLETE %s"),*QAProbe);
    };
    if(QAElapsed>90){Finish();return;}
    if(QAProbe==TEXT("jump_phases"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);bLockedOn=false;bEncounterActive=false;
        if(ProbeStep==0&&GetCharacterMovement()->IsMovingOnGround())
        {
            SetActorLocation(Arena->GetArenaCenter()+FVector(-500,0,90),false,nullptr,ETeleportType::TeleportPhysics);
            GetCharacterMovement()->StopMovementImmediately();SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-8,100,0));
            Jump();++ProbeStep;
        }
        JumpPhasesSeen|=1<<JumpVisualPhase;
        if(auto* I=Cast<UAnimSingleNodeInstance>(GetMesh()->GetAnimInstance()))
        {
            static float LastAirTime=-1;
            if(JumpVisualPhase==2)
            {
                if(I->GetCurrentAsset()!=JumpAirAnimation||I->IsLooping()||I->GetCurrentTime()+.005f<LastAirTime)++ProbeYawDrift;
                LastAirTime=I->GetCurrentTime();
            }
        }
        static TSet<FString> Captured;
        FString Stage;
        if(JumpVisualPhase==1)Stage=TEXT("takeoff");
        if(JumpVisualPhase==2&&FMath::Abs(GetVelocity().Z)<100)Stage=TEXT("apex");
        if(JumpVisualPhase==2&&GetVelocity().Z<-230)Stage=TEXT("descent");
        if(JumpVisualPhase==3&&JumpVisualAge>.07f)Stage=TEXT("landing");
        if(!Stage.IsEmpty()&&!Captured.Contains(Stage))
        {
            Captured.Add(Stage);WriteCombatSnapshot();
            const FString D=FPaths::ProjectSavedDir()/TEXT("JumpPolish/");
            IFileManager::Get().Copy(*(D+Stage+TEXT(".json")),*(FPaths::ProjectSavedDir()/TEXT("Automation/combat-runtime.json")));
            FScreenshotRequest::RequestScreenshot(D+Stage+TEXT(".png"),true,false);
        }
        if(ProbeStep==1&&JumpCount==1&&JumpVisualPhase==0&&GetCharacterMovement()->IsMovingOnGround()&&QAElapsed>2.5f)
        {if((JumpPhasesSeen&14)!=14)++ProbeYawDrift;++ProbeStep;Finish();}
        return;
    }
    if(QAProbe==TEXT("hero_sprint"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);
        const double RealTime=GetWorld()->GetRealTimeSeconds();
        if(ProbeStep==0&&GetCharacterMovement()->IsMovingOnGround())
        {
            SetActorLocation(Arena->GetArenaCenter()+FVector(-650,-400,90),false,nullptr,ETeleportType::TeleportPhysics);
            GetCharacterMovement()->StopMovementImmediately();SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-8,0,0));
            bLockedOn=false;bEncounterActive=false;Stamina=100;ForwardInput=1;RightInput=0;
            SprintDown();if(bSprint||DodgeCount)++ProbeYawDrift;++ProbeStep;
        }
        else if(ProbeStep==1&&RealTime-SprintPressedAt>.065)
        {
            SprintUp();if(ActionState!=EAction::Dodge||DodgeCount!=1)++ProbeYawDrift;++ProbeStep;
        }
        else if(ProbeStep==2&&ActionState==EAction::Idle){SprintDown();++ProbeStep;}
        else if(ProbeStep==3)
        {
            AddMovementInput(FVector::ForwardVector,1);
            if(RealTime-SprintPressedAt>.25&&GetVelocity().Size2D()>350)
            {if(!bSprint||DodgeCount!=1)++ProbeYawDrift;Jump();++ProbeStep;}
        }
        else if(ProbeStep==4&&GetCharacterMovement()->IsFalling())
        {SprintUp();if(bSprint||DodgeCount!=1||JumpCount!=1)++ProbeYawDrift;++ProbeStep;}
        else if(ProbeStep==5&&GetCharacterMovement()->IsMovingOnGround())
        {bLockedOn=true;SprintDown();++ProbeStep;}
        else if(ProbeStep==6)
        {
            AddMovementInput(FVector::ForwardVector,1);
            if(RealTime-SprintPressedAt>.25&&GetVelocity().Size2D()>350)
            {if(!bSprint||!bLockedOn)++ProbeYawDrift;Stamina=1;bEncounterActive=true;++ProbeStep;}
        }
        else if(ProbeStep==7)
        {
            AddMovementInput(FVector::ForwardVector,1);
            if(bSprintExhausted){if(bSprint||Stamina>.01f)++ProbeYawDrift;ProbeYaw=RealTime;++ProbeStep;}
        }
        else if(ProbeStep==8&&RealTime-ProbeYaw>.5)
        {if(bSprint)++ProbeYawDrift;SprintUp();if(DodgeCount!=1)++ProbeYawDrift;bEncounterActive=false;++ProbeStep;Finish();}
        return;
    }
    if(QAProbe==TEXT("hero_cloth"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);bLockedOn=false;bEncounterActive=false;SwordReadyTime=0;
        if(ProbeStep==0)
        {
            SetActorLocation(Arena->GetArenaCenter()+FVector(-500,0,90),false,nullptr,ETeleportType::TeleportPhysics);
            GetCharacterMovement()->StopMovementImmediately();SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-6,20,0));
            PlayCharacterAnimation(SwordIdle,true);++ProbeStep;
        }
        ActionState=EAction::Hit;StateTime=0;
        if(auto* I=Cast<UAnimSingleNodeInstance>(GetMesh()->GetAnimInstance())){I->SetPosition(.3f,false);I->SetPlaying(false);}
        if(HeroWind)HeroWind->SetSpeed(QAElapsed<4?0.f:2.5f+1.5f*FMath::Sin((QAElapsed-4)*3.f));
        if(ProbeStep==1&&QAElapsed>4){ClothMotion=0;PreviousClothPoint=FVector::ZeroVector;++ProbeStep;}
        if(QAElapsed>5&&QAElapsed<10)
        {
            const int32 Frame=FMath::FloorToInt((QAElapsed-5)*12);
            if(Frame!=QACaptureIndex){QACaptureIndex=Frame;FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/FString::Printf(TEXT("HeroComplete/WindFrames/frame-%03d.png"),Frame),false,false);}
        }
        if(QAElapsed>10){Finish();}
        return;
    }
    if(QAProbe==TEXT("hero_jump"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);bLockedOn=false;bEncounterActive=false;
        if(ProbeStep==0&&GetCharacterMovement()->IsMovingOnGround())
        {
            SetActorLocation(Arena->GetArenaCenter()+FVector(-600,0,90),false,nullptr,ETeleportType::TeleportPhysics);
            GetCharacterMovement()->StopMovementImmediately();SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-8,145,0));
            Jump();++ProbeStep;
        }
        else if(ProbeStep==1&&GetCharacterMovement()->IsFalling())
        {
            const float Before=Stamina;Jump();Dodge();
            if(IsInvulnerable()||Stamina!=Before||DodgeCount!=0)++ProbeYawDrift;
            if(JumpPeakHeight>65)
            {
                FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("HeroComplete/jump-apex.png"),true,false);++ProbeStep;
            }
        }
        else if(ProbeStep==2&&GetCharacterMovement()->IsMovingOnGround())
        {
            if(JumpCount!=1||JumpPeakHeight<65)++ProbeYawDrift;
            Stamina=100;Dodge();if(ActionState!=EAction::Dodge||Stamina!=72)++ProbeYawDrift;
            Jump();++ProbeStep;
        }
        else if(ProbeStep==3&&ActionState==EAction::Idle){if(JumpCount!=1||DodgeCount!=1)++ProbeYawDrift;Finish();}
        return;
    }
    if(QAProbe==TEXT("sword_pose"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);bLockedOn=false;bEncounterActive=false;SwordReadyTime=2;
        const int32 Index=FMath::FloorToInt((QAElapsed-1)/1.5f);if(Index>=5){Finish();return;}
        const float Positions[]={.4f,.36f,.63f,.24f,.32f};
        UAnimSequence* Clips[]={SwordGuard,AttackAnimation,HeavyAnimation,DodgeAnimation,SwordRun};
        if(ProbeStep==Index)
        {
            SetActorLocation(Arena->GetArenaCenter()+FVector(0,0,90),false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-8,145,0));
            PlayCharacterAnimation(Clips[Index],false);++ProbeStep;
        }
        ActionState=EAction::Hit;StateTime=0;GetCharacterMovement()->StopMovementImmediately();
        if(auto* I=Cast<UAnimSingleNodeInstance>(GetMesh()->GetAnimInstance())){I->SetPosition(Positions[Index],false);I->SetPlaying(false);}
        if(FMath::Fmod(QAElapsed-1,1.5f)>1.f)
        {
            static TSet<int32> Captured;
            if(!Captured.Contains(Index))
            {
                Captured.Add(Index);WriteCombatSnapshot();const FString D=FPaths::ProjectSavedDir()/TEXT("SwordPass/");
                IFileManager::Get().Copy(*(D+FString::Printf(TEXT("pose-%d.json"),Index)),*(FPaths::ProjectSavedDir()/TEXT("Automation/combat-runtime.json")));
                FScreenshotRequest::RequestScreenshot(D+FString::Printf(TEXT("pose-%d.png"),Index),true,false);
            }
        }
        return;
    }
    if(QAProbe==TEXT("sword_rules"))
    {
        if(!Warden||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);
        if(ActionState!=EAction::Idle)return;
        if(ProbeStep==0){Stamina=0;Attack();if(ActionState!=EAction::Attack||Stamina!=0)++ProbeYawDrift;++ProbeStep;}
        else if(ProbeStep==1){Stamina=0;HeavyAttack();if(ActionState!=EAction::Idle||Stamina!=0)++ProbeYawDrift;Dodge();if(ActionState!=EAction::Idle||Stamina!=0)++ProbeYawDrift;++ProbeStep;}
        else if(ProbeStep==2){Stamina=34;HeavyAttack();if(ActionState!=EAction::Heavy||Stamina!=0)++ProbeYawDrift;++ProbeStep;}
        else if(ProbeStep==3){Stamina=28;Dodge();if(ActionState!=EAction::Dodge||Stamina!=0)++ProbeYawDrift;++ProbeStep;}
        else if(ProbeStep<9){Stamina=0;Attack();if(ActionState!=EAction::Attack||Stamina!=0)++ProbeYawDrift;++ProbeStep;}
        else Finish();
        return;
    }
    if(QAProbe==TEXT("sword_locomotion"))
    {
        if(!Warden||!Arena||QAElapsed<1)return;
        Warden->ChangeState(EWellWardenState::Dormant);
        const int32 Index=FMath::FloorToInt((QAElapsed-1)/1.8f);
        if(Index>=6){Finish();return;}
        const float T=FMath::Fmod(QAElapsed-1,1.8f);
        if(ProbeStep==Index)
        {
            GetCharacterMovement()->StopMovementImmediately();SetActorLocation(Arena->GetArenaCenter()+FVector(-600,0,90),false,nullptr,ETeleportType::TeleportPhysics);SetActorRotation(FRotator::ZeroRotator);Controller->SetControlRotation(FRotator(-10,155,0));++ProbeStep;
        }
        bSlow=Index==1;bSprint=Index==3;bLockedOn=false;bEncounterActive=false;SwordReadyTime=Index>=4?2.f:0.f;
        if(Index==1||Index==2||Index==3||Index==5)AddMovementInput(FVector::ForwardVector,1);
        if(T>1.25f)
        {
            static TSet<int32> Captured;
            if(!Captured.Contains(Index))
            {
                Captured.Add(Index);WriteCombatSnapshot();
                const FString Dir=FPaths::ProjectSavedDir()/TEXT("SwordPass/");
                IFileManager::Get().Copy(*(Dir+FString::Printf(TEXT("locomotion-%d.json"),Index)),*(FPaths::ProjectSavedDir()/TEXT("Automation/combat-runtime.json")));
                FScreenshotRequest::RequestScreenshot(Dir+FString::Printf(TEXT("locomotion-%d.png"),Index),true,false);
            }
        }
        return;
    }
    if(QAProbe==TEXT("battle_camera"))
    {
        bLockedOn=true;
        const int Index=FMath::FloorToInt(QAElapsed/1.4f);
        if(Index>=5){Finish();return;}
        if(ProbeStep==Index)
        {
            const FVector C=Arena->GetArenaCenter();const auto H=Arena->GetHalfExtents();
            const FVector Points[]={Warden->GetActorLocation()+FVector(-180,0,0),C+FVector(H.X-160,-H.Y+160,0),C+FVector(H.X-160,H.Y-160,0),C+FVector(-H.X+160,H.Y-160,0),C+FVector(-H.X+160,-H.Y+160,0)};
            FVector P=Points[Index];P.Z=90;
            if(!GetWorld()->FindTeleportSpot(this,P,GetActorRotation())){ProbeYawDrift+=100;Finish();return;}
            SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);++ProbeStep;
        }
        if(FMath::Fmod(QAElapsed,1.4f)>.8f)
        {
            auto* PC=Cast<APlayerController>(Controller);FCollisionQueryParams Q(SCENE_QUERY_STAT(BattleCamera),false,this);Q.AddIgnoredActor(Warden);
            if(GetWorld()->OverlapBlockingTestByChannel(PC->PlayerCameraManager->GetCameraLocation(),FQuat::Identity,ECC_Camera,FCollisionShape::MakeSphere(8),Q))ProbeYawDrift+=Dt;
            static TSet<int32> Captured;
            if(!Captured.Contains(Index)){Captured.Add(Index);FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/FString::Printf(TEXT("Screenshots/Polish/battle-camera-%d.png"),Index),true,false);}
        }
        return;
    }
    if(QAProbe.StartsWith(TEXT("battle_")))
    {
        if(!Warden||!Arena)return;
        ProbeMinimumDilation=FMath::Min(ProbeMinimumDilation,UGameplayStatics::GetGlobalTimeDilation(GetWorld()));
        ProbeMinimumSeparation=FMath::Min(ProbeMinimumSeparation,float(FVector::Dist2D(GetActorLocation(),Warden->GetActorLocation())));
        const bool PlayerAttack=QAProbe==TEXT("battle_light")||QAProbe==TEXT("battle_heavy")||QAProbe==TEXT("battle_miss");
        const bool BodyCheck=QAProbe==TEXT("battle_body"),WallCheck=QAProbe==TEXT("battle_wall");
        if(ProbeStep==0&&QAElapsed>1)
        {
            const bool Charge=QAProbe.Contains(TEXT("charge")),Kick=QAProbe.Contains(TEXT("kick"));
            const float Distance=PlayerAttack?(QAProbe==TEXT("battle_miss")?420:190):BodyCheck?210:Charge?700:Kick?185:315;
            FVector P=Warden->GetActorLocation()+Warden->GetActorForwardVector()*Distance;P.Z=Arena->GetPlayerStart().Z;
            if(WallCheck)P=Arena->GetArenaCenter()+FVector(0,Arena->GetHalfExtents().Y-75,90);
            SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);GetCharacterMovement()->StopMovementImmediately();
            SetActorRotation((Warden->GetActorLocation()-P).Rotation());bLockedOn=true;ProbeStep=1;
            if(PlayerAttack){if(QAProbe==TEXT("battle_heavy"))HeavyAttack();else Attack();}
            else if(BodyCheck||WallCheck){Warden->ChangeState(EWellWardenState::Dormant);}
            else {Arena->PowerOn();bEncounterActive=true;Warden->ActivateEncounter(this);Warden->BeginAttack(Kick?EWellWardenAttack::Kick:Charge?EWellWardenAttack::Charge:EWellWardenAttack::Slam);}
        }
        if(ProbeStep>0)
        {
            if(PlayerAttack){if(QAElapsed>2.6f)Finish();}
            else if(BodyCheck)
            {
                AddMovementInput((Warden->GetActorLocation()-GetActorLocation()).GetSafeNormal2D(),1);
                if(QAElapsed>3.5f)Finish();
            }
            else if(WallCheck)
            {
                if(ProbeStep==1){bLockedOn=false;Controller->SetControlRotation(FRotator(0,90,0));ForwardInput=1;RightInput=0;Dodge();ForwardInput=0;ProbeStep=2;}
                if(QAElapsed>2.5f)Finish();
            }
            else
            {
                auto S=Warden->GetCombatState();
                if(S==EWellWardenState::Windup&&Warden->GetAttackProgress()>.81f)
                {
                    ProbeYaw=Warden->GetActorRotation().Yaw;
                    if(QAProbe.Contains(TEXT("dodge"))&&ProbeStep==1){ForwardInput=0;RightInput=1;Dodge();RightInput=0;ProbeStep=2;}
                }
                if(S==EWellWardenState::Strike)ProbeYawDrift=FMath::Max(ProbeYawDrift,FMath::Abs(FMath::FindDeltaAngleDegrees(ProbeYaw,Warden->GetActorRotation().Yaw)));
                if(S==EWellWardenState::Recovery&&Warden->GetStateTime()>.25f)Finish();
            }
        }
        if(QAElapsed>12)Finish();
        return;
    }

    if(QAProbe==TEXT("camera"))
    {
        bLockedOn=true;
        const FVector C=Arena->GetArenaCenter();
        const FVector Points[]={Arena->GetEnemyStart()+FVector(-125,0,90),C+FVector(560,-470,90),C+FVector(560,480,90),C+FVector(-610,500,90),C+FVector(-610,-480,90)};
        if(ProbeStep>=5){Finish();return;}
        FVector D=Points[ProbeStep]-GetActorLocation();
        if(D.Size2D()>65)AddMovementInput(D.GetSafeNormal2D(),1);
        else
        {
            const FString Shot=FPaths::ProjectSavedDir()/FString::Printf(TEXT("Screenshots/Polish/camera-%d.png"),ProbeStep);
            IFileManager::Get().MakeDirectory(*FPaths::GetPath(Shot),true);FScreenshotRequest::RequestScreenshot(Shot,true,false);++ProbeStep;
        }
        FCollisionQueryParams Q(SCENE_QUERY_STAT(CameraProbe),false,this);Q.AddIgnoredActor(Warden);
        // Sample the camera manager's completed view, not the component's
        // temporary parent-moved position before the spring arm has ticked.
        const auto* PC=Cast<APlayerController>(Controller);
        const FVector RenderedCamera=PC&&PC->PlayerCameraManager?PC->PlayerCameraManager->GetCameraLocation():FollowCamera->GetComponentLocation();
        if(QAElapsed>2&&GetWorld()->OverlapBlockingTestByChannel(RenderedCamera,FQuat::Identity,ECC_Camera,FCollisionShape::MakeSphere(8.f),Q))
            ProbeYawDrift+=Dt; // This fixture reports seconds with the camera inside collision.
        return;
    }
    if(QAProbe==TEXT("stamina"))
    {
        if(QAElapsed>1&&ActionState==EAction::Idle)
        {
            if(ProbeStep<4){Attack();++ProbeStep;}
            else {Attack();++ProbeStep;Finish();}
        }
        return;
    }
    if(QAElapsed>1&&Arena&&!Arena->IsPowered())Interact();
    if(!bEncounterActive||!Warden)return;
    bLockedOn=true;
    if(ProbeStep==0)
    {
        const float Range=QAProbe==TEXT("pursuit")?470.f:215.f;
        FVector P=Warden->GetActorLocation()+Warden->GetActorForwardVector()*Range;
        P.Z=Arena->GetPlayerStart().Z;
        SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);++ProbeStep;
    }
    if(QAProbe==TEXT("ending"))
    {
        // A declared kill fixture isolates the ending; full CombatQA wins with real attacks.
        if(!HasWon())Warden->ReceiveMeleeHit(800,GetActorLocation());
        bLockedOn=false;
        const FVector Goal=bReadRecord?Arena->GetLiftPoint():Arena->GetConsoleLocation()+FVector(-110,0,90);
        if(!Arena->IsDeparting())
        {
            FVector D=Goal-GetActorLocation();
            if(D.Size2D()>80)AddMovementInput(D.GetSafeNormal2D(),1);else Interact();
        }
        if(HasFinishedSlice()){ProbeStep=2;Finish();}
        return;
    }
    if(QAProbe==TEXT("invulnerability"))
    {
        if(ProbeStep==1&&ActionState==EAction::Idle){Dodge();++ProbeStep;}
        if(ProbeStep==2&&StateTime>.15f)
        {FDamageEvent E;TakeDamage(35,E,nullptr,Warden);++ProbeStep;Finish();}
        return;
    }
    const auto S=Warden->GetCombatState();
    if(S==EWellWardenState::Windup&&Warden->GetAttackProgress()>.85f)
    {
        ProbeYaw=Warden->GetActorRotation().Yaw;
        if(QAProbe==TEXT("dodge")&&ProbeStep==1)
        {ForwardInput=0;RightInput=1;Dodge();RightInput=0;++ProbeStep;}
    }
    if(S==EWellWardenState::Strike)
        ProbeYawDrift=FMath::Max(ProbeYawDrift,FMath::Abs(FMath::FindDeltaAngleDegrees(ProbeYaw,Warden->GetActorRotation().Yaw)));
    const int32 Expected=QAProbe==TEXT("sweep")?2:1;
    if(S==EWellWardenState::Recovery&&Warden->GetStrikeCount()>=Expected&&Warden->GetStateTime()>.2f)
        Finish();
}
