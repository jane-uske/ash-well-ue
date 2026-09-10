#include "AshWellIntroCharacter.h"
#include "AshWellIntroAudio.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Animation/AnimSequence.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "UnrealClient.h"

static FVector WalkwayPoint(float T)
{
    if(T<=12) return FVector((-6+T)*100,0,0);
    const float Q=(T-12)/20;
    return FVector((6+18*Q)*100,8*Q*Q*(3-2*Q)*100,0);
}
AAshWellIntroCharacter::AAshWellIntroCharacter()
{
    PrimaryActorTick.bCanEverTick=true;
    GetCapsuleComponent()->InitCapsuleSize(28,88);
    GetCharacterMovement()->MaxWalkSpeed=NormalWalkSpeed;
    GetCharacterMovement()->MaxAcceleration=330;
    GetCharacterMovement()->BrakingDecelerationWalking=420;
    GetCharacterMovement()->GroundFriction=6;
    GetCharacterMovement()->MaxStepHeight=18;
    GetCharacterMovement()->bCanWalkOffLedges=false;
    GetCharacterMovement()->bOrientRotationToMovement=false;
    bUseControllerRotationYaw=false;
    GetMesh()->SetRelativeLocation(FVector(0,0,-88));
    GetMesh()->SetRelativeScale3D(FVector(1,-1,1));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    CameraBoom=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength=420;
    CameraBoom->SocketOffset=FVector(0,85,102);
    CameraBoom->bUsePawnControlRotation=true;
    CameraBoom->bEnableCameraLag=true;
    CameraBoom->CameraLagSpeed=6;
    CameraBoom->bDoCollisionTest=false; // The curated corridor has dedicated walking bounds.
    FollowCamera=CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom,USpringArmComponent::SocketName);
    FollowCamera->FieldOfView=70;
    LanternLight=CreateDefaultSubobject<UPointLightComponent>(TEXT("LanternLight"));
    LanternLight->SetupAttachment(RootComponent);
    LanternLight->IntensityUnits=ELightUnits::Lumens;
    LanternLight->SetIntensity(190);
    LanternLight->SetLightColor(FLinearColor(1,.43,.12));
    LanternLight->SetAttenuationRadius(480);
    LanternLight->SourceRadius=7;
    LanternLight->VolumetricScatteringIntensity=.35;
}
void AAshWellIntroCharacter::BeginPlay()
{
    Super::BeginPlay();
    StartTime=GetWorld()->GetTimeSeconds();
    bQACapture=FParse::Param(FCommandLine::Get(),TEXT("IntroQA"));
    StepAttenuation=AshWellIntroAudio::CreateFootstepAttenuation(this);
    WellReverb=AshWellIntroAudio::CreateWellReverb(this,this);
    if(!HeroMesh) HeroMesh=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/AshWell/Intro/Characters/SK_Intro_Protagonist.SK_Intro_Protagonist"));
    if(!WalkAnimation) WalkAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Protagonist_Walk.A_Intro_Protagonist_Walk"));
    if(!IdleAnimation) IdleAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/AshWell/Intro/Characters/A_Intro_Protagonist_Idle.A_Intro_Protagonist_Idle"));
    if(FootstepSounds.IsEmpty())for(int32 I=1;I<=6;++I)
    {
        const FString Name=FString::Printf(TEXT("AW_Foley_WetStoneStep_%02d"),I);
        if(auto* S=LoadObject<USoundBase>(nullptr,*(FString(TEXT("/Game/AshWell/Intro/Audio/"))+Name+TEXT(".")+Name)))FootstepSounds.Add(S);
    }
    if(GearSounds.IsEmpty())for(int32 I=1;I<=3;++I)
    {
        const FString Name=FString::Printf(TEXT("AW_Foley_LanternGear_%02d"),I);
        if(auto* S=LoadObject<USoundBase>(nullptr,*(FString(TEXT("/Game/AshWell/Intro/Audio/"))+Name+TEXT(".")+Name)))GearSounds.Add(S);
    }
    if(HeroMesh) GetMesh()->SetSkeletalMesh(HeroMesh);
    if(IdleAnimation) PlayCharacterAnimation(IdleAnimation,true);
    PreviousLocation=GetActorLocation();
    SetAutoTour(FParse::Param(FCommandLine::Get(),TEXT("IntroTour")));
}
void AAshWellIntroCharacter::EndPlay(const EEndPlayReason::Type Reason)
{
    UGameplayStatics::DeactivateReverbEffect(this,TEXT("FirstDescentWell"));
    Super::EndPlay(Reason);
}
void AAshWellIntroCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("MoveForward",this,&AAshWellIntroCharacter::MoveForward);
    Input->BindAxis("MoveRight",this,&AAshWellIntroCharacter::MoveRight);
    Input->BindAxis("Turn",this,&AAshWellIntroCharacter::LookYaw);
    Input->BindAxis("LookUp",this,&AAshWellIntroCharacter::LookPitch);
    Input->BindAction("Quiet",IE_Pressed,this,&AAshWellIntroCharacter::QuietDown);
    Input->BindAction("Quiet",IE_Released,this,&AAshWellIntroCharacter::QuietUp);
}
void AAshWellIntroCharacter::MoveForward(float V)
{
    if(!Controller||FMath::IsNearlyZero(V))return;
    bAutoTour=false;
    AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),V);
}
void AAshWellIntroCharacter::MoveRight(float V)
{
    if(!Controller||FMath::IsNearlyZero(V))return;
    bAutoTour=false;
    AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),V);
}
void AAshWellIntroCharacter::LookYaw(float V){AddControllerYawInput(V*1.2f);}
void AAshWellIntroCharacter::LookPitch(float V){AddControllerPitchInput(V*1.1f);}
void AAshWellIntroCharacter::QuietDown(){bQuiet=true;GetCharacterMovement()->MaxWalkSpeed=QuietWalkSpeed;}
void AAshWellIntroCharacter::QuietUp(){bQuiet=false;GetCharacterMovement()->MaxWalkSpeed=NormalWalkSpeed;}
void AAshWellIntroCharacter::SetAutoTour(bool bEnabled){bAutoTour=bEnabled;TourElapsed=0;}
void AAshWellIntroCharacter::Tick(float Dt)
{
    Super::Tick(Dt);
    const float Age=GetWorld()->GetTimeSeconds()-StartTime;
    if(bQACapture&&QACaptureIndex<4)
    {
        const float Times[]={2,11,16,28};
        if(Age>=Times[QACaptureIndex])
        {
            const FString Name=FPaths::ProjectSavedDir()/FString::Printf(TEXT("Screenshots/Intro/Intro_%02d.png"),QACaptureIndex);
            IFileManager::Get().MakeDirectory(*FPaths::GetPath(Name),true);
            FScreenshotRequest::RequestScreenshot(Name,true,false);
            ++QACaptureIndex;
        }
    }
    if(bAutoTour)
    {
        TourElapsed+=Dt;
        if(GetActorLocation().X<1250)
        {
            const float T=GetActorLocation().X<=600 ? GetActorLocation().X/100+6 : 12+(GetActorLocation().X/100-6)/.9;
            FVector Dir=WalkwayPoint(T+.65f)-GetActorLocation();Dir.Z=0;
            AddMovementInput(Dir.GetSafeNormal(),1);
        }
        if(Controller)
        {
            const FRotator Wanted(-5,FMath::Lerp(7.f,17.f,FMath::Clamp(TourElapsed/24,0.f,1.f)),0);
            Controller->SetControlRotation(FMath::RInterpTo(Controller->GetControlRotation(),Wanted,Dt,1.2f));
        }
    }
    const FVector Here=GetActorLocation();
    const float Travel=FVector::Dist2D(Here,PreviousLocation);
    PreviousLocation=Here;
    if(Travel<40){TotalDistance+=Travel;StepDistance+=Travel;}
    const float Speed=GetVelocity().Size2D();
    const bool bWalking=Speed>5;
    if(bWalking&&ShouldFaceMovement())
    {
        const FRotator Facing(0,GetVelocity().Rotation().Yaw,0);
        SetActorRotation(FMath::RInterpTo(GetActorRotation(),Facing,Dt,5));
    }
    if(ShouldUpdateLocomotion())
    {
        UAnimSequence* Anim=SelectLocomotionAnimation(Speed);
        if(Anim&&Anim!=LastLocomotionAnimation){PlayCharacterAnimation(Anim,true);LastLocomotionAnimation=Anim;}
        bWasWalking=bWalking;
    }
    else{bWasWalking=false;LastLocomotionAnimation=nullptr;StepDistance=0;}
    if(ShouldUpdateLocomotion()&&bWalking)if(UAnimSingleNodeInstance* Inst=Cast<UAnimSingleNodeInstance>(GetMesh()->GetAnimInstance()))Inst->SetPlayRate(FMath::Clamp(Speed/GetLocomotionReferenceSpeed(),.4f,1.8f));
    if(ShouldUpdateLocomotion()&&bWalking&&GetCharacterMovement()->IsMovingOnGround()&&StepDistance>GetFootstepSpacing()){StepDistance-=GetFootstepSpacing();PlayFootstep();}
    FVector Lamp=Here+GetActorRotation().RotateVector(FVector(8,35,-20));
    if(GetMesh()->DoesSocketExist(TEXT("lamp_light_R"))) Lamp=GetMesh()->GetSocketLocation(TEXT("lamp_light_R"));
    LanternLight->SetWorldLocation(Lamp);
    LanternLight->SetIntensity(190*(1+.025f*FMath::Sin(Age*4.1f)+.012f*FMath::Sin(Age*8.7f)));
    const float Bob=bWalking?FMath::Sin(TotalDistance/GetFootstepSpacing()*PI)*.75f:0;
    CameraBoom->SocketOffset.Z=102+Bob;
    TelemetryElapsed+=Dt;
    if(TelemetryElapsed>=1){TelemetryElapsed=0;WriteTelemetry();}
}
void AAshWellIntroCharacter::PlayFootstep()
{
    if(FootstepSounds.Num())
    {
        USoundBase* Sound=FootstepSounds[StepCount%FootstepSounds.Num()];
        UGameplayStatics::PlaySoundAtLocation(this,Sound,GetActorLocation()-FVector(0,0,80),bQuiet?.22f:.65f,1.f+FMath::Sin(StepCount*2.1f)*.045f,0.f,StepAttenuation);
    }
    if(StepCount%3==1&&GearSounds.Num())UGameplayStatics::PlaySoundAtLocation(this,GearSounds[StepCount%GearSounds.Num()],GetActorLocation(),.18f);
    ++StepCount;
}

