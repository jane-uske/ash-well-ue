#include "AshWellCombatCharacter.h"
#include "AshWellCombatArena.h"
#include "AshWellWarden.h"
#include "AshWellIntroDirector.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Sound/SoundBase.h"
#include "UnrealClient.h"

AAshWellCombatCharacter::AAshWellCombatCharacter()
{
    WeaponHandle=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CombatHammerHandle"));
    WeaponHandle->SetupAttachment(RootComponent);
    WeaponHandle->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WeaponHead=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CombatHammerHead"));
    WeaponHead->SetupAttachment(RootComponent);
    WeaponHead->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AAshWellCombatCharacter::BeginPlay()
{
    Super::BeginPlay();
    SetAutoTour(false);
    bQA=FParse::Param(FCommandLine::Get(),TEXT("CombatQA"));
    // The combat slice uses the same background, with its own safe floor and rails.
    for(TActorIterator<AActor> It(GetWorld());It;++It)
    {
        AActor* Actor=*It;
        if(Actor->IsA<AAshWellIntroDirector>()){Actor->Destroy();continue;}
        if(Actor->ActorHasTag(TEXT("AWIntroCollision_")))Actor->SetActorEnableCollision(false);
        if(AStaticMeshActor* Static=Cast<AStaticMeshActor>(Actor))
        {
            const UStaticMesh* Mesh=Static->GetStaticMeshComponent()->GetStaticMesh();
            const FString Name=Mesh?Mesh->GetName():FString();
            if(Name.Contains(TEXT("WalkwayRails"))||Name.Contains(TEXT("WalkwayEdgeBeams"))||Name.Contains(TEXT("WalkwayUnderTruss")))
            {Actor->SetActorHiddenInGame(true);Actor->SetActorEnableCollision(false);}
        }
    }
    Arena=GetWorld()->SpawnActor<AAshWellCombatArena>();
    if(Arena)
    {
        SetActorLocation(Arena->GetPlayerStart(),false,nullptr,ETeleportType::TeleportPhysics);
        FActorSpawnParameters Spawn;Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        Warden=GetWorld()->SpawnActor<AAshWellWarden>(Arena->GetEnemyStart()+FVector(0,0,135),FRotator(0,180,0),Spawn);
        if(Warden)Warden->SetArenaBounds(Arena->GetArenaCenter(),Arena->GetHalfExtents());
        CombatCompanion=NewObject<USkeletalMeshComponent>(Arena,TEXT("CompanionAtEntrance"));
        Arena->AddInstanceComponent(CombatCompanion);
        CombatCompanion->SetupAttachment(Arena->GetRootComponent());
        CombatCompanion->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Intro/Characters/SK_Intro_Companion.SK_Intro_Companion")));
        CombatCompanion->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        CombatCompanion->SetRelativeScale3D(FVector(1,-1,1));
        CombatCompanion->SetWorldLocationAndRotation(Arena->GetPlayerStart()+FVector(-130,-140,-90),FRotator(0,20,0));
        CombatCompanion->RegisterComponent();
        if(UAnimSequence* Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Companion_Idle.A_Intro_Companion_Idle")))CombatCompanion->PlayAnimation(Idle,true);
        CompanionStopAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Companion_StopSignal.A_Intro_Companion_StopSignal"));
        UPointLightComponent* Light=NewObject<UPointLightComponent>(Arena,TEXT("CompanionEntranceLantern"));
        Arena->AddInstanceComponent(Light);Light->SetupAttachment(CombatCompanion,TEXT("lamp_light_L"));
        Light->IntensityUnits=ELightUnits::Lumens;Light->SetIntensity(120);Light->SetAttenuationRadius(420);
        Light->SetLightColor(FLinearColor(1,.43,.12));Light->SetCastShadows(false);Light->RegisterComponent();
    }
    auto LoadAnimation=[](const TCHAR* Suffix)
    {
        const FString Name=FString(TEXT("A_Combat_Protagonist_"))+Suffix;
        return LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/Characters/"))+Name+TEXT(".")+Name));
    };
    AttackAnimation=LoadAnimation(TEXT("Attack"));DodgeAnimation=LoadAnimation(TEXT("Dodge"));
    HitAnimation=LoadAnimation(TEXT("Hit"));DeathAnimation=LoadAnimation(TEXT("Death"));
    if(UAnimSequence* Walk=LoadAnimation(TEXT("CombatWalk"))){WalkAnimation=Walk;bCombatWalkLoaded=true;}
    WeaponHandle->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));
    WeaponHead->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/Geometry/SM_Combat_ArmorBlock.SM_Combat_ArmorBlock")));
    WeaponHandle->SetRelativeLocation(FVector(0,25,0));
    WeaponHandle->SetRelativeRotation(FRotator(0,0,90));
    WeaponHandle->SetRelativeScale3D(FVector(.035,.035,.62));
    WeaponHead->SetRelativeLocation(FVector(0,54,0));
    WeaponHead->SetRelativeScale3D(FVector(.27,.16,.18));
    if(UMaterialInterface* Steel=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Materials/M_DarkSteel.M_DarkSteel")))
    {WeaponHandle->SetMaterial(0,Steel);WeaponHead->SetMaterial(0,Steel);}
    AttackSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Swing.AW_Combat_Swing"));
    ImpactSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Impact.AW_Combat_Impact"));
    DodgeSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Dodge.AW_Combat_Dodge"));
    GetCharacterMovement()->MaxWalkSpeed=240;
    GetCharacterMovement()->MaxAcceleration=1500;
    GetCharacterMovement()->BrakingDecelerationWalking=1800;
    CameraBoom->TargetArmLength=470;
    CameraBoom->SocketOffset=FVector(0,75,115);
    CameraBoom->CameraLagSpeed=10;
    CameraBoom->bDoCollisionTest=true;
    CameraBoom->ProbeSize=16;
    FollowCamera->FieldOfView=73;
    if(Controller)Controller->SetControlRotation(FRotator(-14,12,0));
    SetAction(EAction::Idle);
    WriteCombatSnapshot();
}

void AAshWellCombatCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    // Own bindings avoid the exploration controller overriding committed actions.
    Input->BindAxis("MoveForward",this,&AAshWellCombatCharacter::MoveForwardCombat);
    Input->BindAxis("MoveRight",this,&AAshWellCombatCharacter::MoveRightCombat);
    Input->BindAxis("Turn",this,&AAshWellCombatCharacter::LookYawCombat);
    Input->BindAxis("LookUp",this,&AAshWellCombatCharacter::LookPitchCombat);
    Input->BindKey(EKeys::LeftMouseButton,IE_Pressed,this,&AAshWellCombatCharacter::Attack);
    Input->BindKey(EKeys::SpaceBar,IE_Pressed,this,&AAshWellCombatCharacter::Dodge);
    Input->BindKey(EKeys::Tab,IE_Pressed,this,&AAshWellCombatCharacter::ToggleLock);
    Input->BindKey(EKeys::E,IE_Pressed,this,&AAshWellCombatCharacter::Interact);
    Input->BindKey(EKeys::LeftShift,IE_Pressed,this,&AAshWellCombatCharacter::SlowDown);
    Input->BindKey(EKeys::LeftShift,IE_Released,this,&AAshWellCombatCharacter::SlowUp);
}

