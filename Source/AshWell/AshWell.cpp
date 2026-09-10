#include "Modules/ModuleManager.h"

#if PLATFORM_MAC && WITH_EDITOR
#include "Containers/Ticker.h"
#include "Misc/OutputDevice.h"
#include "Misc/OutputDeviceRedirector.h"
#include "Runtime/Launch/Resources/Version.h"
#include <cstdio>

namespace
{
// UE 5.8 AppExit tears down logging immediately before localization/ICU.
// Earlier OnPreExit cleanup is insufficient: module teardown can enqueue more
// Slate notification callbacks. Keep this static sink alive across module
// shutdown, then release the callbacks while ICU's allocator is still valid.
class FEditorExitDrain final : public FOutputDevice
{
public:
    void Serialize(const TCHAR*, ELogVerbosity::Type, const FName&) override {}
    void TearDown() override
    {
        if (GIsEditor)
        {
            FTSTicker::GetCoreTicker().Reset();
            // Reset destroys Elements after draining AddedElements; destruction
            // can enqueue another deferred notification into AddedElements.
            FTSTicker::GetCoreTicker().Reset();
            std::fputs("AW_EDITOR_EXIT late callback drain before ICU teardown\n", stderr);
        }
    }
};
FEditorExitDrain EditorExitDrain;
}
#endif

class FAshWellModule final : public FDefaultGameModuleImpl
{
public:
    void StartupModule() override
    {
#if PLATFORM_MAC && WITH_EDITOR && ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 8
        if (GIsEditor && GLog)
        {
            GLog->AddOutputDevice(&EditorExitDrain);
        }
#endif
    }

    void ShutdownModule() override
    {
#if PLATFORM_MAC && WITH_EDITOR
        // A live reload/unload must detach; normal shutdown needs the later hook.
        if (!IsEngineExitRequested() && GLog)
        {
            GLog->RemoveOutputDevice(&EditorExitDrain);
        }
#endif
    }
};

IMPLEMENT_PRIMARY_GAME_MODULE(FAshWellModule, AshWell, "AshWell");
