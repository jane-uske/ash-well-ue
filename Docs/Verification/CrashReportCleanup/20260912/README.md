# 2026-09-12 崩溃报告残留核查

用户截图中的四个无响应项均已与 AshWell 的 CrashReportClientEditor 残留对应；核查开始时没有游戏或 UE 编辑器本体运行。

| 报告进程 PID | 启动时间（本地） | CPU | 对应操作 |
| --- | --- | --- | --- |
| 87211 | 09-10 22:55 | 99.3% | import_hero_complete.py 在 commandlet 环境使用 Slate / 资产导入接口，CurrentApplication.IsValid 断言 |
| 14775 | 09-10 23:38 | 99.0% | build_mounted_arena.py 在 commandlet 环境访问 LevelEditorSubsystem::IsInPlayInEditor，非法访问 |
| 61836 | 09-11 20:47 | 98.3% | 早期冲锋样本导入图连接失败后退出；Editor ModeManager 在销毁阶段断言 |
| 64572 | 09-11 20:53 | 99.2% | 冲锋样本导入结束后的相同编辑器退出断言 |

四者父进程均已成为 launchd（PPID 1），总 CPU 约 395.8%，RSS 合计约 572 MiB。属于导入/编辑器工具链故障后未清理的报告程序，不能据此诊断为骑战运行时性能缺陷，也不能把这些真实崩溃说成普通闲置进程。

对 64572 的采样显示其卡在自身退出路径：FScheduler::StopWorkers → CheckVerifyFailed → 日志重定向。另有最近两次 CrashReportClientEditor 自身 SIGSEGV 的 Apple 报告；这些报告与活着的四个 PID 不应混为同一个进程实例。

已逐个核对命令行和 AshWell 报告路径，然后发送 SIGTERM。四者全部退出，无需 SIGKILL；未删除原始崩溃日志，未修改游戏代码或系统安全设置。processes-before.txt、cleanup.json、processes-after.txt 与 crash-contexts.json 保存证据。

性能边界：此前 A/B 录像期间这些高 CPU 残留仍存在，且 FrameGrabber 本身有开销。旧录像的 18 FPS 不能当作清理后游戏性能基准；清理没有自动证明画面性能达标。

预防原则：后续每次自动化 UE 任务必须同时检查退出日志、返回码和新生崩溃报告；资产导入成功不等于退出成功。仅可清理由该任务 PID 对应且已保留报告的残留，不全局杀 UE 进程，不通过关闭崩溃报告功能掩盖错误。此次未声称根治 UE 编辑器退出缺陷。

复查结果：当前编辑器实际加载人马 AnimBP 与冲锋 Montage 后正常退出（返回码 0，无 Fatal/Ensure）；当前新资产冲锋实机检查通过，单次命中 32 点、六阶段通知、恢复后退出返回码 0。最终检查无 UE 游戏本体和 CrashReportClient 残留。这不是完整性能测试或 C 验收。
