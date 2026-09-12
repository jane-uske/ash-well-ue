# Ash Well — Unreal

## 当前进度（2026-09-11）

当前制作阶段为骑战 Boss 的“冲锋横扫”质量样本。新资产、AnimBP、Montage、Notify 与 UE 原生马匹 IK 重定向已实际运行，保留原六招入口。当前 A/B 连续实机录像已交付为待验收候选；C 普通输入尝试受操作工具限制，未通过。详见 [样本状态、录像与启动/回退](Docs/Implementation/MountedBoss/ChargeSample/STATUS.md)。本轮不扩世界、剧情或背包。

- 骑战入口：`Scripts/launch_mounted_boss.command`。六招、阶段变化、死亡/胜利和重试已实现；马步滑移、完整自然交锋与美术仍待打磨。
- 守井者入口：`Scripts/launch_station_gate.command`。保留现有主角 v02、长剑与原战斗基线。
- 验证：样本战斗实现版本 27/27 必要回归（含原六招与守井者）；后续录制/盾朝向修正的最新二进制 5/5 针对性回归。版本 hash 与覆盖范围见样本状态，不能作为视觉验收。旧阶段测试保留在 [验收矩阵](Docs/Implementation/MountedBoss/qa_matrix.json)。
- 私有远程仓库：[jane-uske/ash-well-ue](https://github.com/jane-uske/ash-well-ue)。旧网页原型仓库独立保留。

## 既有方向与文档入口（2026-09-10）

**新会话接手先读：[会话上下文与接续说明](Docs/Handoff/session-context-2026-09-10.md)。** 汇总已确认决定、长剑人物现状、尚未实施的战斗通用化建议、工具与预算背景、已知问题和验证边界。

当前方向：具有魂系气质的古老奇幻冒险。以用户指定的《艾尔登法环》式壮美、神秘、探索与战斗重量为参考，采用 AshWell 原创世界与角色。

- **美术制作依据：**[整体美术规范 v1.2](Docs/ArtDirection/art-direction-v1.md)。古老奇幻为主体；旧工业主导版本已被取代。
- **现有可玩内容：**[第一章实现记录](Docs/Implementation/chapter01-map.md)。这是实施状态，与新的美术目标分开阅读；本次文档更新未替换地图、模型或玩法代码。
- **最新剧本提案：**[《未竟之日》主线剧本 v0.3](Docs/Story/ash-well-screenplay-v03.md)，配套[演出、线索与关卡衔接](Docs/Story/ash-well-screenplay-v03-production.md)。以送葬旅人进入未结束的加冕日展开，包含三幕及两条短结尾；待评审，未实装。
- **上一版故事候选：**[姐姐救援与上下城提案 v0.2](Docs/Design/world-premise-v02.md)及其地图保留供回看，不与当前剧本混作同一设定。
- **旧剧情讨论：**[工业故事初稿](Docs/Story/main-story-v01.md)保留供比较，不与新提案同时作为确定设定。当前运行中的旧文本尚未替换。

制作以一段完整可玩的区域为起点，不将风格参考等同于完整开放世界的规模承诺。早期 Docs/visual-dev 和概念图保留为历史证据；美术冲突以当前规范为准。

UE 5.8.2 playable development baseline.

## Run

- `Scripts/launch_chapter01.command`: Chapter One, from the ration street through the mine and cliff walkway to the existing Boss encounter and elevator. Repair the water pump with E to open the departure gate. R retries from the station once reached; before that it restarts the street.

- `Scripts/launch_combat.command`: inspection-station development slice. E powers the station/interacts, Tab locks on, left mouse attacks, right mouse uses a heavy attack, Space jumps, tap Shift to dodge / hold Shift to sprint, R retries. Esc pauses; arrow keys adjust volume, sensitivity and subtitles.
- `Scripts/launch_intro.command`: introduction.
- `Scripts/launch_editor_mcp.command`: editor and official MCP on localhost:8001. Close the old AshWell MCP editor first to free this port.

Build before first launch:

```sh
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer '/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' AshWellEditor Mac Development "$PWD/AshWell.uproject" -WaitMutex -NoHotReloadFromIDE -architecture=arm64
```

## Contents

Chapter One map and current validation: [chapter01-map.md](Docs/Implementation/chapter01-map.md).

Existing combat implementation, validation limits and fallback: [inspection-station-polish.md](Docs/Implementation/inspection-station-polish.md). Actual before/after captures: [comparison.html](Docs/Verification/InspectionStation/comparison.html). Packaging is paused; older applications under Artifacts do not include the latest development changes.

`Source` gameplay; `Content` Unreal assets; `SourceAssets` editable model/audio sources; `Scripts` build/import helpers; `Docs` design and verification history. Historical documents may mention previous paths or engine versions.

Git LFS manages binary assets. Install Git LFS and run `git lfs pull` after cloning. Binaries, caches and live runtime output are excluded. Selected verification evidence is archived under `Docs/Verification`. The private remote is `jane-uske/ash-well-ue`; credentials and raw signed download responses are excluded. Asset-specific licenses remain authoritative; a private backup does not establish public redistribution rights.

The browser prototype and UE 5.7 project remain in ../ash-well. This repository combines the tested 5.8 code/assets with the original editable sources and scripts.

Migration check: native arm64 Development editor build succeeded from this repository path. Runtime and MCP evidence in Docs/Verification were recorded on the equivalent pre-migration 5.8 project.

## 检修站战斗精修 v01

双击 `Scripts/launch_station_gate.command` 从大门前体验。左键横劈、右键重砸、空格跳跃、Shift 点按翻滚/长按冲刺、Tab 锁定、E 交互、R 重试。Meshy 动作已适配，Boss 有重砸、近身踹击及拖锤追击。未打包。

实现与积分记录：[battle-polish-v01](Docs/Implementation/battle-polish-v01.md)。实机证据：[BattlePolish](Docs/Verification/BattlePolish/)。旧动作回退：`Scripts/launch_battle_baseline.command`。

编辑器退出修复：Mac UE 5.8 的导入通知可能在退出时触发 ICU 无效释放，已加入项目级清理并完成三轮复测。自动化关闭编辑器使用 `Scripts/shutdown_editor.command`（需本项目 MCP 编辑器已启动）；验证记录见 [EditorExit](Docs/Verification/EditorExit/README.md)。