FVector AAshWellCombatCharacter::InputDirection() const
{
    if(!Controller)return FVector::ZeroVector;
    const FRotationMatrix Basis(FRotator(0,Controller->GetControlRotation().Yaw,0));
    return (Basis.GetUnitAxis(EAxis::X)*ForwardInput+Basis.GetUnitAxis(EAxis::Y)*RightInput).GetClampedToMaxSize(1);
}
void AAshWellCombatCharacter::MoveForwardCombat(float Value)
{
    ForwardInput=Value;
    if(ActionState==EAction::Idle&&Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),Value);
}
void AAshWellCombatCharacter::MoveRightCombat(float Value)
{
    RightInput=Value;
    if(ActionState==EAction::Idle&&Controller)AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),Value);
}
void AAshWellCombatCharacter::LookYawCombat(float Value){if(!bLockedOn&&!IsDead())AddControllerYawInput(Value*1.2f);}
void AAshWellCombatCharacter::LookPitchCombat(float Value){if(!bLockedOn&&!IsDead())AddControllerPitchInput(Value*1.1f);}
void AAshWellCombatCharacter::SlowDown(){bSlow=true;GetCharacterMovement()->MaxWalkSpeed=140;}
void AAshWellCombatCharacter::SlowUp(){bSlow=false;GetCharacterMovement()->MaxWalkSpeed=240;}
bool AAshWellCombatCharacter::ShouldUpdateLocomotion() const {return ActionState==EAction::Idle;}
bool AAshWellCombatCharacter::IsDead() const {return ActionState==EAction::Dead;}
bool AAshWellCombatCharacter::HasWon() const {return Warden&&Warden->IsDead();}
bool AAshWellCombatCharacter::HasPower() const {return Arena&&Arena->IsPowered();}
FVector AAshWellCombatCharacter::GetConsolePoint() const {return Arena?Arena->GetConsoleLocation():GetActorLocation();}
bool AAshWellCombatCharacter::IsInvulnerable() const {return ActionState==EAction::Dodge&&StateTime>=.07f&&StateTime<=.37f;}

