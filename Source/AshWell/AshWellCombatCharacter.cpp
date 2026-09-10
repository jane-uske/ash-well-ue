#include "AshWellCombatCharacter.h"
#include "AshWellCombatArena.h"
#include "AshWellWarden.h"
#include "AshWellBattleFX.h"
#include "AshWellIntroGameMode.h"
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
#include "AshWellAnimInstance.h"
#include "AshWellClothAnimInstance.h"
#include "AshWellSession.h"
#include "Components/WindDirectionalSourceComponent.h"
#include "ClothingAsset.h"
#include "SkeletalRenderPublic.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "AshWellChapterDirector.h"

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
    if(auto* S=Cast<UAshWellSession>(GetGameInstance()))S->ApplyAudio(GetWorld());
    SetAutoTour(false);
    bQA=FParse::Param(FCommandLine::Get(),TEXT("CombatQA"))||FParse::Param(FCommandLine::Get(),TEXT("ChapterQA"));
    FParse::Value(FCommandLine::Get(),TEXT("WardenProbe="),QAProbe);
    if(bQA&&FParse::Param(FCommandLine::Get(),TEXT("ChapterStationQA")))if(auto* S=Cast<UAshWellSession>(GetGameInstance()))S->bChapterReachedStation=true;
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
            if(Name.Contains(TEXT("WalkwayRails"))||Name.Contains(TEXT("WalkwayEdgeBeams"))||Name.Contains(TEXT("WalkwayUnderTruss"))||(Name.Contains(TEXT("DeepBridges_And_SuspendedWalks"))&&AAshWellChapterDirector::Find(GetWorld())))
            {Actor->SetActorHiddenInGame(true);Actor->SetActorEnableCollision(false);}
        }
    }
    Arena=GetWorld()->SpawnActor<AAshWellCombatArena>();
    if(Arena)
    {
        SetActorLocation(Arena->GetPlayerStart(),false,nullptr,ETeleportType::TeleportPhysics);
        auto* Session=Cast<UAshWellSession>(GetGameInstance());
        if(!bQA&&!(Session&&Session->bRetry))SetActorLocation(Arena->GetArrivalStart(),false,nullptr,ETeleportType::TeleportPhysics);
        FActorSpawnParameters Spawn;Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        Warden=GetWorld()->SpawnActor<AAshWellWarden>(Arena->GetEnemyStart()+FVector(0,0,135),FRotator(0,180,0),Spawn);
        if(Warden&&Arena->IsGrandEncounter()){Warden->SetActorScale3D(FVector(1.5f));Warden->SetActorLocation(Arena->GetEnemyStart()+FVector(0,0,202.5f));}
        if(Warden)Warden->SetArenaBounds(Arena->GetArenaCenter(),Arena->GetHalfExtents());
        CombatCompanion=NewObject<USkeletalMeshComponent>(Arena,TEXT("CompanionAtEntrance"));
        Arena->AddInstanceComponent(CombatCompanion);
        CombatCompanion->SetupAttachment(Arena->GetRootComponent());
        CombatCompanion->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Intro/Characters/SK_Intro_Companion.SK_Intro_Companion")));
        CombatCompanion->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        CombatCompanion->SetWorldScale3D(FVector(1,-1,1));
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
    auto* FinishedHandle=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/PlayerHammer/SM_PlayerHammer_Handle.SM_PlayerHammer_Handle"));
    auto* FinishedHead=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/PlayerHammer/SM_PlayerHammer_Head.SM_PlayerHammer_Head"));
    if(FinishedHandle&&FinishedHead)
    {
        WeaponHandle->SetStaticMesh(FinishedHandle);WeaponHead->SetStaticMesh(FinishedHead);
        WeaponHandle->EmptyOverrideMaterials();WeaponHead->EmptyOverrideMaterials();bPolishedWeapon=true;
    }
    AttackSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Swing.AW_Combat_Swing"));
    ImpactSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Impact.AW_Combat_Impact"));
    DodgeSound=LoadObject<USoundBase>(nullptr,TEXT("/Game/AshWell/Combat/Audio/AW_Combat_Dodge.AW_Combat_Dodge"));
    if(!FParse::Param(FCommandLine::Get(),TEXT("BattleBaseline")))
    {
        auto LoadBattle=[](const TCHAR* Name){const FString N=FString(TEXT("A_Battle_"))+Name;return LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/BattlePolish/"))+N+TEXT(".")+N));};
        auto* Slash=LoadBattle(TEXT("Slash"));auto* Heavy=LoadBattle(TEXT("Heavy"));auto* Roll=LoadBattle(TEXT("Dodge"));auto* Reaction=LoadBattle(TEXT("Hit"));
        if(Slash&&Heavy&&Roll&&Reaction){AttackAnimation=Slash;HeavyAnimation=Heavy;DodgeAnimation=Roll;HitAnimation=Reaction;bBattlePolish=true;BattleFX=GetWorld()->SpawnActor<AAshWellBattleFX>();GetCapsuleComponent()->SetCapsuleRadius(34);}
        auto Sound=[](const TCHAR* Name){const FString N=FString(TEXT("AW_Battle_"))+Name;return LoadObject<USoundBase>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/BattlePolish/"))+N+TEXT(".")+N));};
        if(auto* A=Sound(TEXT("Swing")))AttackSound=A;if(auto* A=Sound(TEXT("MetalHit")))ImpactSound=A;if(auto* A=Sound(TEXT("Roll")))DodgeSound=A;
    }
    if(bBattlePolish&&!FParse::Param(FCommandLine::Get(),TEXT("SwordBaseline")))
    {
        auto Load=[](const TCHAR* S){const FString N=FString(TEXT("A_Sword_"))+S;return LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/SwordPass/"))+N+TEXT(".")+N));};
        SwordWalk=Load(TEXT("Walk"));SwordRun=Load(TEXT("Run"));SwordSprint=Load(TEXT("Sprint"));SwordIdle=Load(TEXT("Idle"));SwordGuard=Load(TEXT("Guard"));SwordCombatWalk=Load(TEXT("CombatWalk"));
        auto* SwordSlash=Load(TEXT("Slash"));auto* SwordHeavy=Load(TEXT("Heavy"));
        auto* Sword=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/SM_TravellerSword.SM_TravellerSword"));
        if(Sword&&SwordWalk&&SwordRun&&SwordSprint&&SwordIdle&&SwordGuard&&SwordCombatWalk&&SwordSlash&&SwordHeavy)
        {bSwordPass=true;AttackAnimation=SwordSlash;HeavyAnimation=SwordHeavy;WeaponHandle->SetStaticMesh(Sword);WeaponHandle->EmptyOverrideMaterials();WeaponHead->SetVisibility(false);IdleAnimation=SwordIdle;}
    }
    if(bSwordPass)
    {
        if(auto* Skin=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/SK_Traveller.SK_Traveller")))
        {
            GetMesh()->SetSkeletalMesh(Skin);GetMesh()->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/M_TravellerBody.M_TravellerBody")));GetMesh()->SetMaterial(1,GetMesh()->GetMaterial(0));bTravellerVisual=true;GetMesh()->SetBoundsScale(1.f);LanternLight->SetVisibility(false);
            auto* Cloak=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/SK_TravellerCloak.SK_TravellerCloak"));
            if(Cloak)
            {
                TravellerCloak=NewObject<USkeletalMeshComponent>(this,TEXT("TravellerCloak"));AddInstanceComponent(TravellerCloak);TravellerCloak->SetupAttachment(GetMesh());TravellerCloak->SetSkeletalMesh(Cloak);TravellerCloak->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/M_TravellerCloak.M_TravellerCloak")));TravellerCloak->SetMaterial(1,TravellerCloak->GetMaterial(0));TravellerCloak->SetCollisionEnabled(ECollisionEnabled::NoCollision);TravellerCloak->RegisterComponent();TravellerCloak->SetLeaderPoseComponent(GetMesh());
            }
        }
        SwordScabbard=NewObject<UStaticMeshComponent>(this,TEXT("TravellerScabbard"));AddInstanceComponent(SwordScabbard);SwordScabbard->SetupAttachment(RootComponent);SwordScabbard->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/AshWell/Combat/SwordPass/SM_TravellerScabbard.SM_TravellerScabbard")));SwordScabbard->SetCollisionEnabled(ECollisionEnabled::NoCollision);SwordScabbard->RegisterComponent();
    }
    // The centimetre-native hero is an independent asset family; retain a baseline launch switch.
    if(bSwordPass&&!FParse::Param(FCommandLine::Get(),TEXT("HeroBaseline")))
    {
        auto Load=[](const TCHAR* S){const FString N=FString(TEXT("A_Hero_"))+S;return LoadObject<UAnimSequence>(nullptr,*(FString(TEXT("/Game/AshWell/Combat/HeroComplete/"))+N+TEXT(".")+N));};
        auto* Skin=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/HeroComplete/SK_Hero.SK_Hero"));
        auto* Cloak=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Combat/HeroComplete/SK_HeroCloak.SK_HeroCloak"));
        auto* JumpClip=Load(TEXT("MeshyJump"));
        if(Skin&&Cloak&&JumpClip&&Load(TEXT("Guard"))&&Load(TEXT("Slash"))&&Load(TEXT("Heavy"))&&Load(TEXT("MeshyWalk"))&&Load(TEXT("MeshyRun"))&&Load(TEXT("MeshyIdle"))&&Load(TEXT("MeshyDodge")))
        {
            bHeroComplete=true;GetMesh()->SetSkeletalMesh(Skin);GetMesh()->SetRelativeScale3D(FVector::OneVector);GetMesh()->EmptyOverrideMaterials();
            auto* BodyMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/HeroComplete/M_HeroBody.M_HeroBody"));GetMesh()->SetMaterial(0,BodyMaterial);GetMesh()->SetMaterial(1,BodyMaterial);
            IdleAnimation=SwordIdle=Load(TEXT("Idle"));SwordWalk=Load(TEXT("MeshyWalk"));SwordRun=Load(TEXT("MeshyRun"));
            SwordSprint=Load(TEXT("Sprint"));SwordGuard=Load(TEXT("Guard"));SwordCombatWalk=Load(TEXT("CombatWalk"));
            AttackAnimation=Load(TEXT("Slash"));HeavyAnimation=Load(TEXT("Heavy"));DodgeAnimation=Load(TEXT("MeshyDodge"));JumpAnimation=JumpClip;HitAnimation=Load(TEXT("Hit"));DeathAnimation=Load(TEXT("Death"));
            if(TravellerCloak)
            {
                TravellerCloak->SetLeaderPoseComponent(nullptr);TravellerCloak->SetSkeletalMesh(Cloak);TravellerCloak->EmptyOverrideMaterials();
                auto* ClothMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/AshWell/Combat/HeroComplete/M_HeroCloth.M_HeroCloth"));TravellerCloak->SetMaterial(0,ClothMaterial);TravellerCloak->SetMaterial(1,ClothMaterial);
                TravellerCloak->SetAnimInstanceClass(UAshWellClothAnimInstance::StaticClass());TravellerCloak->AddTickPrerequisiteComponent(GetMesh());TravellerCloak->bDisableClothSimulation=false;TravellerCloak->bWaitForParallelClothTask=true;
                TravellerCloak->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
                TravellerCloak->SetClothMaxDistanceScale(1.f);TravellerCloak->ForceClothNextUpdateTeleportAndReset();
            }
            auto* Wind=NewObject<UWindDirectionalSourceComponent>(this,TEXT("TravellerWind"));HeroWind=Wind;AddInstanceComponent(Wind);Wind->SetupAttachment(RootComponent);
            Wind->SetAbsolute(false,true,false);Wind->SetWorldRotation(FRotator(0,155,0));Wind->SetStrength(.6f);Wind->SetSpeed(1.8f);Wind->RegisterComponent();
        }
    }
    GetCharacterMovement()->bEnablePhysicsInteraction=false;
    GetCharacterMovement()->MaxWalkSpeed=240;
    GetCharacterMovement()->JumpZVelocity=420;
    GetCharacterMovement()->AirControl=.28f;
    JumpMaxCount=1;JumpMaxHoldTime=0;
    GetCharacterMovement()->MaxAcceleration=1500;
    GetCharacterMovement()->BrakingDecelerationWalking=1800;
    CameraBoom->TargetArmLength=470;
    CameraBoom->SocketOffset=FVector(0,75,115);
    CameraBoom->CameraLagSpeed=10;
    CameraBoom->bDoCollisionTest=true;
    CameraBoom->ProbeSize=16;
    if(bBattlePolish){CameraBoom->TargetOffset.Z=95;CameraBoom->CameraLagMaxDistance=85;}
    FollowCamera->FieldOfView=73;
    if(Controller)Controller->SetControlRotation(FRotator(-14,12,0));
    SetAction(EAction::Idle);
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))
    {
        const auto* S=Cast<UAshWellSession>(GetGameInstance());
        if(!(S&&S->bChapterReachedStation)&&!Chapter->RoutePoints.IsEmpty())SetActorLocation(Chapter->RoutePoints[0],false,nullptr,ETeleportType::TeleportPhysics);
#if !UE_BUILD_SHIPPING
        if(FParse::Param(FCommandLine::Get(),TEXT("ChapterGatePreview"))&&Arena)
        {
            SetActorLocation(Arena->GetEntryPoint()+FVector(-270,0,0),false,nullptr,ETeleportType::TeleportPhysics);
            if(Controller)Controller->SetControlRotation(FRotator(-8,0,0));
            if(CombatCompanion)CombatCompanion->SetWorldLocation(Arena->GetEntryPoint()+FVector(-370,-120,-90));
        }
        // Explicit preview launch only; normal launches and retries retain the encounter.
        if(FParse::Param(FCommandLine::Get(),TEXT("ChapterAfterBoss"))&&Arena&&Warden&&S&&!S->bChapterReachedStation)
        {
            if(auto* Session=Cast<UAshWellSession>(GetGameInstance()))Session->bChapterReachedStation=true;
            SetActorLocation(Arena->GetPlayerStart(),false,nullptr,ETeleportType::TeleportPhysics);
            Arena->PowerOn();bEncounterActive=true;
            Warden->ActivateEncounter(this);Warden->ReceiveMeleeHit(Warden->GetHealth(),GetActorLocation());
        }
#endif
    }
    WriteCombatSnapshot();
}

void AAshWellCombatCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    if(FParse::Param(FCommandLine::Get(),TEXT("CombatQA"))||FParse::Param(FCommandLine::Get(),TEXT("ChapterQA")))return;
    // Own bindings avoid the exploration controller overriding committed actions.
    Input->BindAxis("MoveForward",this,&AAshWellCombatCharacter::MoveForwardCombat);
    Input->BindAxis("MoveRight",this,&AAshWellCombatCharacter::MoveRightCombat);
    Input->BindAxis("Turn",this,&AAshWellCombatCharacter::LookYawCombat);
    Input->BindAxis("LookUp",this,&AAshWellCombatCharacter::LookPitchCombat);
    Input->BindKey(EKeys::LeftMouseButton,IE_Pressed,this,&AAshWellCombatCharacter::Attack);
    Input->BindKey(EKeys::RightMouseButton,IE_Pressed,this,&AAshWellCombatCharacter::HeavyAttack);
    Input->BindKey(EKeys::SpaceBar,IE_Pressed,this,&AAshWellCombatCharacter::Jump);
    Input->BindKey(EKeys::SpaceBar,IE_Released,this,&AAshWellCombatCharacter::StopJumping);
    Input->BindKey(EKeys::Tab,IE_Pressed,this,&AAshWellCombatCharacter::ToggleLock);
    Input->BindKey(EKeys::E,IE_Pressed,this,&AAshWellCombatCharacter::Interact);
    Input->BindKey(EKeys::LeftControl,IE_Pressed,this,&AAshWellCombatCharacter::SlowDown);
    Input->BindKey(EKeys::LeftControl,IE_Released,this,&AAshWellCombatCharacter::SlowUp);
    Input->BindKey(EKeys::LeftShift,IE_Pressed,this,&AAshWellCombatCharacter::Dodge);
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
void AAshWellCombatCharacter::LookYawCombat(float Value){if(!bLockedOn&&!IsDead()){auto* S=Cast<UAshWellSession>(GetGameInstance());AddControllerYawInput(Value*1.2f*(S?S->MouseSensitivity:1.f));}}
void AAshWellCombatCharacter::LookPitchCombat(float Value){if(!bLockedOn&&!IsDead()){auto* S=Cast<UAshWellSession>(GetGameInstance());AddControllerPitchInput(Value*1.1f*(S?S->MouseSensitivity:1.f));}}
void AAshWellCombatCharacter::SlowDown(){bSlow=true;GetCharacterMovement()->MaxWalkSpeed=140;}
void AAshWellCombatCharacter::SlowUp(){bSlow=false;GetCharacterMovement()->MaxWalkSpeed=240;}
void AAshWellCombatCharacter::SprintDown(){bSprint=true;}
void AAshWellCombatCharacter::SprintUp(){bSprint=false;}
bool AAshWellCombatCharacter::IsSwordReady() const {return bLockedOn||(bEncounterActive&&!HasWon())||SwordReadyTime>0;}
UAnimSequence* AAshWellCombatCharacter::SelectLocomotionAnimation(float Speed) const
{
    if(!bSwordPass)return Super::SelectLocomotionAnimation(Speed);
    if(Speed<=5)return IsSwordReady()?SwordGuard.Get():SwordIdle.Get();
    if(bSprint&&!bLockedOn&&!bSlow)return SwordSprint;
    if(IsSwordReady())return SwordCombatWalk;
    return bSlow?SwordWalk.Get():SwordRun.Get();
}
float AAshWellCombatCharacter::GetLocomotionReferenceSpeed() const
{
    if(!bSwordPass)return bCombatWalkLoaded?240.f:51.4f;
    if(bSprint&&!bLockedOn&&!bSlow)return 200.f;
    if(IsSwordReady())return 86.f;
    if(bHeroComplete&&bSlow)return 140.f;
    if(bSlow)return 86.f;
    return bHeroComplete?280.f:305.f;
}
FVector AAshWellCombatCharacter::SwordPoint(float Distance) const
{
    return WeaponHandle->GetComponentTransform().TransformPosition(FVector(Distance,0,0));
}
bool AAshWellCombatCharacter::ShouldUpdateLocomotion() const {return ActionState==EAction::Idle&&!GetCharacterMovement()->IsFalling();}
bool AAshWellCombatCharacter::IsDead() const {return ActionState==EAction::Dead;}
bool AAshWellCombatCharacter::HasWon() const {return Warden&&Warden->IsDead();}
bool AAshWellCombatCharacter::HasPower() const {return Arena&&Arena->IsPowered();}
FVector AAshWellCombatCharacter::GetConsolePoint() const {return Arena?Arena->GetConsoleLocation():GetActorLocation();}
FVector AAshWellCombatCharacter::GetEntryPoint() const {return Arena?Arena->GetEntryPoint():GetActorLocation();}
bool AAshWellCombatCharacter::IsEntryClosed() const {return Arena&&!Arena->IsEntryOpen();}
bool AAshWellCombatCharacter::IsInvulnerable() const {return ActionState==EAction::Dodge&&StateTime>=.07f&&StateTime<=.37f;}

void AAshWellCombatCharacter::SetAction(EAction NewAction)
{
    ActionState=NewAction;StateTime=0;bSwingAudioPlayed=false;
    UAnimSequence* Animation=nullptr;
    switch(NewAction)
    {
        case EAction::Idle:Animation=bSwordPass?SelectLocomotionAnimation(0):IdleAnimation.Get();break;
        case EAction::Attack:Animation=AttackAnimation;break;
        case EAction::Heavy:Animation=HeavyAnimation;break;
        case EAction::Dodge:Animation=DodgeAnimation;break;
        case EAction::Hit:Animation=HitAnimation;break;
        case EAction::Dead:Animation=DeathAnimation;break;
    }
    if(NewAction==EAction::Dodge&&bBattlePolish)SetActorRotation(ActionDirection.Rotation());
    if(Animation)PlayCharacterAnimation(Animation,NewAction==EAction::Idle);
    if(NewAction!=EAction::Idle){GetCharacterMovement()->StopMovementImmediately();ConsumeMovementInputVector();}
}

void AAshWellCombatCharacter::PlayCharacterAnimation(UAnimSequence* Animation,bool bLoop)
{
    if(!Cast<UAshWellAnimInstance>(GetMesh()->GetAnimInstance()))GetMesh()->SetAnimInstanceClass(UAshWellAnimInstance::StaticClass());
    if(auto* Instance=Cast<UAshWellAnimInstance>(GetMesh()->GetAnimInstance()))
    {
        float Phase=0;
        if(bSwordPass&&bLoop&&Instance->IsLooping()&&Instance->GetLength()>0)Phase=Instance->GetCurrentTime()/Instance->GetLength();
        Instance->SetAnimationAsset(Animation,bLoop,1.f);Instance->SetPosition(Phase*Instance->GetLength(),false);Instance->SetPlaying(true);
    }
}

void AAshWellCombatCharacter::Attack()
{
    if(IsDead()||HasWon()||GetCharacterMovement()->IsFalling())return;
    if(ActionState!=EAction::Idle)
    {
        if(ActionState==EAction::Attack&&StateTime>.68f)AttackBuffer=.18f;
        return;
    }
    if(!bSwordPass)
    {
        if(Stamina<24){Feedback=TEXT("体力不足，拉开距离");FeedbackTime=1;return;}
        Stamina-=24;RegenDelay=.9f;
    }
    SwordReadyTime=4.f;++AttackCount;bAttackConnected=false;
    ActionDirection=GetActorForwardVector();
    if(bLockedOn&&Warden)ActionDirection=(Warden->GetActorLocation()-GetActorLocation()).GetSafeNormal2D();
    SetActorRotation(ActionDirection.Rotation());
    SetAction(EAction::Attack);
    if(AttackSound&&!bBattlePolish)UGameplayStatics::PlaySoundAtLocation(this,AttackSound,GetActorLocation(),.55f);
}
void AAshWellCombatCharacter::HeavyAttack()
{
    if(!bBattlePolish){Attack();return;}
    if(IsDead()||HasWon()||ActionState!=EAction::Idle||GetCharacterMovement()->IsFalling())return;
    if(Stamina<34){Feedback=TEXT("体力不足，无法重砸");FeedbackTime=1;return;}
    Stamina-=34;RegenDelay=1.f;++AttackCount;++HeavyCount;bAttackConnected=false;
    ActionDirection=bLockedOn&&Warden?(Warden->GetActorLocation()-GetActorLocation()).GetSafeNormal2D():GetActorForwardVector();
    SetActorRotation(ActionDirection.Rotation());SetAction(EAction::Heavy);

}
void AAshWellCombatCharacter::Jump()
{
    if(IsDead()||ActionState!=EAction::Idle||!GetCharacterMovement()->IsMovingOnGround())return;
    Super::Jump();
}
void AAshWellCombatCharacter::OnJumped_Implementation()
{
    Super::OnJumped_Implementation();
    ++JumpCount;JumpStartHeight=GetActorLocation().Z;JumpPeakHeight=0;
    if(JumpAnimation)PlayCharacterAnimation(JumpAnimation,false);
}
void AAshWellCombatCharacter::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);StopJumping();
    if(ActionState==EAction::Idle)PlayCharacterAnimation(SelectLocomotionAnimation(GetVelocity().Size2D()),true);
}
void AAshWellCombatCharacter::Dodge()
{
    if(IsDead()||!GetCharacterMovement()->IsMovingOnGround())return;
    if(ActionState!=EAction::Idle)
    {
        if((ActionState==EAction::Attack&&StateTime>.68f)||(ActionState==EAction::Heavy&&StateTime>.92f)||(ActionState==EAction::Hit&&StateTime>.32f))DodgeBuffer=.18f;
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
    if(IsDead())return;
    if(Arena&&Arena->OpenEntry(GetActorLocation()))return;
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))if(Chapter->HandleInteract(this))return;
    if(HasWon()&&Arena)
    {
        if(FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())<250)
        {bReadRecord=true;RecordTime=14;UE_LOG(LogTemp,Display,TEXT("AW_ENDING record_read"));return;}
        if(bReadRecord&&EndingTime>7&&FVector::Dist2D(GetActorLocation(),Arena->GetLiftPoint())<190)
        {Arena->Depart();RecordTime=0;return;}
        return;
    }
    if(Arena&&Arena->IsPowered()&&!bEncounterActive)
    {
        if(auto* S=Cast<UAshWellSession>(GetGameInstance()))if(S->bSeenAwakening)PowerTime=2.7f;
        return;
    }
    if(!Arena||Arena->IsPowered()||IsDead())return;
    if(FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())>250)return;
    Arena->PowerOn();PowerTime=0;Feedback=TEXT("电力恢复……守井者正在苏醒");FeedbackTime=3;
    if(CombatCompanion&&CompanionStopAnimation)CombatCompanion->PlayAnimation(CompanionStopAnimation,false);
}

