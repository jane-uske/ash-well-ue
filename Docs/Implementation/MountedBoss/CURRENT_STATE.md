> 当前执行（2026-09-12）：用户恢复制作，要求声音、招式、原版大小同步。回退基线8a78f76；先整体人马1.30倍候选（非官方尺寸），校验真实碰撞/步幅/握柄；使用授权免费音源并按Montage Notify与实际接触触发；原六招保留，参考动作覆盖逐项接续。A/B需新版录像复验，C仍未初测，旧测试不覆盖本次改动。以下暂停记录已被本条替代。

> 最新决定（2026-09-12）：用户要求停止精修及继续放大，先调研普通大树守卫的招式与碰撞、挥剑、砍击、音效反馈。当前代码074cf9a，骑士1.60/马1.30仍被认为偏小；人马整体再次放大未实施。调研及缺口见[TREE_SENTINEL_RESEARCH_20260912.md](TREE_SENTINEL_RESEARCH_20260912.md)。A需返修、B未验收、C未初测；无本轮UE/录制进程驻留。下方制作记录为历史过程。

> 2026-09-12 19:20：骑士体量反馈进入A返修；六招仍保留，仅冲锋是本轮精修对象。骑士1.60比例候选及座位/脚蹬缩放适配正在实测。已解锁并取得首份时间戳审计合格的原生环绕录像；旧锁屏阻塞已解除。新尺寸判定与A/B仍待验证、C未初测。详见ChargeSample/REFERENCE_PRODUCTION.md。

> 2026-09-12 17:55 接续入口：`ChargeSample/REFERENCE_PRODUCTION.md`。Meshy累计140积分，四件构件已接入；独立人马原生Montage/Notify/坡地IK已实机运行，死亡已能侧倒。六招16项、坡地16项、生命周期相机6项、守井者/主角6项分版本通过。1080p预热后平均14.29ms、p95 18.47ms，未达稳定60fps。A/B未验收、C未执行；最新录屏受Mac锁屏阻塞，已请求解锁。运行候选f87f955已推送（含26个新增LFS对象约291MB）；main未合并。

# Mounted Boss 当前状态

## 当前制作轮：原片复刻（2026-09-12）

用户已批准并要求执行新的[原片复刻计划](ChargeSample/REFERENCE_PRODUCTION.md)：允许重排冲锋时序、建设参考中的起伏地形并重新验碰撞，所需模型优先 Meshy，首批 200 / 总计 964 积分。工作分支不变，制作前候选已提交为 `db1ee62`。旧文档“不改时序/地形”的限制已被本次授权替代；其他五招保留而不推广。当前 A/B 待验收、C 未完成，制作过程与版本证据以新文档接续。

## 历史第二轮（2026-09-12，原片优先修正）

工作分支 `codex/mounted-charge-standard`，已推送基线 `bd791aa`；本轮新改动仍在原工程，未提交/推送，不合并 main。已按用户“直接在旧版上面改”“先参考原视频，再来制作”执行：重查普通大树守卫 19.3–25.1 秒，修正高位架柄、压身低扫、抬起收势，并让准备阶段保持有限推进。UE AnimBP / Montage / Notify 与原战斗规则保留；马蹄 Foot Placement 试验未采用，停止扩展。

新版正常速度对照：`Docs/Verification/MountedChargeSample/Round2/ReferenceFirst/reference-vs-current-1x.mp4`。未剪辑窗口原片和对应模块/资产记录位于该目录 `After/B/`。对照仅作固定时间平移，无变速/插帧；原片含单招检查、等待和恢复自然 AI，玩家没有进行真人交锋，不能称 C。旧 A/B 证据不代表最新修正已验收。

