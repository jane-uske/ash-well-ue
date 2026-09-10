# AshWell 战斗技术交接 · 2026-09-10

这份文件保存本会话的技术经验与验证边界，供新会话接续。用户正在另行修改故事和世界观：旧剧情、章节顺序、角色动机不作为定稿；先读取用户最新故事版本，再决定场景变化。以下是日期快照，后续以当前代码和实机结果为准。

## 项目与工作边界

- 生产工程：`/Users/rare/dev/ash-well-ue/AshWell.uproject`。`/Users/rare/dev/ash-well` 是旧浏览器原型，不能当作 UE 生产工程。
- 本机引擎：`/Users/Shared/Epic Games/UE_5.8`，本轮 UE 5.8.2；开发环境需 `DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer`。遗漏会出现 Xcode Not Found 弹窗。
- 用户偏好：先把第一场 Boss 战做出可见、可玩的进步；保留确认过的角色外形；免费素材优先；Meshy 使用插件 API。先不打包，直到用户重新要求。
- 本次没有提交或推送 Git。工作区有大量已有修改和未跟踪文件，包含其他场景/故事工作；不要整体回退、清理或覆盖。

## 启动与回退

- 大门前游玩：双击 `/Users/rare/dev/ash-well-ue/Scripts/launch_station_gate.command`。
- 全章入口：`Scripts/launch_chapter01.command`；地图 `/Game/AshWell/Chapter01/L_Chapter01_Descent`。
- 操作：左键横劈、右键重砸、空格翻滚、Tab 锁定、E 交互、R 重试。
- 旧战斗对照：`Scripts/launch_battle_baseline.command`。它切换战斗行为，不会还原地图布局。
- 这是借助本机 UE 启动的开发版，不是可拷贝给朋友的独立安装包。
- 本地回退材料：`Saved/BattlePolish/before-battle-polish.zip`、`Saved/BattlePolish/before-layout.umap`。Saved 中备份不随 Git 自动传递，换机器须单独保存。

## 已接入内容与资产位置

- 玩家新增横劈、重砸、翻滚、受击动作；Boss 当前为重砸、近身踹击、拖锤短追击，半血后有踹击接重新蓄势重砸。具体时序/伤害见 `Docs/Implementation/battle-polish-v01.md`，这是可调的测试基线。
- 伤害跟随可见锤头或脚部扫掠，每次攻击最多命中一次；突进保留碰撞，出手前提交方向。
- 已接入池化火花、短冲击环、落点灯光、有限震屏、命中停顿与终结慢动作。时间缩放必须使用实时时钟恢复，并在 EndPlay 兜底恢复。
- 七条原创合成音效，来源见 `SourceAssets/BattlePolish/audio-manifest.json`。保留原 Suno 音乐及其单独记录的授权来源；本轮没有改变音乐使用权限。
- 资产：`SourceAssets/BattlePolish/`；UE `/Game/AshWell/Combat/BattlePolish`；制作脚本 `Scripts/retarget_battle_motion.py`、`build_battle_polish_geometry.py`、`build_battle_audio.py`、`chapter01_battleassets.py`。
- Meshy 原始输出及任务记录：`meshy_output/20260909_battle_motion_v01/`。预设 97 横斩、128 重锤、103 踹击、158 翻滚、178 受击；载体为 CC0 Quaternius 角色，仅供动作适配，没有替换游戏角色外形。
- 本轮预算上限 400，实际消耗 20；余额 2360 → 2340 是当时快照，不是实时余额。见 `Docs/Verification/BattlePolish/budget.json`。密钥不写入本交接或 Git；下一轮调用先确认凭据可用和预算适用范围。

## 容易重复踩的坑

1. 玩家原骨架为 `/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton`。FBX Armature 对象根名必须精确为 `SK_Intro_Protagonist_Rig`，否则会报缺少 root track；注意 Blender 多场景和 `.001` 重名。
2. 玩家渲染网格 Y 轴负缩放 `(1,-1,1)`，武器跟随 `hand_L`。可见左右和骨名存在镜像关系，不能只看名字交换左右手。
3. Meshy 翻滚包含约 3 米水平根位移；导出时去除水平根运动，由战斗代码控制位移，避免叠加和穿地。
4. Boss 仍为可姿态驱动骨架、刚性装甲、肢体 IK 和独立锤子；踹击采样用于适配驱动。没有完成整套标准人形 AnimBP/Meshy 重定向，不能误报为全部骨骼动作完成。
5. FBX 重导入的缩放覆盖曾不可靠。冲击环一度半径 5000 cm；已改源文件直径 1 米、导入倍率 1，并实测 UE 半径 50 cm。导入后查边界，不能只看参数。
6. 镜头数值测试通过不等于画面合格。低栏杆曾把相机挤进背部；已抬高探测起点。绕背、贴墙和近身必须再看实际渲染截图。
7. 扩大战斗区后，旧远景柱梁与栈桥侵入甲板。`chapter01_battlelayout.py` 对远景和支柱做有标签防重复的移位；章节运行时隐藏旧装饰 `DeepBridges_And_SuspendedWalks`。重新生成地图后检查并重做布局阶段，勿隐藏实际可行走桥梁。
8. Blender 多场景 GLB 导出使用 `use_active_scene=True` 并检查选择集，避免其他场景资产混入；检查相机、灯光和动作载体不作为游戏资产导入。