void AAshWellCombatCharacter::UpdateAttack()
{
    const bool Heavy=ActionState==EAction::Heavy;
    if(StateTime<(Heavy?.55f:.30f)||StateTime>(Heavy?.73f:.45f)||bAttackConnected||!Warden)return;
    if(bBattlePolish&&!bSwingAudioPlayed){bSwingAudioPlayed=true;if(AttackSound)UGameplayStatics::PlaySoundAtLocation(this,AttackSound,GetActorLocation(),Heavy?.32f:.30f,Heavy?.78f:1.f);}
    if(BattleFX)BattleFX->Trail(PreviousWeaponPosition,WeaponHead->GetComponentLocation());
    // Sweep the visible hammer head; FBX bone scaling must not enlarge its reach.
    const FVector Start=PreviousWeaponPosition;
    const FVector End=WeaponHead->GetComponentLocation();
    FHitResult Hit;FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatHammerHit),false,this);
    bool Contact=false;
    if(bSwordPass)
    {
        // Sample the visible blade along its length; nearby geometry blocks each sample.
        for(int32 I=1;I<=6&&!Contact;++I)
        {
            const float A=I/6.f;
            const FVector From=FMath::Lerp(PreviousSwordBase,PreviousWeaponPosition,A);
            const FVector To=FMath::Lerp(SwordPoint(14),SwordPoint(101),A);
            Contact=GetWorld()->SweepSingleByChannel(Hit,From,To,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(7),Query)&&Hit.GetActor()==Warden;
        }
    }
    else Contact=GetWorld()->SweepSingleByChannel(Hit,Start,End,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(24),Query)&&Hit.GetActor()==Warden;
    if(Contact)
    {
        if(!bEncounterActive)
        {
            if(Arena&&!Arena->IsPowered())Arena->PowerOn();
            if(CombatCompanion&&CompanionStopAnimation)CombatCompanion->PlayAnimation(CompanionStopAnimation,false);
            bEncounterActive=true;Warden->ActivateEncounter(this);
        }
        bAttackConnected=Warden->ReceiveMeleeHit(Heavy?55.f:40.f,GetActorLocation());
        if(bAttackConnected)
        {
            ++HitCount;
            if(ImpactSound)UGameplayStatics::PlaySoundAtLocation(this,ImpactSound,Hit.ImpactPoint,bBattlePolish?1.25f:.75f);
            if(BattleFX)BattleFX->Burst(Hit.ImpactPoint,Heavy?1.8f:1.f,true,HasWon());
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
    if(BattleFX&&!IsDead())BattleFX->Burst(GetActorLocation(),.65f);
    if(Health<=0){bLockedOn=false;GetCharacterMovement()->DisableMovement();}
    return Damage;
}

void AAshWellCombatCharacter::UpdateCamera(float Dt)
{
    if(IsEntryClosed())bLockedOn=false;
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))if(!Chapter->IsAtStation())bLockedOn=false;
    if(bLockedOn&&Warden&&!Warden->IsDead()&&Controller)
    {
        const FVector Direction=Warden->GetAimPoint()-GetActorLocation();
        FRotator Wanted(Warden->GetActorScale3D().X>1.1f?-8.f:-13.f,Direction.Rotation().Yaw,0);
        Controller->SetControlRotation(FMath::RInterpTo(Controller->GetControlRotation(),Wanted,Dt,7));
        if(ActionState==EAction::Idle)SetActorRotation(FMath::RInterpTo(GetActorRotation(),FRotator(0,Wanted.Yaw,0),Dt,12));
    }
    if(HasWon())bLockedOn=false;
    const float Distance=Warden?FVector::Dist2D(GetActorLocation(),Warden->GetActorLocation()):350.f;
    const float BossScale=Warden?Warden->GetActorScale3D().X:1.f;
    const float Length=bLockedOn?FMath::GetMappedRangeValueClamped(FVector2D(130,600),FVector2D(460*BossScale,570*BossScale),Distance):470.f;
    CameraBoom->TargetArmLength=FMath::FInterpTo(CameraBoom->TargetArmLength,Length,Dt,4.f);
    CameraBoom->SocketOffset.Y=FMath::FInterpTo(CameraBoom->SocketOffset.Y,bLockedOn?40.f:75.f,Dt,5.f);
    CameraBoom->SocketOffset.Z=(bBattlePolish?20:115)+(BattleFX?BattleFX->Shake()*FMath::Sin(GetWorld()->GetRealTimeSeconds()*74)*5:0)+DamageFlash*FMath::Sin(StateTime*75)*2.5f;
}