void AAshWellIntroCharacter::PlayCharacterAnimation(UAnimSequence* Animation,bool bLoop)
{
    GetMesh()->PlayAnimation(Animation,bLoop);
}
void AAshWellIntroCharacter::WriteTelemetry()
{
    TSharedRef<FJsonObject> O=MakeShared<FJsonObject>();
    O->SetStringField(TEXT("world"),GetWorld()->GetMapName());
    O->SetNumberField(TEXT("elapsed"),GetWorld()->GetTimeSeconds()-StartTime);
    O->SetNumberField(TEXT("x"),GetActorLocation().X);O->SetNumberField(TEXT("y"),GetActorLocation().Y);O->SetNumberField(TEXT("z"),GetActorLocation().Z);
    O->SetNumberField(TEXT("distance_cm"),TotalDistance);O->SetNumberField(TEXT("steps"),StepCount);
    O->SetNumberField(TEXT("speed_cm_s"),GetVelocity().Size2D());
    O->SetNumberField(TEXT("max_walk_speed_cm_s"),GetCharacterMovement()->MaxWalkSpeed);
    O->SetBoolField(TEXT("quiet_walking"),bQuiet);
    O->SetBoolField(TEXT("grounded"),GetCharacterMovement()->IsMovingOnGround());
    O->SetBoolField(TEXT("auto_tour"),bAutoTour);O->SetBoolField(TEXT("mesh_loaded"),GetMesh()->GetSkeletalMeshAsset()!=nullptr);
    O->SetBoolField(TEXT("walk_loaded"),WalkAnimation!=nullptr);O->SetBoolField(TEXT("idle_loaded"),IdleAnimation!=nullptr);
    O->SetNumberField(TEXT("footstep_sounds"),FootstepSounds.Num());
    O->SetNumberField(TEXT("frame_ms"),GetWorld()->GetDeltaSeconds()*1000);
    if(APlayerController* PC=Cast<APlayerController>(Controller))
    {
        O->SetStringField(TEXT("controller"),PC->GetClass()->GetPathName());
        O->SetBoolField(TEXT("paused"),UGameplayStatics::IsGamePaused(this));
    }
    FString S;TSharedRef<TJsonWriter<>> W=TJsonWriterFactory<>::Create(&S);FJsonSerializer::Serialize(O,W);
    const FString File=FPaths::ProjectSavedDir()/TEXT("Automation/intro-player-runtime.json");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(File),true);FFileHelper::SaveStringToFile(S,*File);
}