## MCP 与关闭编辑器

- UE 原生 MCP 端口 19854，脚本 `Scripts/chapter01_editor.py` / `chapter01_mcp.py` / `chapter01_tools.py`；启动就绪记录 `Saved/Chapter01/editor-ready.json` 必须匹配新进程，防止读到旧记录。
- 工具集完整名：`Users.rare.dev.ash-well-ue.Scripts.chapter01_tools.ChapterOneTools`。阶段包含 `battleassets`、`battlelayout`、`shutdown`。
- 客户端环境：`/Users/rare/.local/share/ashwell-mcp/venv/bin/python`；本地请求设置 `NO_PROXY=127.0.0.1,localhost`。遇到 `Session termination failed: 202` 不要直接认定导入失败，检查返回的 `isError` 和阶段产物。
- Blender MCP 使用 GUI 服务 localhost:9876，本机应用 `/Applications/Blender.app/Contents/MacOS/Blender`；CLI 包装器曾因找不到 `blender` 可执行文件失败。端口/进程在线状态要重新检查。
- 编辑器优先经 `Scripts/shutdown_editor.command` 调用原生 QuitEditor；它不强制保存未保存资产。测试可能更新 MCP SecurityToken，恢复时只处理本轮改变的字段，不覆盖整个配置文件，也不打印凭据。

## 已复现的编辑器退出崩溃

- 用户最近截图对应导入编辑器退出：CrashContext 为 `EngineMode=Editor`、`IsRequestingExit=true`、`UserActivityHint=EditorExit`；不要将它误归因于战斗 QA 游戏进程。
- 调用栈是延迟 Slate 通知销毁，经 `FICUTextBiDi` / `ubidi_close_64` 非法释放。诊断认为回调拖到 ICU 分配器清理之后才析构。只在 OnPreExit 清理、或只改用 QuitEditor，均未解决复现。
- 当前项目内绕过在 `Source/AshWell/AshWell.cpp`：只对 Mac UE 5.8 编辑器注册静态日志设备 teardown 钩子，在 ICU teardown 前两次 Reset 核心 ticker，处理析构时再次入队的回调。没有改安装引擎、关闭崩溃报告或删中文字体。
- 标记：`AW_EDITOR_EXIT late callback drain before ICU teardown`。升级引擎时复查实现及必要性，不无条件移植。
- 两次导入后原生退出、一次原 SIGTERM 路径，均退出码 0 且无新增崩溃目录：`Docs/Verification/EditorExit/after.json`。仅此退出问题得到回归验证，历史 GameFeatureData 等问题另算。
- 复现脚本 `Scripts/test_editor_shutdown.py`；完整说明 `Docs/Verification/EditorExit/README.md`。原始报告实际在 `/Users/rare/Library/Application Support/Epic/UnrealEngine/5.8/Saved/Crashes`。

## 验证边界与下一步

- 14 项实机专项、17 项未改规则检查通过；证据 `Docs/Verification/BattlePolish/runtime-probes.json`、`player-invariants.json`。普通攻击获胜、两种玩家招式、二阶段、现有结尾交互和速度恢复通过，见 `final-fight-checks.json`。这些结果不代表所有穿模或美术问题解决。
- 最新 `final-performance.json`：1600×900、约 150 秒，帧时间 P50 17.91 ms / P95 21.59 ms / P99 23.03 ms，19 次超过 50 ms，RSS 约 8.40 GB；`complete=false`。与旧实现说明中的前一轮数字区分，未达到稳定 60 FPS，也未做 30 分钟持续验证。
- 仍需：实机近身动作和握持/自相交修正、音效试听与混音、持续性能与连续重试、三名未参与开发者试玩。自动通关不能算真人试玩。
- 下一会话先读本文件与当前代码，确认用户最新故事，再继续首场战斗的视觉/操作体验验收。不要从已废弃故事扩建新章节，不要仅凭测试通过宣称“3A 完成”。