void AAshWellCombatCharacter::SetAction(EAction NewAction)
{
    ActionState=NewAction;StateTime=0;
    UAnimSequence* Animation=nullptr;
    switch(NewAction)
    {
        case EAction::Idle:Animation=IdleAnimation;break;
        case EAction::Attack:Animation=AttackAnimation;break;
        case EAction::Dodge:Animation=DodgeAnimation;break;
        case EAction::Hit:Animation=HitAnimation;break;
        case EAction::Dead:Animation=DeathAnimation;break;
    }
    if(Animation)GetMesh()->PlayAnimation(Animation,NewAction==EAction::Idle);
    if(NewAction!=EAction::Idle){GetCharacterMovement()->StopMovementImmediately();ConsumeMovementInputVector();}
}

void AAshWellCombatCharacter::Attack()
{
    if(IsDead()||HasWon())return;
    if(ActionState!=EAction::Idle)
    {
        if(ActionState==EAction::Attack&&StateTime>.68f)AttackBuffer=.18f;
        return;
    }
    if(Stamina<24){Feedback=TEXT("体力不足，拉开距离");FeedbackTime=1;return;}
    Stamina-=24;RegenDelay=.9f;++AttackCount;bAttackConnected=false;
    ActionDirection=GetActorForwardVector();
    if(bLockedOn&&Warden)ActionDirection=(Warden->GetActorLocation()-GetActorLocation()).GetSafeNormal2D();
    SetActorRotation(ActionDirection.Rotation());
    SetAction(EAction::Attack);
    if(AttackSound)UGameplayStatics::PlaySoundAtLocation(this,AttackSound,GetActorLocation(),.55f);
}
void AAshWellCombatCharacter::Dodge()
{
    if(IsDead())return;
    if(ActionState!=EAction::Idle)
    {
        if((ActionState==EAction::Attack&&StateTime>.68f)||(ActionState==EAction::Hit&&StateTime>.32f))DodgeBuffer=.18f;
        return;
    }
    if(Stamina<28){Feedback=TEXT("体力不足，无法闪避");FeedbackTime=1;return;}
    Stamina-=28;RegenDelay=.85f;++DodgeCount;
    ActionDirection=InputDirection();
    if(ActionDirection.IsNearlyZero())ActionDirection=-GetActorForwardVector();
    ActionDirection.Normalize();
    SetAction(EAction::Dodge);
    if(DodgeSound)UGameplayStatics::PlaySoundAtLocation(this,DodgeSound,GetActorLocation(),.5f);
}
void AAshWellCombatCharacter::ToggleLock()
{
    if(!IsDead()&&Warden&&!Warden->IsDead())bLockedOn=!bLockedOn;
}
void AAshWellCombatCharacter::Interact()
{
    if(!Arena||Arena->IsPowered()||IsDead())return;
    if(FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())>250)return;
    Arena->PowerOn();PowerTime=0;Feedback=TEXT("电力恢复……守井者正在苏醒");FeedbackTime=3;
    if(CombatCompanion&&CompanionStopAnimation)CombatCompanion->PlayAnimation(CompanionStopAnimation,false);
}