A/B 仍待动态验收；新版有动作轮廓进展，马匹制动、身体重量和比例感仍未达到普通大树守卫目标。真人初次反馈只有约一分钟有效按键记录且无对应录像，10–15 分钟 C 初测与最终 C 均未完成。新骑士死亡离鞍姿态仍未适配。一次回归启动在布料首帧渲染断言崩溃，报告已保存，自有残留进程已清理；单独重试随后通过，不据此宣称启动崩溃已修好。

本轮依据、详细新旧测试归属及回退方式见 [ChargeSample/ROUND2.md](ChargeSample/ROUND2.md)、[参考比较](ChargeSample/REFERENCE_COMPARISON.md) 和 `Docs/Verification/MountedChargeSample/Round2/progress.json`。历史段落以下保留，不能覆盖当前验收状态。

## 历史阶段切换（2026-09-11，冲锋横扫目标样本）

用户已恢复制作，采用 UE 标准动画设施优先。当前新资产冲锋已实际运行 AnimBP、Montage、阶段/武器窗口 Notify、原生马匹 IK 重定向，并交付当前版本 A 绕拍与 B 正常速度完整冲锋录像。A/B 待动态验收；C 普通输入尝试已录下但受工具按键/连接限制，未形成合格交锋，明确未通过。原六招默认入口、守井者与原件保留，未推广第二招。详见 [ChargeSample/STATUS.md](ChargeSample/STATUS.md)；完整回归 27/27 与最后录制/盾朝向修改后针对性 5/5 分别存于 CurrentBuild / PostExportBuild。以下原暂停与测试记录是历史版本证据。

审计日期：2026-09-11。**当日制作已按用户要求暂停，仅整理提交与私有远程备份；后续录制和战斗打磨等待下次继续。** 六招、Debug 和空中中断清理已实现；**修正真实 UI 问题前的同一构建 27/27 自动化用例通过，原守井者 2/2 指定回归通过；当前新增 Debug/暂停修复的真实 UI 日志复测 13/13 通过，最新构建的 9/9 必要战斗回测与 2/2 守井者回归通过；新录制器只完成编译，Mac 锁屏阻止实际录制验证。整体验收仍未完成**：马步滑移、全部招式自然交锋、人类读招学习与完整未剪辑交付录像尚不足证据。源文件快照、每例日志和当前未通过项见 `qa_matrix.json`。

## 项目与本轮边界

主项目为 `/Users/rare/dev/ash-well-ue`，运行关卡 `/Game/AshWell/MountedBoss/L_MountedCourtyard`。网页目录 `/Users/rare/dev/ash-well` 不承担本轮交付。独立关卡已存在，现有主角、长剑、生命、体力、死亡重试和 HUD 被复用；原守井者仍由原入口启动。

目标仍是以普通大树守卫为参考的完整骑乘 Boss 实验。当前优先验收三种结构差异明显的攻击——冲锋横扫、近身马体攻击、跃起盾砸——是整场战斗的关键样本，**不是把完整目标缩成三招**。本轮代码已包含六种攻击及连招、阶段、移动、脱战、死亡和胜利；后续完整参考动作族与魔法反制的覆盖情况见 `move_catalog.json`。