void AAshWellCombatCharacter::Tick(float Dt)
{
    Super::Tick(Dt);
    if(GetCharacterMovement()->IsFalling())JumpPeakHeight=FMath::Max(JumpPeakHeight,GetActorLocation().Z-JumpStartHeight);
    // Imported bones can carry a unit-conversion scale. Use their location and
    // rotation only, so the 62 cm hammer stays 62 cm in world space.
    const FTransform Hand=GetMesh()->GetSocketTransform(TEXT("hand_L"),RTS_World);
    WeaponHandle->SetWorldLocationAndRotation(Hand.GetLocation()+Hand.GetRotation().RotateVector(FVector(0,25,0)),Hand.GetRotation()*FRotator(0,0,90).Quaternion());
    WeaponHandle->SetWorldScale3D(FVector(.035,.035,.62));
    WeaponHead->SetWorldLocationAndRotation(Hand.GetLocation()+Hand.GetRotation().RotateVector(FVector(0,54,0)),Hand.GetRotation());
    WeaponHead->SetWorldScale3D(FVector(.27,.16,.18));
    if(bPolishedWeapon)
    {
        WeaponHandle->SetWorldLocationAndRotation(Hand.GetLocation(),Hand.GetRotation());WeaponHandle->SetWorldScale3D(FVector::OneVector);
        WeaponHead->SetWorldScale3D(FVector::OneVector);
    }
    if(bHeroComplete&&TravellerCloak)
    {
        const auto& Assets=TravellerCloak->GetSkeletalMeshAsset()->GetMeshClothingAssets();
        if(Assets.Num())if(const auto* Cloth=Cast<UClothingAssetCommon>(Assets[0]))
        {
            FVector P;
            // A free-hem vertex measures actual solver output, not the component transform.
            if(ClothProbeVertex==INDEX_NONE){float Z=FLT_MAX;for(int32 I=0;I<Cloth->LodData[0].PhysicalMeshData.Vertices.Num();++I)if(Cloth->LodData[0].PhysicalMeshData.Vertices[I].Z<Z){Z=Cloth->LodData[0].PhysicalMeshData.Vertices[I].Z;ClothProbeVertex=I;}}
            if(TravellerCloak->GetClothSimulatedPosition_GameThread(Cloth->GetAssetGuid(),ClothProbeVertex,P))
            {
                const FVector Local=GetMesh()->GetComponentTransform().InverseTransformPosition(P);
                if(!PreviousClothPoint.IsNearlyZero())ClothMotion=FMath::Max(ClothMotion,FVector::Distance(Local,PreviousClothPoint));
                PreviousClothPoint=Local;
            }
        }
    }
    StateTime+=Dt;FeedbackTime=FMath::Max(0.f,FeedbackTime-Dt);
    RegenDelay=FMath::Max(0.f,RegenDelay-Dt);
    DamageFlash=FMath::Max(0.f,DamageFlash-Dt*2.8f);
    if(bSwordPass)
    {
        const FVector Up=(GetMesh()->GetSocketLocation(TEXT("head"))-GetMesh()->GetSocketLocation(TEXT("pelvis"))).GetSafeNormal();
        const FVector Across=(GetMesh()->GetSocketLocation(TEXT("upperarm_R"))-GetMesh()->GetSocketLocation(TEXT("upperarm_L"))).GetSafeNormal();
        const FQuat Torso=FRotationMatrix::MakeFromXZ(FVector::CrossProduct(Across,Up).GetSafeNormal(),Up).ToQuat();
        const FQuat BackRotation=Torso*FRotationMatrix::MakeFromX(FVector(0,-.48,-.88)).ToQuat();
        const FVector Back=GetMesh()->GetSocketLocation(TEXT("spine_02"))+Torso.RotateVector(FVector(-23,20,23));
        if(SwordScabbard)SwordScabbard->SetWorldLocationAndRotation(Back,BackRotation);
        const bool InHand=IsSwordReady()||ActionState==EAction::Attack||ActionState==EAction::Heavy;
        WeaponHandle->SetWorldLocationAndRotation(InHand?(Hand.GetLocation()+Hand.GetRotation().RotateVector(FVector(0,6,0))):Back,InHand?(Hand.GetRotation()*FQuat(FVector::RightVector,-PI/2)):BackRotation);WeaponHandle->SetWorldScale3D(FVector::OneVector);
        WeaponHead->SetWorldLocation(SwordPoint(101));
        SwordReadyTime=FMath::Max(0.f,SwordReadyTime-Dt);
        GetCharacterMovement()->MaxWalkSpeed=bSlow?140.f:(bSprint&&!bLockedOn?360.f:IsSwordReady()?155.f:280.f);
    }
    if(RegenDelay<=0&&ActionState==EAction::Idle)Stamina=FMath::Min(100.f,Stamina+26*Dt);
    if(Arena&&Arena->IsPowered()&&!bEncounterActive)
    {
        PowerTime+=Dt;
        if(CombatCompanion&&PowerTime<.8f)CombatCompanion->AddWorldOffset(FVector(-65*Dt,0,0));
        if(PowerTime>=2.7f&&Warden){bEncounterActive=true;Warden->ActivateEncounter(this);if(auto* S=Cast<UAshWellSession>(GetGameInstance()))S->bSeenAwakening=true;}
    }
    RecordTime=FMath::Max(0.f,RecordTime-Dt);
    if(Warden&&Warden->IsPhaseTwo()&&!bSawOverload){bSawOverload=true;if(Arena)Arena->SetOverload();}
    if(HasWon())
    {
        if(EndingTime<0){EndingTime=0;if(Arena)Arena->FinishEncounter();}
        EndingTime+=Dt;
    }
    if(ActionState==EAction::Attack)
    {
        SetActorRotation(ActionDirection.Rotation());
        if(StateTime>=.23f&&StateTime<=.43f)AddActorWorldOffset(ActionDirection*(100*Dt),true);
        UpdateAttack();
        if(StateTime>=.8333f)SetAction(EAction::Idle);
    }
    else if(ActionState==EAction::Heavy)
    {
        SetActorRotation(ActionDirection.Rotation());
        if(StateTime>=.50f&&StateTime<=.70f)AddActorWorldOffset(ActionDirection*(95*Dt),true);
        UpdateAttack();if(StateTime>=1.10f)SetAction(EAction::Idle);
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
    PreviousSwordBase=bSwordPass?SwordPoint(14):PreviousWeaponPosition;
    if(bQA&&!bQAComplete)RunCombatQA(Dt);
    if(bQA)if(auto* S=Cast<UAshWellSession>(GetGameInstance()))S->RecordFrame(Dt,GetWorld());
    SnapshotTimer+=Dt;
    if(SnapshotTimer>=.25f){SnapshotTimer=0;WriteCombatSnapshot();}
}

FString AAshWellCombatCharacter::GetCombatState() const
{
    switch(ActionState){case EAction::Idle:return TEXT("idle");case EAction::Attack:return TEXT("attack");case EAction::Heavy:return TEXT("heavy");case EAction::Dodge:return TEXT("dodge");case EAction::Hit:return TEXT("hit");default:return TEXT("dead");}
}
FString AAshWellCombatCharacter::GetPrompt() const
{
    if(IsDead())return TEXT("R 重新挑战");
    if(Arena&&Arena->IsGrandEncounter()&&!Arena->IsEntryOpen()&&AAshWellChapterDirector::Find(GetWorld())->IsAtStation())return TEXT("靠近七号检修站铁门按 E  ·  开门后进入供电大厅");
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))
    {
        if(HasFinishedSlice())return TEXT("第一章 · 下井  完成  |  下一站：无名工区  |  R 重试检修站");
        if(!Chapter->IsAtStation())return Chapter->Prompt(this);
    }
    if(HasFinishedSlice())return TEXT("升降机正在驶向下一层  ·  感谢体验  ·  R 再次挑战");
    if(HasWon())
    {
        if(EndingTime<7)return TEXT("机械终于安静下来……");
        if(!bReadRecord)return TEXT("供电台上还有一份记录  ·  靠近后按 E 查看");
        return TEXT("前往蓝灯下的升降机  ·  E 下行");
    }
    if(FeedbackTime>0)return Feedback;
    if(Arena&&!Arena->IsPowered())return FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())<=250?TEXT("E  拉下供电闸"):TEXT("返回供电闸按 E，或近身敲击守井者开始战斗");
    if(!bEncounterActive)
    {auto* S=Cast<UAshWellSession>(GetGameInstance());return S&&S->bSeenAwakening?TEXT("E 跳过唤醒演出"):TEXT("井壁深处传来机械启动声……");}
    if(Warden&&Warden->GetCombatState()==EWellWardenState::Overload)return TEXT("限流器失效——注意它接下来的动作");
    if(Warden&&Warden->IsComboPending())return TEXT("它还没有收锤……");
    return TEXT("看清起手，留住体力，在它收招时反击");
}

