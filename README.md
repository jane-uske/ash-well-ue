> **当前骑卫候选 c62edc2：声音、现有六招反馈和整体尺寸已同步。** [启动当前实战](Scripts/launch_mounted_boss_current.command) · [本轮交付/缺口/回退](Docs/Implementation/MountedBoss/SIZE_SOUND_MOVES_SYNC_20260912.md)。现有录像对应c2e44ae；最新蹄声采样修正待解锁补录。原作全招式、稳定60FPS、真人C均未验收。以下旧状态以本条和当前状态文件为准。

> **当前制作：声音、六招反馈、整体人马尺寸同步候选。** 用户已恢复制作，最新决定/验收入口见 [SIZE_SOUND_MOVES_SYNC_20260912.md](Docs/Implementation/MountedBoss/SIZE_SOUND_MOVES_SYNC_20260912.md)。原作完整动作仍有缺口，A/B待新版本验收、C未初测；下方暂停说明仅为历史。

# Ash Well — Unreal

## 当前进度（2026-09-12）

当前制作目标是以选定原片为参考的骑战 Boss“冲锋横扫”质量样本。**六招都保留，只有冲锋正在按新流程精修；其余五招有实现，尚非同等美术/动画完成度。** 人马独立骨架，AnimBP、Montage、Notify 与原生接触约束已实际运行。本轮允许按参考重排冲锋时序和调整地形后重新验证碰撞；不扩世界、剧情或背包。

- 运行入口：`Scripts/launch_mounted_charge_sample.command`。用户已暂停精修和继续放大，先做[招式与打击反馈调研](Docs/Implementation/MountedBoss/TREE_SENTINEL_RESEARCH_20260912.md)。A需返修、B待验收；真人C初测、最终验收均未完成。
- 制作接续、精确版本与已知问题：[原片复刻状态](Docs/Implementation/MountedBoss/ChargeSample/REFERENCE_PRODUCTION.md)，[交付索引](Docs/Verification/MountedChargeSample/ReferenceProduction/DELIVERY_STATUS.json)。状态文件优先于下方历史记录。
- 守井者入口：`Scripts/launch_station_gate.command`。原六招、主角、长剑、死亡重试和战斗基线保留。
- 专项录像使用显式A/B检查场景，不能当成普通输入完整Boss实战；功能回归不能代替视觉验收或真人C初测。每次比例/挂点修改需要新版本判定复测。
- 工作分支`codex/mounted-charge-standard`，私有远程[jane-uske/ash-well-ue](https://github.com/jane-uske/ash-well-ue)；不合并main。旧网页原型仓库独立保留。

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