本轮不扩大世界、故事、NPC、背包，不替换守井者关卡，不打包发布。用户要求今天停止制作并分组提交、创建远程仓库；现已在 `main` 保留既有工程快照 `0c6eae1`、骑战实现与资产 `4c293f8`、制作及测试工具 `b481620`，验收文档随其后的文档提交保存。原始 `65a681b` 历史保留。私有远程为 [jane-uske/ash-well-ue](https://github.com/jane-uske/ash-well-ue)，旧网页仓库独立保留。工作中的游戏源文件未因拆分提交改变；具体范围见 `version_control_handoff.json`。完整交付录像仍缺失。

## 四类状态定义

- **已验证可复用**：有本地源文件与对应的实际运行或资产证据，且范围写清。
- **需要修改**：有实现，但行为、视觉、证据强度或新需求尚有缺口。
- **缺失**：当前没有这项交付或对应系统。
- **未能验证**：可能存在或正在制作，本审计没有足够证据给通过结论。

脚本通过只证明其断言；不会自动证明马不滑步、动作自然、玩家看得懂或人类实战可赢。

## 逐项审计

| 项目 | 已验证可复用 | 需要修改 | 缺失 | 未能验证 |
|---|---|---|---|---|
| 引擎与工程 | `AshWell.uproject` 指定 5.8；真实游戏日志记录 UE **5.8.2-56702186**，模块与原生窗口可启动 | 持续维护同一源码/构建/运行证据对应 | 本轮独立可分发包；本轮不制作 | 跨机器、打包运行与持久性能未验证 |
| 玩家移动、锁定 | WASD、Ctrl 慢走、短按 Shift 松开闪避/长按冲刺、空格跳跃；骑乘场景独立镜头与速度分支 | 冲锋擦身镜头、贴身可见性需要人工录像；一般输入 fixture 不能代替 Shift 键路径测试 | 没有单独的持盾玩家或可骑乘玩家；不属于本轮需求 | 新 Debug 干预后镜头恢复自然 AI 的完整表现 |
| 翻滚、无敌与承诺 | 当前无敌为翻滚开始后 `[0.07,0.37]s`；旧五招对应受击/闪避 fixtures 均留有通过记录；体力不足和晚后摇缓冲有验证 | 六招命中/闪避对照已通过；精确无敌边界仍待验证；无碰撞的空间闪避不能证明无敌窗口 | 精确窗口前/内/后边界回归尚无本轮完整矩阵结果 | 按键到动作可感知延迟、低帧率下稳定性、人类读招体验 |
| 玩家攻击 | 横斩/重击使用可见剑刃分段扫掠；旧版 `light/heavy/miss` 验证 40/55 伤害与空挥；骑乘轻击消耗 12 体力，守井者长剑规则保留 | 当前 light/heavy/miss/input fixtures 已回归；自然交锋中的容错与互相打断仍需评审 | 重击输入缓冲、早段取消没有实现；目前只提供晚后摇排队 | 低帧率动画/判定一致、所有接触位置容错 |
| 生命、体力与恢复 | 玩家 100 生命/体力，轻击 12、重击 34、闪避 28；休息恢复 26/s；旧 `input` fixture 检查不能重入和零体力动作被拒 | 数值以一次真实交锋调校，不能将旧 fixture 的零压力耐力曲线作为平衡结论 | 没有耐力击破、独立装备属性；本轮不扩系统 | 熟练玩家击杀用时、失败原因与学习曲线 |
| Boss 状态与 AI | 六招采用距离/角度/冷却/状态筛选，900 HP，半血阶段、有限连招、返回出生点；旧阶段/返回均留有实际证据 | 冲锋改横扫、真实马体 `BodyCheck`、离地 `LeapShield` 已实现；脚本交锋曾发现贴马尾 AI 无应答，已增近尾蹄击回应及 Approach 阶段切换；最终 loop 产生 4 次 Boss 攻击并打败玩家 | 普通大树守卫全动作族尚未全部制作；魔法反制没有系统 | 自然选出全部六招、横扫接下劈连招独立覆盖；loop 只观察到冲锋/蹄击与 P2 |
| 碰撞与伤害来源 | 当前马体阻挡、武器/刃缘扫掠、马肩撞与范围来源分离；近身主动马体伤害只由真实马身箱扫掠产生，普通贴身不伤害；最终 body 前方靠近回测通过 | 跃盾使用根落地与盾底距地面门限共同开启一次范围冲击；尚无独立盾牌接触扫掠，视觉接地与容错需逐帧核验 | 没有盾的真实格挡/反射魔法系统 | 所有边界角度、场边、跳跃高度、慢帧下穿透/多重伤害 |
| 骨架与动画 | 马使用真实骨架及 Idle/Walk/Gallop/Death；骑手独立 `SK_MountedRider`，保持已有驱动骨名；座位跟 `Torso2`；资产记录和旧 runtime 均可核查 | 马无专用转弯、停止、扬蹄片段；骑手主要为程序双骨求解。Gallop 相位距离曲线已接入；最终 movement 支撑蹄漂移代理量仍 **80.92 cm/s**，采样 10.23 秒，不能判无滑步 | 写实马材质/模型、完整骑手骑乘表演包、精修转向/受击动作 | 新动作下足底、缰绳、鞍座、手与柄的连续同步；静态资产验证不是动态视觉通过 |
| 声音、VFX、震屏 | 复用 Swing/GroundSlam/Kick，蹄声改为骨骼下降接地事件，玩家命中使用较小 Burst；旧样本 `min_dilation=1` | `Kick` 作为马蹄音仍需听感匹配；新身体冲击/跃盾落地必须各自同步；灰尘与轻震不能挡动作 | 专门的骑乘战配乐与完整材质接触音组 | 本审计未做人工实时听音；蹄声触发计数不等于音色和同步验收 |
| 构建与启动 | `Scripts/launch_mounted_boss.command` 使用项目 UE 5.8 本地原生游戏窗口；`Saved/MountedBoss/build.log` 记录 00:22 左右构建成功 | UI 修复前六招/Debug 构建和 27 例报告已归档；新暂停/热键修复真实 UI 13 项通过，后续录制改造后必要战斗回测 9/9 通过 | 发布包不属本轮 | 跨干净工作区重现和普通 UI 录制还未完成审计 |
| 性能 | 真实日志存在；Debug 的 session_end 已开始记录实际帧数与帧间隔。部分未录制样本 p50≈8.33、p95≈8.49、p99≈8.58 ms，当前不是配置 60 FPS 的实测证明 | 需要在最终场地与自然 AI 下采集帧时、1% low、最差帧与加载卡顿；早期脚本运行时长不代表 FPS | 本轮完整骑乘战性能报告 | 持续帧预算、GPU/CPU 瓶颈、持续运行温度；120 Hz 附近短时采样不等于稳定高帧率保证 |

### 可定位的源文件

- 玩家操作/攻击/体力/镜头：`Source/AshWell/AshWellCombatCharacter.cpp` 的 `SetupPlayerInputComponent`、`Attack`、`HeavyAttack`、`Dodge`、`IsInvulnerable`、`UpdateAttack`、`UpdateCamera`、`Tick`；状态声明见同名 `.h`。
- 骑乘入战/返回/运行 fixture：`Source/AshWell/AshWellMountedPlayer.cpp`。
- Boss 规则/移动/判定：`Source/AshWell/AshWellMountedBoss.cpp` 与 `.h`。
- 马的运动相位、落蹄、鞍座和骑手求解：`Source/AshWell/AshWellMountedBossVisual.cpp`。
- 重试：`Source/AshWell/AshWellIntroGameMode.cpp::IntroRestart`；界面：`AshWellIntroHUD.cpp::DrawCombatHUD`；局部反馈：`AshWellBattleFX.cpp`。
- 主角实际资产还会优先使用 `JumpPolish` 的起跳/空中/落地适配；不能只看 `hero-complete-v02.md` 认定当前跳跃仍为旧单片段。

## 真实 UI 新发现与当前版本差异

自动化全绿后的普通 UE 游戏窗口实际按键发现两个问题：F1–F8 与 Development 构建的 `PlayerInput.DebugExecBindings` 冲突，会把场景切成 Unlit/ShaderComplexity 等引擎显示模式；按下暂停的同一帧仍可能推进约 0.008 秒状态时钟。它们没有被调用动作接口的 fixture 覆盖，因此保留为本轮真实失败，不能用前面的绿灯忽略。旧 session 与审查报告已归档 `Docs/Verification/MountedBoss/debug-ui-initial-failure/`：13 项日志检查中 12 通过、暂停时钟失败，漂移为 0.0079739 秒。

当前修复在本玩家实例移除冲突的 F1–F8 引擎 Debug 绑定，在 Boss 与骑乘玩家 Tick 检查暂停后早退；不改全局项目输入配置。修复后实际 UI 已复测：连续暂停 13.4988 秒，world 与 Boss 状态时钟漂移均为 0，状态/攻击序号不变；F3 慢放与恢复、F4 复位、F5 后自然 AI 继续攻击有日志。`Docs/Verification/MountedBoss/debug-ui-fixed/verification.json` 13/13 检查通过，原始 session 一并归档。之后还更新了 F8 录制器：呈现帧抓取、线程池编码 720p/24fps 目标、准确音频输出路径、结束清理；R 重载分段。新构建已成功。旧录制方式出现冻结/旧帧画面，预期录制目录没有 WAV；该 103.70 秒失败片段没有作为交付录像，失败元数据见 `Docs/Verification/MountedBoss/recording-initial-failure/`。新录制器尚未实际测试：启动前 Mac 锁屏，CUA 明确需要用户手动解锁；用户随后要求今天停止制作，录制验证已延期。不能把代码编译通过写成音视频录制通过。

三个关键攻击的 hit/dodge、cleanup/retry/loop 共 **9/9** 必要回归已在锁屏期间通过；这是 UE 自身渲染 fixture 和断言，不是当前普通窗口的人工观察或按键试玩。独立归档 `Docs/Verification/MountedBoss/final-runtime-ui-fix/` 的 run ID 为 `20260911-012503-a147e821`，9 例文件齐全，10 份 Debug session（retry 两份），新源/模块 hash 和构建日志齐全；采集时没有 Source 文件晚于 run 开始。

新模块 SHA-256 为 `19323b736e3560a3602423e0898f68ee86f22c5bd1be5ce11abb78884b827640`。三个必选受击样本分别剩 68/81/62 HP，各只一次对应来源接触；闪避各保留 100 HP。新跃盾实际 Z 样本峰值 141.50 cm，接触时 Active=0.68704 秒、Actor Z=0、盾底代理间隙约 8.00 cm。最新 loop 再次为 15 次玩家命中、1 次闪避、4 次 Boss 出手，P2、Boss 300 HP、玩家死亡。具体原始值见新目录 `evidence-summary.json`，不得用两次不同采样峰值差异推断实际跃高被改动。

两版证据分开保存：旧 27 例证明六招基础动作与完整 fixture 集，新 9 例证明 UI/暂停/录制工具改造后受影响路径回归；最新同模块的守井者两例也再次通过，归档 `Docs/Verification/MountedBoss/baseline-runtime-ui-fix/`；没有合并声称最新构建重跑了全部 27 例。新录制器的音视频文件仍未实际验证。攻击时序、AI 参数和判定参数未因此改变，但之前 27 例的源/模块 hash 仍属于修复前版本。

`Docs/Verification/MountedBoss/final-runtime/` 是**UI 修复前 27 例的保留档案**，不覆盖；之后的新报告使用独立目录。最终最新代码可验证范围以新报告为准。

## UI 修复前同版本运行证据

归档目录为 `Docs/Verification/MountedBoss/final-runtime/`，报告 run ID 为 `20260911-005158-f321083f`。27 例包括玩家轻/重/空挥、马身阻挡、六招各自受击/闪避、移动、相机、脱战、阶段、胜利、重试、动作输入、强制冲锋运动、死亡、清理、脚本交锋。**27/27 指上述自动化断言，不是本目录所有验收要求都通过。**

- 每例 `started/result/probe/engine.log/screenshot` 齐全，匹配 28 份 Debug session；retry 有关卡重载前后两份日志。在该次采集时源码与 run 开始相比没有 Source 文件变更；系统清单记录当时源码和模块 SHA-256、UE Build.version、构建日志。
- 跃盾实际 Actor Z 的 trace 样本峰值 145.38 cm；伤害接触时 Active=0.68265 秒、Actor Z=0、盾底代理距地约 8.00 cm，最终玩家 HP=62。该高度来自实际位置，**不是 `maximum_leap_height_cm` 的期望抛物线**。闪避对照 HP=100、一次翻滚；它没有接触事件，是空间避开，不能单独证明无敌帧挡住盾砸。六种闪避中，只有 rear 记录了 1 次接触被无敌拒绝；其余五种为无接触的空间避开。
- `loop` 使用强制冲锋起手，后续自然 AI 与脚本玩家交锋 26.07 秒，玩家 15 次命中、1 次闪避，Boss 4 次出手，半血阶段已观察；最终玩家死亡、Boss 300 HP。它修复了此前尾后无限追打而 Boss 不回应的具体漏洞，不是人类熟练通关证据。
- `victory` 对固定 Boss 23 次普通攻击并进入胜利；`retry` 实际新实例玩家 100/Boss 900、Idle、未入战。`cleanup` 验证暂停伤害关闭、空中调试取消、空中死亡后落地、重复攻击 ID 拒绝及重置清理。
- `camera` 在五个固定位置 300/300 目标投影在画幅内、环境重叠为零；马体相机通道被忽略，仍须人工看近身遮挡。`body` 正前方最小中心距离 142.048 cm=马箱半长 108+玩家半径 34+0.048，穿透累计为 0、没有被动马身伤害。
- movement 约行进 5145 cm，支撑足滑速代理仍 80.92 cm/s。该问题保持“视觉需要修改”，不会因为 movement 脚本通过而改成无滑步。
- 未录制 loop 的 3108 帧，平均帧间隔 8.689 ms，p50/p95/p99=8.335/8.493/8.568 ms；这是含 fixture/日志开销的短时样本。retry 新实例只有 19 帧，p95/p99=389.09 ms，加载尖峰保留。没有 GPU 成本或完整持续温度测试，不能从配置 60 推断实测 60，也不能把 p99 倒数称为 1% low。

设备证据：Apple M5 Max，128 GiB，macOS 27.0 (26A428)，UE 5.8.2 CL56702186；见 `system-and-source.json`。原守井者 `battle_light` 与 `battle_dodge_charge` 两例的早期回测日志/截图在 `Docs/Verification/MountedBoss/baseline-runtime/`，最新模块再次通过的结果在 `baseline-runtime-ui-fix/`；旧测试通过 chapter01 的 WardenProbe 执行，覆盖这两种行为，不等于完整守井者人工复玩。

## 已读运行证据及限制

| 证据 | 记录结果 | 只能证明什么 |
|---|---|---|
| `Saved/MountedBoss/runs/20260910-234944-6224e3d9/test-results.json` | 7 例，早期 charge/shield 接触失败 | 保留失败历史，不能称首次全通过 |
| `Saved/MountedBoss/runs/20260911-000557-259053c6/test-results.json` | 22 例，20 通过；body 与 disengage 失败 | 旧版完整 fixture 运行；其中胜利是对固定 Boss 反复普通攻击，input 是脚本动作调用 |
| `Saved/MountedBoss/runs/20260911-001817-23c88ebe/test-results.json` | body/disengage/death/movement/natural_charge/hit_charge/dodge_charge 共 7 例通过 | 修复后的针对性回测，不等于最终版本 22 例同时通过 |
| `Saved/MountedBoss/runs/20260911-002318-0cb02cc6/test-results.json` | movement 通过 | 运动/资源/边界断言，不证明无滑步 |
| `Saved/MountedBoss/runs/20260911-002603-0160a49d/test-results.json` | movement/hit_sweep/hit_charge/hit_rear 共 4 例通过 | 旧五招分支样本；早于本次三种关键动作修订 |
| `Saved/MountedBoss/runs/20260911-000557-259053c6/camera/probe.json` | 5 个位置，300/300 目标投影在画幅内，环境相机重叠为 0 | 目标点在画幅内与无环境重叠；**没有证明玩家/武器无遮挡，也没有模拟自然高速擦身** |
| `Saved/MountedBoss/runs/20260911-000557-259053c6/retry/probe.json` | `retry_observed=true`，新实例玩家 100、Boss 900，Idle，未入战 | 实际关卡重载复位；新六招版本需要重跑 |
| `Saved/MountedBoss/runs/20260911-002603-0160a49d/movement/probe.json` | 行进约 5147 cm，72 次落蹄，支撑样本 5.07 秒，支撑漂移代理值约 98.9 cm/s | 真实骨骼与运动相位有输出；此量与资产离线分析提示仍需改滑移，不应忽略 |

新增六招的中途报告继续保留：`runs/20260911-004008-369e7435/test-results.json` 中冲锋/马肩撞接触失败；当时跃盾虽通过扣血断言，画面仍是盾离地伤害。随后加入盾底接地门限，`runs/20260911-004436-c0210b43/test-results.json` 的跃盾正确失败，暴露骑手手臂伸不到目标；调整侧倾与握点后，`runs/20260911-004856-0a7caa28/test-results.json` 的跃盾受击/闪避通过，但该报告的 loop 死亡结束条件导致超时，仍不是全通过。最终完整报告必须来自之后一次同版本运行。

`natural_charge` fixture 会调用 `ForceAttack("charge")`，然后让马完成运动与判定；它不是“自然 AI 自行决定冲锋”的证据。`loop` 同样强制冲锋起手，之后由 Boss 自然决策、脚本玩家通过真实移动/攻击/翻滚接口交锋。`victory` 是对固定 Boss 的真实普通攻击扣血与胜利流程，`input` 是动作接口断言。三者都不能替代人类按键试玩、完整自然开场选招或熟练玩家获胜录像。

完整逐例索引、旧失败和本轮待验证项见 `qa_matrix.json`。根目录下 `Saved/MountedBoss/test-results.json` 会被后续运行覆盖；引用历史结论时优先引用上表有 run ID 的路径。

## 当前可见问题

已检视更早场景截图，以及本次 27 例实际归档的 `Docs/Verification/MountedBoss/final-runtime/hit_sweep/screenshot.png`。归档画面仍可见低面数灰马、简单圆盘盾和柱廊/树占位造型；地面大面积单色、地平线黑带、偏暗骑手/手部和写实主角之间的材质落差明显。当前应称**可检验战斗结构的制作中版本**，不能称已达到古老奇幻写实美术或第二个更高质量 Boss 的最终结果。

静态截图不足以评判连续马步与武器轨迹。`Saved/MountedBoss/Capture/` 中已有 fixture 截帧序列，尚无本审计已核验的交付用未剪辑完整交锋录像。最终需要同时展示失败、读招躲过、恢复反击、胜利与快速重试。

资产代理已实际检查新跃盾截帧 `Saved/MountedBoss/Capture/hit_leap_shield/frame-0033.png`、`0035`、`0037–0044`：能看见下降；扣血时盾下沿靠近地面与落蹄；盾没有改尺寸，未见明显手与盾脱开或离鞍跳变。暗部细小手指/握柄仍未验证。这是局部视觉进展，既不消除马步滑移，也不证明全部六招与镜头已经达标；正式归档还需明确这些帧的生成版本。

## 资产来源与已核验范围

`asset_manifest.json` 由资产审计单独维护，记录 11 个资产族、原始来源、许可证据、转换文件、UE 路径与未使用候选。马来自 Quaternius 的低面数 CC0 动物包，原网格约 1093 顶点；有真实动画骨架不等于写实美术。骑手源是已有 Hunyuan3D 本地生成守井者的独立骑姿适配，不能误写成新的 Meshy 骑手。主角继续复用 Meshy 与社区动作结合的本地资产及最新 JumpPolish 适配。

马、社区动作与 Poly Haven 环境材质的 CC0 原文有记录；Hunyuan 2/2.1 官方条款及 hash 已归档，但其他生成管线依赖尚未全部审完。Hero 的生成时账户计划和适用输出条款没有完整证据，不能只凭曾付积分就标成 CC0。具体未知项保留在资产清单中，不在本轮推断全球发布授权。

资产转换误差检查仅证明转换一致：极小坐标误差不能抵消运行中的支撑蹄滑移。后续相位曲线离线估计即使降到约 74.79 cm/s，也仍不是 UE 运行或视觉验收结果。

## 守井者保留与回退

已对照 `Saved/MountedBoss/before-manifest.json` 重新计算，以下 SHA-256 与骑乘改动前记录相同：

| 文件 | SHA-256 |
|---|---|
| `Source/AshWell/AshWellWarden.cpp` | `de37126df17e546d7231241a9111bbeec259f66f5f0beb705dc1fc4b7c9570ce` |
| `Source/AshWell/AshWellWarden.h` | `ee8e0c963abf3b5c79e0394b78208358ddeee811d208add91537ebf4b5d28c1c` |
| `Source/AshWell/AshWellWardenVisual.cpp` | `26d4679fc30eeb76474b5d1a514384e44a1633b73aea28ed6605c48868216215` |
| `Source/AshWell/AshWellCombatArena.cpp` | `a185112ce8c4a134b020724774ebe648617ff44c51444218ac3aa71bbf4ebf14` |
| `Source/AshWell/AshWellCombatArena.h` | `f72d146944a5f6ce3414434c53c58eda6c853c3c19ddc0b08e3a6dcf8dc14a3b` |
| `Scripts/launch_station_gate.command` | `3ef5ec28cacd7a9273c6032b9cc9e552a91d03be81d7e3f5fb8d7a1deec63714` |
| `Config/DefaultInput.ini` | `6c0317c4cbc9ffd1cfc19acfd7ed752b28428de621d0c3a36245971ee4a0b1fb` |

`Saved/MountedBoss/before-mounted-20260910-233144.zip` 包含 42 个源/配置/启动脚本条目，**不含 `.umap` 或完整 Content 资产**，不是完整项目备份。共享玩家、HUD 和动画文件仍有本轮与先前其他工作改动；`battle_light`、`battle_dodge_charge` 已完成实际回归；完整 Shift 点按/长按矩阵与原入口人工完整复玩仍未在本轮全部完成。不要为了回退骑乘实验整体解压覆盖并发工作。

## 下一次更新的收口条件

1. 同构建 27 例与源文件 hash 已归档；后续若再改代码，须重新界定受影响的测试，不能继续使用此报告冒充新版本通过。
2. 优先实看冲锋横扫、近身马体攻击、跃盾落地三种关键攻击；其余横扫、过顶、前蹄落地、阶段与连招也必须保留并验收。
3. 验证 Debug 开关、暂停/慢速、可重复单招、碰撞显示、重置与恢复自然 AI；调试慢速不能混入正常实战通过数据。
4. 补未剪辑交锋录像并标注输入来源；人工评定动作、镜头、声音。短时帧时已保留，持续性能及加载尖峰仍需单独评估。
5. 更新本目录四个技术文件及独立 `asset_manifest.json`，再记录实际提交或仍未提交状态。

文档冻结：当前代码/9 例目标回归、13 项 UI 日志复测、最终模块 2 例守井者回归均已归档。用户要求今天停止制作后，仅整理分组提交及私有远程备份，未继续修改游戏代码或运行新一轮游戏验收。下次继续制作时仍需验证新录制器并交付视频与听感结论。