bool AAshWellCombatCharacter::HasFinishedSlice() const { return Arena&&Arena->HasDeparted(); }
FString AAshWellCombatCharacter::GetStorySubtitle() const
{
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))
    {if(HasWon()&&EndingTime>=2.f&&EndingTime<7.f)return TEXT("守井者：别……再送电了。");return Chapter->Subtitle();}
    if(HasWon()&&EndingTime>=2.f&&EndingTime<7.f)return TEXT("守井者：别……再送电了。");
    if(!HasPower()&&GetWorld()->GetTimeSeconds()<14.f)return TEXT("同伴：检修站没有回音。先看看供电台。");
    return FString();
}

void AAshWellCombatCharacter::RunCombatQA(float Dt)
{
    if(auto* Chapter=AAshWellChapterDirector::Find(GetWorld()))if(!Chapter->IsAtStation())return;
    QAElapsed+=Dt;
    if(!QAProbe.IsEmpty()){RunPolishProbe(Dt);return;}
    // Optional unattended death/restart regression, using the same interaction
    // and controller restart functions bound to E and R in the manual build.
    if(FParse::Param(FCommandLine::Get(),TEXT("WardenDeathQA")))
    {
        static bool Restarted=false;
        if(Restarted)
        {
            bQAComplete=true;WriteCombatSnapshot();
            const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/");
            IFileManager::Get().Copy(*(Dir+TEXT("warden-reset-result.json")),*(Dir+TEXT("combat-runtime.json")));
            if(FParse::Param(FCommandLine::Get(),TEXT("QAExit")))FPlatformMisc::RequestExit(false);
            return;
        }
        if(QAElapsed>1 && Arena && !Arena->IsPowered())Interact();
        if(bEncounterActive && !bLockedOn && !IsDead())ToggleLock();
        if(bEncounterActive&&ProbeStep==0&&Warden)
        {
            // Place the death fixture in the open; the console physically blocks low weapon sweeps.
            FVector P=Warden->GetActorLocation()+Warden->GetActorForwardVector()*185;P.Z=90;
            SetActorLocation(P,false,nullptr,ETeleportType::TeleportPhysics);ProbeStep=1;
        }
        if(IsDead() && StateTime>2.f)
        {
            WriteCombatSnapshot();
            const FString Dir=FPaths::ProjectSavedDir()/TEXT("Automation/");
            IFileManager::Get().Copy(*(Dir+TEXT("warden-death-result.json")),*(Dir+TEXT("combat-runtime.json")));
            Restarted=true;
            if(auto* PC=Cast<AAshWellIntroPlayerController>(Controller))PC->IntroRestart();
        }
        return;
    }
    // Capture actual rendered states of the imported visual, independently of QA victory.
    static TSet<FString> VisualCaptures;
    if(Warden && Warden->HasGeneratedVisual())
    {
        FString Shot;
        if(Warden->GetCombatState()==EWellWardenState::Overload&&Warden->GetStateTime()>.65f)Shot=TEXT("Overload");
        else if(Warden->GetCombatState()==EWellWardenState::Windup && Warden->GetAttackProgress()>.82f)Shot=TEXT("Raised_")+Warden->GetAttackLabel();
        else if(Warden->GetCombatState()==EWellWardenState::Recovery)Shot=TEXT("Slam");
        else if(Warden->IsDead())Shot=TEXT("Defeated");
        if(bBattlePolish&&ActionState==EAction::Heavy&&StateTime>.56f&&StateTime<.70f)Shot=TEXT("PlayerHeavy");
        else if(bBattlePolish&&ActionState==EAction::Attack&&StateTime>.32f&&StateTime<.43f)Shot=TEXT("PlayerSlash");
        else if(bBattlePolish&&ActionState==EAction::Dodge&&StateTime>.26f&&StateTime<.40f)Shot=TEXT("PlayerRoll");
        else if(Warden->GetAttackKind()==EWellWardenAttack::Kick&&Warden->GetCombatState()==EWellWardenState::Strike&&Warden->GetStateTime()>.13f)Shot=TEXT("KickContact");
        if(!Shot.IsEmpty() && !VisualCaptures.Contains(Shot))
        {
            VisualCaptures.Add(Shot);
            const FString Path=FPaths::ProjectSavedDir()/TEXT("Screenshots/WardenHQ/")+Shot+TEXT(".png");
            IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path),true);
            FScreenshotRequest::RequestScreenshot(Path,true,false);
        }
    }
    const float CaptureTimes[]={.6f,6.f,10.f,16.f};
    if(QACaptureIndex<4&&QAElapsed>=CaptureTimes[QACaptureIndex])
    {
        const FString Name=FPaths::ProjectSavedDir()/FString::Printf(TEXT("Screenshots/Combat/Combat_%02d.png"),QACaptureIndex++);
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Name),true);
        FScreenshotRequest::RequestScreenshot(Name,true,false);
    }
    if(QAElapsed>1&&Arena&&!Arena->IsPowered())Interact();
    if(!bEncounterActive||!Warden)return;
    if(HasWon())
    {
        bLockedOn=false;
        const FVector Goal=bReadRecord?Arena->GetLiftPoint():Arena->GetConsoleLocation()+FVector(-110,0,90);
        const FVector D=Goal-GetActorLocation();
        if(!Arena->IsDeparting())
        {
            if((!bReadRecord&&FVector::Dist2D(GetActorLocation(),Arena->GetConsoleLocation())<230)||(bReadRecord&&D.Size2D()<175))Interact();
            else AddMovementInput(D.GetSafeNormal2D(),1);
        }
        if(!HasFinishedSlice()&&QAElapsed<330)return;
    }
    if(HasFinishedSlice()||IsDead()||QAElapsed>330)
    {
        bQAComplete=true;WriteCombatSnapshot();
        if(FParse::Param(FCommandLine::Get(),TEXT("CombatSoak")))
        {if(auto* PC=Cast<AAshWellIntroPlayerController>(Controller))PC->IntroRestart();}
        else if(FParse::Param(FCommandLine::Get(),TEXT("QAExit")))FPlatformMisc::RequestExit(false);
        return;
    }
    bLockedOn=true;
    if(ActionState!=EAction::Idle)return;
    const FVector Delta=Warden->GetActorLocation()-GetActorLocation();
    const float Distance=Delta.Size2D();
    if(Warden->IsAttacking()&&(Distance<355*Warden->GetActorScale3D().X||Warden->GetAttackKind()==EWellWardenAttack::Charge))
    {
        if(Warden->GetCombatState()==EWellWardenState::Windup&&Warden->GetAttackProgress()>.86f)
        {ForwardInput=Warden->GetAttackKind()==EWellWardenAttack::Sweep?-1.f:0.f;RightInput=Warden->GetAttackKind()==EWellWardenAttack::Sweep?0.f:1.f;Dodge();ForwardInput=RightInput=0;}
    }
    else if((Warden->GetCombatState()==EWellWardenState::Recovery&&!Warden->IsComboPending())||Warden->GetCombatState()==EWellWardenState::Stagger)
    {
        if(Distance>(bBattlePolish?205:150))AddMovementInput(Delta.GetSafeNormal2D(),1);
        else if(Stamina>=80){if(bBattlePolish&&AttackCount%3==2)HeavyAttack();else Attack();} // Keep dodge stamina in reserve.
    }
    else if(Distance>220)AddMovementInput(Delta.GetSafeNormal2D(),1);
}