void AAshWellCombatCharacter::UpdateAttack()
{
    if(StateTime<.30f||StateTime>.45f||bAttackConnected||!Warden)return;
    // Sweep the visible hammer head; FBX bone scaling must not enlarge its reach.
    const FVector Start=PreviousWeaponPosition;
    const FVector End=WeaponHead->GetComponentLocation();
    FHitResult Hit;FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatHammerHit),false,this);
    if(GetWorld()->SweepSingleByChannel(Hit,Start,End,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(24),Query)&&Hit.GetActor()==Warden)
    {
        if(!bEncounterActive)
        {
            if(Arena&&!Arena->IsPowered())Arena->PowerOn();
            if(CombatCompanion&&CompanionStopAnimation)CombatCompanion->PlayAnimation(CompanionStopAnimation,false);
            bEncounterActive=true;Warden->ActivateEncounter(this);
        }
        bAttackConnected=Warden->ReceiveMeleeHit(40,GetActorLocation());
        if(bAttackConnected)
        {
            ++HitCount;
            if(ImpactSound)UGameplayStatics::PlaySoundAtLocation(this,ImpactSound,Hit.ImpactPoint,.75f);
        }
    }
}

float AAshWellCombatCharacter::TakeDamage(float Damage,const FDamageEvent& Event,AController* Instigator,AActor* Causer)
{
    if(IsDead()||HasWon()||!bEncounterActive||Damage<=0)return 0;
    if(IsInvulnerable()){++EvadedHits;return 0;}
    Health=FMath::Max(0.f,Health-Damage);DamageFlash=1;++DamageTakenCount;
    if(ImpactSound)UGameplayStatics::PlaySoundAtLocation(this,ImpactSound,GetActorLocation(),.6f,.7f);
    AttackBuffer=DodgeBuffer=0;RegenDelay=1;
    SetAction(Health<=0?EAction::Dead:EAction::Hit);
    if(Health<=0){bLockedOn=false;GetCharacterMovement()->DisableMovement();}
    return Damage;
}

void AAshWellCombatCharacter::UpdateCamera(float Dt)
{
    if(bLockedOn&&Warden&&!Warden->IsDead()&&Controller)
    {
        const FVector Direction=Warden->GetAimPoint()-GetActorLocation();
        FRotator Wanted(-13,Direction.Rotation().Yaw,0);
        Controller->SetControlRotation(FMath::RInterpTo(Controller->GetControlRotation(),Wanted,Dt,7));
        if(ActionState==EAction::Idle)SetActorRotation(FMath::RInterpTo(GetActorRotation(),FRotator(0,Wanted.Yaw,0),Dt,12));
    }
    if(HasWon())bLockedOn=false;
    CameraBoom->SocketOffset.Z=115+DamageFlash*FMath::Sin(StateTime*75)*2.5f;
}

