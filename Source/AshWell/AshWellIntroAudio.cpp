#include "AshWellIntroAudio.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/ReverbEffect.h"
#include "Sound/SoundAttenuation.h"
#include "UObject/UObjectGlobals.h"

namespace AshWellIntroAudio
{
    UReverbEffect* CreateWellReverb(UObject* Outer, UObject* WorldContext)
    {
        if (!IsValid(Outer) || !IsValid(WorldContext) || !GEngine)
        {
            return nullptr;
        }

        UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull);
        if (!World || !World->IsGameWorld())
        {
            return nullptr;
        }

        UReverbEffect* Reverb = NewObject<UReverbEffect>(Outer, NAME_None, RF_Transient);
        // The UE 5.7 effect stores these directly on UReverbEffect, not in a
        // Settings struct. A readable early return and dark short tail preserve
        // each sole impact; this is a mine entrance, not a bright hall wash.
        Reverb->bBypassEarlyReflections = false;
        Reverb->ReflectionsDelay = 0.072f;
        Reverb->ReflectionsGain = 0.35f;
        Reverb->GainHF = 0.42f;

        Reverb->bBypassLateReflections = false;
        Reverb->LateDelay = 0.037f;
        Reverb->DecayTime = 2.65f;
        Reverb->DecayHFRatio = 0.52f;
        Reverb->Density = 0.78f;
        Reverb->Diffusion = 0.72f;
        Reverb->AirAbsorptionGainHF = 0.96f;
        Reverb->LateGain = 1.10f;
        Reverb->Gain = 0.65f;

        UGameplayStatics::ActivateReverbEffect(WorldContext, Reverb,
            FName(TEXT("FirstDescentWell")), 1.0f, 0.35f, 2.0f);
        return Reverb;
    }

    USoundAttenuation* CreateFootstepAttenuation(UObject* Outer)
    {
        if (!IsValid(Outer))
        {
            return nullptr;
        }

        USoundAttenuation* Attenuation = NewObject<USoundAttenuation>(Outer, NAME_None, RF_Transient);
        FSoundAttenuationSettings& Settings = Attenuation->Attenuation;
        Settings.bAttenuate = true;
        Settings.bSpatialize = true;
        Settings.SpatializationAlgorithm = SPATIALIZATION_Default;
        Settings.DistanceAlgorithm = EAttenuationDistanceModel::Linear;
        Settings.AttenuationShape = EAttenuationShape::Sphere;
        Settings.AttenuationShapeExtents = FVector(500.0f, 0.0f, 0.0f);
        // Falloff is measured OUTSIDE the inner shape: 500 + 1500 = 2000 cm.
        Settings.FalloffDistance = 1500.0f;
        Settings.NonSpatializedRadiusStart = 0.0f;
        Settings.NonSpatializedRadiusEnd = 0.0f;
        Settings.StereoSpread = 0.0f;

        Settings.bEnableReverbSend = true;
        Settings.ReverbSendMethod = EReverbSendMethod::Linear;
        Settings.ReverbDistanceMin = 0.0f;
        Settings.ReverbDistanceMax = 2000.0f;
        Settings.ReverbWetLevelMin = 0.30f;
        Settings.ReverbWetLevelMax = 0.45f;
        Settings.ManualReverbSendLevel = 0.35f;

        // Retain close wet-grit detail and take the edge off distant footsteps.
        Settings.bAttenuateWithLPF = true;
        Settings.AbsorptionMethod = EAirAbsorptionMethod::Linear;
        Settings.bEnableLogFrequencyScaling = true;
        Settings.LPFRadiusMin = 500.0f;
        Settings.LPFRadiusMax = 2000.0f;
        Settings.LPFFrequencyAtMin = 14000.0f;
        Settings.LPFFrequencyAtMax = 4200.0f;
        Settings.HPFFrequencyAtMin = 0.0f;
        Settings.HPFFrequencyAtMax = 0.0f;

        // The walk-in uses hidden BlockAll safety rails. Visibility-channel
        // occlusion would mistake those for solid acoustic walls, so leave it
        // off until dedicated acoustic geometry exists.
        Settings.bEnableOcclusion = false;
        Settings.bUseComplexCollisionForOcclusion = false;
        Settings.bEnableListenerFocus = false;
        return Attenuation;
    }
}
