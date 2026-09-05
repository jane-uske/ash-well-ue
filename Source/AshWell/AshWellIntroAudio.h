#pragma once

#include "CoreMinimal.h"

class UReverbEffect;
class USoundAttenuation;

namespace AshWellIntroAudio
{
    /**
     * Creates and activates a dark, restrained cave reverb for this game world.
     * Call once from BeginPlay and keep the return value in a UPROPERTY TObjectPtr.
     * On EndPlay, deactivate the tag "FirstDescentWell" using GameplayStatics.
     * Returns nullptr for an invalid owner/context or a non-game world.
     */
    ASHWELL_API UReverbEffect* CreateWellReverb(UObject* Outer, UObject* WorldContext);

    /**
     * Creates transient mono Foley attenuation: full level within 5 m, silent
     * at 20 m, spatial panning, and a modest distance-dependent cave send.
     * Keep the return value in a UPROPERTY TObjectPtr before using it in playback.
     */
    ASHWELL_API USoundAttenuation* CreateFootstepAttenuation(UObject* Outer);
}