void AAshWellCombatCharacter::Tick(float Dt)
{
    Super::Tick(Dt);
    // Imported bones can carry a unit-conversion scale. Use their location and
    // rotation only, so the 62 cm hammer stays 62 cm in world space.
    const FTransform Hand=GetMesh()->GetSocketTransform(TEXT("hand_L"),RTS_World);
    WeaponHandle->SetWorldLocationAndRotation(Hand.GetLocation()+Hand.GetRotation().RotateVector(FVector(0,25,0)),Hand.GetRotation()*FRotator(0,0,90).Quaternion());
    WeaponHandle->SetWorldScale3D(FVector(.035,.035,.62));
    WeaponHead->SetWorldLocationAndRotation(Hand.GetLocation()+Hand.GetRotation().RotateVector(FVector(0,54,0)),Hand.GetRotation());
    WeaponHead->SetWorldScale3D(FVector(.27,.16,.18));
    StateTime+=Dt;FeedbackTime=FMath::Max(0.f,FeedbackTime-Dt);
    RegenDelay=FMath::Max(0.f,RegenDelay-Dt);
    DamageFlash=FMath::Max(0.f,DamageFlash-Dt*2.8f);
    if(RegenDelay<=0&&ActionState==EAction::Idle)Stamina=FMath::Min(100.f,Stamina+26*Dt);
    if(Arena&&Arena->IsPowered()&&!bEncounterActive)
    {
        PowerTime+=Dt;
        if(CombatCompanion&&PowerTime<.8f)CombatCompanion->AddWorldOffset(FVector(-65*Dt,0,0));
        if(PowerTime>=2.7f&&Warden){bEncounterActive=true;Warden->ActivateEncounter(this);}
    }
    if(ActionState==EAction::Attack)
    {
        SetActorRotation(ActionDirection.Rotation());
        if(StateTime>=.23f&&StateTime<=.43f)AddActorWorldOffset(ActionDirection*(100*Dt),true);
        UpdateAttack();
        if(StateTime>=.8333f)SetAction(EAction::Idle);
    }
    else if(ActionState==EAction::Dodge)
    {
        GetCharacterMovement()->StopMovementImmediately();
        const float Speed=570.f*FMath::Sin(FMath::Clamp(StateTime/.5833f,0.f,1.f)*PI);
        AddActorWorldOffset(ActionDirection*Speed*Dt,true);
        if(StateTime>=.5833f)SetAction(EAction::Idle);
    }
    else if(ActionState==EAction::Hit&&StateTime>=.45f)SetAction(EAction::Idle);
    if(ActionState==EAction::Idle)
    {
        if(DodgeBuffer>0){DodgeBuffer=0;Dodge();}
        else if(AttackBuffer>0){AttackBuffer=0;Attack();}
    }
    AttackBuffer=FMath::Max(0.f,AttackBuffer-Dt);DodgeBuffer=FMath::Max(0.f,DodgeBuffer-Dt);
    UpdateCamera(Dt);
    PreviousWeaponPosition=WeaponHead->GetComponentLocation();
    if(bQA&&!bQAComplete)RunCombatQA(Dt);
    SnapshotTimer+=Dt;
    if(SnapshotTimer>=.25f){SnapshotTimer=0;WriteCombatSnapshot();}
}

FString AAshWellCombatCharacter::GetCombatState() const
{
    switch(ActionState){case EAction::Idle:return TEXT("idle");case EAction::Attack:return TEXT("attack");case EAction::Dodge:return TEXT("dodge");case EAction::Hit:return TEXT("hit");default:return TEXT("dead");}
}
FString AAshWellCombatCharacter::GetPrompt() const
{
    if(IsDead())return TEXT("R 重新挑战");
    if(HasWon())return TEXT("检修平台已安全  ·  R 再试一次");
    if(FeedbackTime>0)return Feedback;
    if(Arena&&!Arena->IsPowered())return FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())<=250?TEXT("E  拉下供电闸"):TEXT("返回供电闸按 E，或近身敲击守井者开始战斗");
    if(!bEncounterActive)return TEXT("井壁深处传来机械启动声……");
    return TEXT("观察抬锤，闪开重击，在它收招时反击");
}

