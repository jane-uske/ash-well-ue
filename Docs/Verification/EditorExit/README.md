# UE 5.8.2 Mac editor exit crash — 2026-09-10

The user's screenshot matches editor PID 45018. CrashContext says `EngineMode=Editor`, `IsRequestingExit=true`, `UserActivityHint=EditorExit`. PID 29769 has the same stack. Both were editors used for asset import, not the successful combat QA process.

The stack releases an `FSlateAsyncTaskNotificationImpl::UpdateNotificationDeferred` capture during static `FTSTicker` destruction, then `FTextLayout` / `FICUTextBiDi` / `ubidi_close_64` ends in an invalid malloc free. The local engine shuts down ICU in `FEngineLoop::AppExit` before process static destructors run. The initial ticker reset happens much earlier, and module shutdown can enqueue additional notification callbacks. `OnPreExit` alone did not fix the reproduced issue.

Project-scoped workaround: `Source/AshWell/AshWell.cpp` registers a static output-device teardown hook only in Mac UE 5.8 editor mode. Logging teardown is immediately before localization/ICU teardown in the installed engine. The hook clears the ticker, then clears it once more because destructing its Elements can enqueue AddedElements after the first queue drain. No callbacks are executed, no crash handler is disabled, and the installed engine is not edited. Game mode does not register the hook.

Automation now has `Scripts/shutdown_editor.command` and native MCP stage `shutdown`, which schedules Unreal's own `QuitEditor`. Prefer this over SIGTERM; neither this helper nor the workaround force-saves dirty assets. Interactive editor close/save decisions remain in UE.

Verification: two separate editor launches, each reimporting the battle assets and quitting through native MCP, returned 0, logged normal exit and the late cleanup marker, and generated no new crash folders. A third launch repeated the original SIGTERM trigger: return 0, cleanup marker present, and no new crash folder. SIGTERM uses a shorter platform shutdown path, so it does not emit the native path's `LogExit: Exiting.` marker; it is retained as a crash regression, not the recommended close method.

`after.json` contains all three process-specific results. `before.json` contains the matching original reports with the relevant stack and process fields. Original reports remain in the local Unreal crash directory. This fixes the reproduced editor-exit failure; unrelated historical GameFeatureData ensures and general gameplay stability are separate checks.

Reproduce: close other project editor instances, then run `python3 Scripts/test_editor_shutdown.py`. It uses the configured Xcode-beta developer directory and the project native MCP server on 19854, reimports existing battle assets and checks per-process crash output.