void AAshWellCombatCharacter::WriteCombatSnapshot()
{
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();
    O->SetNumberField(TEXT("minimum_dilation"),ProbeMinimumDilation);O->SetNumberField(TEXT("minimum_separation"),ProbeMinimumSeparation);
    O->SetBoolField(TEXT("battle_polish"),bBattlePolish);O->SetNumberField(TEXT("heavy_attacks"),HeavyCount);O->SetNumberField(TEXT("fx_bursts"),BattleFX?BattleFX->GetBurstCount():0);O->SetNumberField(TEXT("time_dilation"),UGameplayStatics::GetGlobalTimeDilation(GetWorld()));
    O->SetStringField(TEXT("probe"),QAProbe);O->SetNumberField(TEXT("probe_step"),ProbeStep);O->SetNumberField(TEXT("committed_yaw_drift"),QAProbe==TEXT("camera")?0.f:ProbeYawDrift);O->SetNumberField(TEXT("camera_overlap_seconds"),QAProbe==TEXT("camera")?ProbeYawDrift:0.f);
    O->SetNumberField(TEXT("time"),GetWorld()->GetTimeSeconds());
    O->SetNumberField(TEXT("health"),Health);O->SetNumberField(TEXT("stamina"),Stamina);
    O->SetStringField(TEXT("state"),GetCombatState());
    O->SetNumberField(TEXT("state_time"),StateTime);
    O->SetBoolField(TEXT("invulnerable"),IsInvulnerable());O->SetBoolField(TEXT("locked"),bLockedOn);
    O->SetBoolField(TEXT("powered"),Arena&&Arena->IsPowered());O->SetBoolField(TEXT("encounter_active"),bEncounterActive);
    O->SetBoolField(TEXT("animation_blend_instance"),Cast<UAshWellAnimInstance>(GetMesh()->GetAnimInstance())!=nullptr);
    O->SetNumberField(TEXT("jumps"),JumpCount);
    O->SetNumberField(TEXT("jump_peak_cm"),JumpPeakHeight);
    O->SetStringField(TEXT("jump_key"),TEXT("SpaceBar"));O->SetStringField(TEXT("dodge_key"),TEXT("LeftShift"));
    O->SetBoolField(TEXT("jump_animation_loaded"),JumpAnimation!=nullptr);
    O->SetBoolField(TEXT("grounded"),GetCharacterMovement()->IsMovingOnGround());
    O->SetNumberField(TEXT("x"),GetActorLocation().X);O->SetNumberField(TEXT("y"),GetActorLocation().Y);O->SetNumberField(TEXT("z"),GetActorLocation().Z);
    O->SetNumberField(TEXT("attacks"),AttackCount);O->SetNumberField(TEXT("hits"),HitCount);O->SetNumberField(TEXT("dodges"),DodgeCount);
    O->SetNumberField(TEXT("damage_taken_count"),DamageTakenCount);O->SetNumberField(TEXT("evaded_hits"),EvadedHits);
    O->SetBoolField(TEXT("entry_open"),Arena&&Arena->IsEntryOpen());O->SetBoolField(TEXT("suno_music"),Arena&&Arena->HasSunoMusic());O->SetNumberField(TEXT("boss_scale"),Warden?Warden->GetActorScale3D().X:1.f);
    O->SetBoolField(TEXT("qa"),bQA);O->SetBoolField(TEXT("qa_complete"),bQAComplete);
    O->SetBoolField(TEXT("victory"),HasWon());O->SetBoolField(TEXT("combat_walk_loaded"),bCombatWalkLoaded);
    O->SetBoolField(TEXT("polished_weapon"),bPolishedWeapon);
    O->SetBoolField(TEXT("sword_pass"),bSwordPass);
    O->SetBoolField(TEXT("traveller_visual"),bTravellerVisual);
    O->SetBoolField(TEXT("hero_complete_assets"),bHeroComplete);
    O->SetNumberField(TEXT("cloth_simulations"),TravellerCloak?TravellerCloak->GetClothingSimulationInstances().Num():0);
    O->SetNumberField(TEXT("cloth_motion_cm"),ClothMotion);
    if(bHeroComplete&&TravellerCloak)
    {
        if(const auto* RD=TravellerCloak->GetSkeletalMeshAsset()->GetResourceForRendering())
        {
            int32 Mappings=0;for(const auto& S:RD->LODRenderData[0].RenderSections)Mappings+=S.HasClothingData();
            O->SetNumberField(TEXT("cloth_render_mappings"),Mappings);
        }
        O->SetBoolField(TEXT("cloth_can_simulate"),TravellerCloak->CanSimulateClothing());
        O->SetBoolField(TEXT("cloth_tick_enabled"),TravellerCloak->IsComponentTickEnabled());
        O->SetNumberField(TEXT("cloth_lod"),TravellerCloak->GetPredictedLODLevel());
        O->SetNumberField(TEXT("cloth_data_count"),TravellerCloak->GetCurrentClothingData_GameThread().Num());
        const auto& Assets=TravellerCloak->GetSkeletalMeshAsset()->GetMeshClothingAssets();
        if(Assets.Num())if(const auto* Cloth=Cast<UClothingAssetCommon>(Assets[0]))
        {
            O->SetNumberField(TEXT("cloth_lod_map"),Cloth->LodMap.Num()?Cloth->LodMap[0]:-99);
            O->SetNumberField(TEXT("cloth_configs"),Cloth->ClothConfigs.Num());
            FBox Box(ForceInit);for(const auto& P:Cloth->LodData[0].PhysicalMeshData.Vertices)Box+=FVector(P);
            O->SetStringField(TEXT("cloth_rest_min"),Box.Min.ToString());O->SetStringField(TEXT("cloth_rest_max"),Box.Max.ToString());
            const auto& Weights=Cloth->LodData[0].PhysicalMeshData.GetWeightMap(EWeightMapTargetCommon::MaxDistance).Values;
            int32 Free=0;float Max=0;for(float V:Weights){Free+=V>.001f;Max=FMath::Max(Max,V);}
            O->SetNumberField(TEXT("cloth_free_vertices"),Free);O->SetNumberField(TEXT("cloth_max_distance"),Max);
        }
    }


    O->SetStringField(TEXT("render_bounds_origin"),(GetMesh()->Bounds.Origin-GetActorLocation()).ToString());
    O->SetStringField(TEXT("render_bounds_extent"),GetMesh()->Bounds.BoxExtent.ToString());
    if(bQA&&QAProbe==TEXT("sword_pose")&&bTravellerVisual)
    {
        if(const auto* Data=GetMesh()->GetSkeletalMeshAsset()->GetResourceForRendering())
        {FString Sections;for(const auto& Section:Data->LODRenderData[0].RenderSections)Sections+=FString::Printf(TEXT("%d "),Section.MaterialIndex);O->SetStringField(TEXT("render_material_indices"),Sections);}
        if(const auto* L=GetMesh()->GetSkeletalMeshAsset()->GetLODInfo(0))
        {FString Map;for(int32 I:L->LODMaterialMap)Map+=FString::Printf(TEXT("%d "),I);O->SetStringField(TEXT("lod_material_map"),Map);}
        TArray<FFinalSkinVertex> Vertices;GetMesh()->GetCPUSkinnedVertices(Vertices,0);FBox Box(ForceInit);
        FString UVs;for(int32 I=0;I<Vertices.Num();I+=FMath::Max(1,Vertices.Num()/12))UVs+=FString::Printf(TEXT("%.4f,%.4f;"),Vertices[I].TextureCoordinates[0].X,Vertices[I].TextureCoordinates[0].Y);O->SetStringField(TEXT("skin_uvs"),UVs);
        for(const auto& V:Vertices)Box+=GetMesh()->GetComponentTransform().TransformPosition(FVector(V.Position))-GetActorLocation();
        O->SetStringField(TEXT("skin_vertices_min"),Box.Min.ToString());O->SetStringField(TEXT("skin_vertices_max"),Box.Max.ToString());
    }
    for(const TCHAR* Bone:{TEXT("root"),TEXT("pelvis"),TEXT("hand_L"),TEXT("foot_L"),TEXT("head")})
    {const FVector P=GetMesh()->GetSocketLocation(Bone)-GetActorLocation();O->SetStringField(FString(TEXT("bone_"))+Bone,P.ToString());}
    O->SetStringField(TEXT("skin_material"),GetMesh()->GetMaterial(0)?GetMesh()->GetMaterial(0)->GetName():TEXT("none"));
    O->SetStringField(TEXT("blade_tip"),(SwordPoint(101)-GetActorLocation()).ToString());
    O->SetNumberField(TEXT("probe_failures"),ProbeYawDrift);
    O->SetBoolField(TEXT("sword_ready"),IsSwordReady());
    O->SetNumberField(TEXT("speed"),GetVelocity().Size2D());
    O->SetStringField(TEXT("locomotion_animation"),SelectLocomotionAnimation(GetVelocity().Size2D())?SelectLocomotionAnimation(GetVelocity().Size2D())->GetName():TEXT("none"));
    O->SetBoolField(TEXT("attack_animation_loaded"),AttackAnimation!=nullptr);O->SetBoolField(TEXT("dodge_animation_loaded"),DodgeAnimation!=nullptr);
    O->SetNumberField(TEXT("camera_boom_length"),FVector::Distance(FollowCamera->GetComponentLocation(),GetActorLocation()));
    O->SetNumberField(TEXT("hand_bone_scale"),GetMesh()->GetSocketTransform(TEXT("hand_L"),RTS_World).GetScale3D().GetAbsMax());
    if(Warden)
    {
        O->SetBoolField(TEXT("enemy_generated_visual"),Warden->HasGeneratedVisual());
        O->SetBoolField(TEXT("enemy_skinned_visual"),Warden->HasSkinnedVisual());
        O->SetBoolField(TEXT("phase_two"),Warden->IsPhaseTwo());
        O->SetBoolField(TEXT("combo_pending"),Warden->IsComboPending());
        O->SetStringField(TEXT("enemy_attack"),Warden->GetAttackLabel());
        O->SetNumberField(TEXT("enemy_strikes"),Warden->GetStrikeCount());
        O->SetNumberField(TEXT("enemy_contacts"),Warden->GetContactCount());
        O->SetNumberField(TEXT("enemy_generated_parts"),Warden->GetGeneratedPartCount());
        O->SetNumberField(TEXT("enemy_hammer_path_error_cm"),Warden->GetGeneratedHammerError());
        O->SetNumberField(TEXT("enemy_health"),Warden->GetHealth());O->SetStringField(TEXT("enemy_state"),Warden->GetStateLabel());
        O->SetNumberField(TEXT("enemy_x"),Warden->GetActorLocation().X);O->SetNumberField(TEXT("enemy_y"),Warden->GetActorLocation().Y);
        O->SetNumberField(TEXT("enemy_z"),Warden->GetActorLocation().Z);
    }
    O->SetBoolField(TEXT("record_read"),bReadRecord);O->SetBoolField(TEXT("slice_completed"),HasFinishedSlice());
    O->SetNumberField(TEXT("ending_time"),EndingTime);
    FString Text;TSharedRef<TJsonWriter<>> Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(O,Writer);
    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/combat-runtime.json");
    FFileHelper::SaveStringToFile(Text,*(File+TEXT(".tmp")),FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    IFileManager::Get().Move(*File,*(File+TEXT(".tmp")),true);
}