void AAshWellCombatCharacter::RunCombatQA(float Dt)
{
    QAElapsed+=Dt;
    const float CaptureTimes[]={.6f,6.f,10.f,16.f};
    if(QACaptureIndex<4&&QAElapsed>=CaptureTimes[QACaptureIndex])
    {
        const FString Name=FPaths::ProjectSavedDir()/FString::Printf(TEXT("Screenshots/Combat/Combat_%02d.png"),QACaptureIndex++);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Name),true);
        FScreenshotRequest::RequestScreenshot(Name,true,false);
    }
    if(QAElapsed>1&&Arena&&!Arena->IsPowered())Interact();
    if(!bEncounterActive||!Warden)return;
    if(HasWon()||IsDead()||QAElapsed>75){bQAComplete=true;WriteCombatSnapshot();return;}
    bLockedOn=true;
    if(ActionState!=EAction::Idle)return;
    const FVector Delta=Warden->GetActorLocation()-GetActorLocation();
    const float Distance=Delta.Size2D();
    if(Warden->IsAttacking()&&Distance<355)
    {
        if(Warden->GetCombatState()==EWellWardenState::Windup&&Warden->GetAttackProgress()>.72f)
        {ForwardInput=-1;RightInput=0;Dodge();ForwardInput=0;}
    }
    else if(Warden->GetCombatState()==EWellWardenState::Recovery||Warden->GetCombatState()==EWellWardenState::Stagger)
    {
        if(Distance>150)AddMovementInput(Delta.GetSafeNormal2D(),1);
        else if(Stamina>=52)Attack(); // Keep one dodge in reserve.
    }
    else if(Distance>220)AddMovementInput(Delta.GetSafeNormal2D(),1);
}

void AAshWellCombatCharacter::WriteCombatSnapshot()
{
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();
    O->SetNumberField(TEXT("time"),GetWorld()->GetTimeSeconds());
    O->SetNumberField(TEXT("health"),Health);O->SetNumberField(TEXT("stamina"),Stamina);
    O->SetStringField(TEXT("state"),GetCombatState());
    O->SetNumberField(TEXT("state_time"),StateTime);
    O->SetBoolField(TEXT("invulnerable"),IsInvulnerable());O->SetBoolField(TEXT("locked"),bLockedOn);
    O->SetBoolField(TEXT("powered"),Arena&&Arena->IsPowered());O->SetBoolField(TEXT("encounter_active"),bEncounterActive);
    O->SetBoolField(TEXT("grounded"),GetCharacterMovement()->IsMovingOnGround());
    O->SetNumberField(TEXT("x"),GetActorLocation().X);O->SetNumberField(TEXT("y"),GetActorLocation().Y);O->SetNumberField(TEXT("z"),GetActorLocation().Z);
    O->SetNumberField(TEXT("attacks"),AttackCount);O->SetNumberField(TEXT("hits"),HitCount);O->SetNumberField(TEXT("dodges"),DodgeCount);
    O->SetNumberField(TEXT("damage_taken_count"),DamageTakenCount);O->SetNumberField(TEXT("evaded_hits"),EvadedHits);
    O->SetBoolField(TEXT("qa"),bQA);O->SetBoolField(TEXT("qa_complete"),bQAComplete);
    O->SetBoolField(TEXT("victory"),HasWon());O->SetBoolField(TEXT("combat_walk_loaded"),bCombatWalkLoaded);
    O->SetBoolField(TEXT("attack_animation_loaded"),AttackAnimation!=nullptr);O->SetBoolField(TEXT("dodge_animation_loaded"),DodgeAnimation!=nullptr);
    O->SetNumberField(TEXT("camera_boom_length"),FVector::Distance(FollowCamera->GetComponentLocation(),GetActorLocation()));
    O->SetNumberField(TEXT("hand_bone_scale"),GetMesh()->GetSocketTransform(TEXT("hand_L"),RTS_World).GetScale3D().GetAbsMax());
    if(Warden)
    {
        O->SetNumberField(TEXT("enemy_health"),Warden->GetHealth());O->SetStringField(TEXT("enemy_state"),Warden->GetStateLabel());
        O->SetNumberField(TEXT("enemy_x"),Warden->GetActorLocation().X);O->SetNumberField(TEXT("enemy_y"),Warden->GetActorLocation().Y);
        O->SetNumberField(TEXT("enemy_z"),Warden->GetActorLocation().Z);
    }
    FString Text;TSharedRef<TJsonWriter<>> Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(O,Writer);
    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/combat-runtime.json");
    FFileHelper::SaveStringToFile(Text,*(File+TEXT(".tmp")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    IFileManager::Get().Move(*File,*(File+TEXT(".tmp")),true);
}
