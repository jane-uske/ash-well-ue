# 冲锋横扫目标质量样本

更新：2026-09-12 凌晨。基线：`a8c455c65a3c19812d14f64b65ff217a87caeac0`，工作分支：`codex/mounted-charge-standard`。

**UE 标准动画流程已在当前游戏版本运行：有内容的 AnimBP、Montage、Notify / Notify State、IK 重定向与接触约束均已接通。A/B 当前版本连续录像已保存，仍是待验收候选；C 普通输入尝试因操作工具限制未形成合格交锋。未推广至第二招。**

## 三个验收节点

| 节点 | 当前证据 | 当前结论 |
| --- | --- | --- |
| A：资产与坐姿 | `Docs/Verification/MountedChargeSample/A/current-asset-uncut-silent.mp4`，25.01 秒、1280×720、1 倍速、无剪切的游戏内绕拍 | 四件新资产、坐姿、盾正面已可观察。盾牌偏大，侧面遮住骑士轮廓；持握、裙甲与接触仍待用户动态验收。该片段无音轨 |
| B：正常速度完整冲锋 | `Docs/Verification/MountedChargeSample/B/current-charge-uncut.mp4`，18.02 秒、1280×720、游戏音轨、1 倍速、无剪切 | 当前版本完整 3.55 秒 Montage、六阶段通知、一次伤害、掠过玩家、制动恢复后接回自然 AI。录制约 18 帧/秒；步态与制动观感未判定达标 |
| C：正常输入、自然 AI | `Docs/Verification/MountedChargeSample/C/ordinary-input-attempt-uncut.mp4`，QuickRecorder 单独窗口录像，约 237 秒 | 普通 E / Tab / R 曾实际触发，AI 自主出招；没有可靠跑位、闪避和反打，明确 rejected，不能宣称 C 通过 |

Mac 后来已解锁。当前 C 阻塞是操作接口：单独 Shift 返回 `keyPressIncludedNoNonModifierKeys`，没有已文档化的持续按住接口，期间还出现 native pipe closed 和录制应用 AX timeout。没有修改正常键位或添加自动玩家来冒充 C。QuickRecorder 实际录到了游戏窗口与应用音频，麦克风关闭；退出本次游戏后录制已结束，原件保留在桌面。其格式帧率不代表游戏实际性能。

旧 A 环绕录像存在 FrameGrabber 未绘制边缘，已标记 rejected。当前 A/B 按原视口尺寸捕获，检查的帧未再出现该问题。原始帧时间戳保留；最大捕获间隙 A 约 0.33 秒、B 约 0.15 秒，按实时时间保持上一帧，没有剪切、变速或生成补帧。

## 09-12 残留进程核查补充

此前录制期间存在四个 AshWell 崩溃报告残留，合计约 396% CPU；已核实来自 09-10 的导入/建图命令行任务及 09-11 20:47、20:53 的早期导入退出异常。09-12 已保留报告并清理，当前编辑器只读加载/退出复查正常。旧 A/B 帧率同时受到残留进程和录制器开销影响，不能作为清理后游戏的性能基准。此次清理不代表根治历史编辑器退出问题，详见 `Docs/Verification/CrashReportCleanup/20260912/README.md`。

## 本轮接入的资产

| 资产 | 游戏网格 | 骨架与接入 | 当前运行比例 |
| --- | --- | --- | --- |
| Gilded Sentinel | 90,000 三角面 | 保留独立骑士骨架（源 GLB 28 骨），完整金属/粗糙度/基础色/法线；SeatedIdle 与骑乘动作 | 骑士组件 1.35 倍 |
| Gilded Warhorse | 140,000 三角面 | 保留独立战马骨架（源 GLB 58 骨），完整贴图；原生 UE IK 重定向与 BlendSpace | 战马组件 1.3 倍 |
| 战斧 | 24,000 三角面 | 实际右手 Socket、真实网格刃缘采样；不扩大 18 cm 命中容差 | 总长 280 cm，握点至尖端约 196 cm，对齐保留的攻击距离 |
| 盾牌 | 24,000 三角面 | 左手 Socket；跃盾读取新盾真实包围盒下缘 | 高 180 cm，与旧盾的竖向尺寸一致；持握与穿插仍需最新版 A 实看 |

派生战斧 FBX 本体长 245 cm，盾本体高 105 cm；以上运行尺寸由独立组件缩放得到，不是改写源 GLB。原始高模、下载件与贴图保留。SourceAssets/MountedChargeSample/originals/provenance.json 记录 Downloads 原件和副本 hash；prepared_manifest.json、animation_manifest.json、poleaxe_edge_samples.json 记录派生关系。

高模与绑定版拓扑不同，因此保留贴图高模 UV，在派生模型转移已有蒙皮；没有要求重新生成或购买绑定。拟合距离不是变形质量验收。

## 实际运行的标准动画流程

- 骑士：SeatedIdle → MountedFullBody Slot → 标准骨骼控制 → 双脚 Two Bone IK → Output。当前 24 节点、0 编译错误/警告。
- 战马：原生 IK Rig / IK Retargeter 输出 Idle、Walk、Gallop，再由 1D 速度 BlendSpace、播放速率和 Slot 驱动 AnimBP。当前动画图 5 节点。
- 左右脚目标来自马骨架上的脚蹬 Socket，每次姿势评估后转入骑士组件空间。鞍座位置与方向跟随马背骨骼；人马骨架未合并。
- `DA_MountedSampleActions` 目前只登记 `charge → AM_SampleChargeSweep`。第二个动作可复用动画图、Socket、IK、Notify 类型和运行流程，见 `SECOND_ACTION.md`；未批量登记其他招式。
- 冲锋 Montage 是有内容的 3.55 秒连续序列：Prepare 0、Launch 1.15、Strike 1.73、Pass 2.10、Brake 2.20、Recover 2.85 秒。武器 Notify State 为 1.73–2.20 秒。
- 战斗阶段读取实际 Montage 进度。动画每个画面帧推进一次，位移保留碰撞子步；最后更新世界空间挂点后进行武器扫掠。较慢帧之间按真实刚性武器变换细分旋转路径，避免用一条直线漏掉弧线中间的玩家。
- 保留每招单次命中消费、无敌判定、伤害值、承诺方向、恢复和重试规则。取消、死亡、返回关闭窗口并停止 Montage；禁用已取消动作的后续通知，防止淡出期间重新开启窗口。
- 源动作没有可直接采用的根位移，本轮保留 Actor 作为唯一碰撞位移来源；Root Motion 与 Motion Warping 未开启。锁向前保留侧向 105 cm 的路线选择，锁向后不追踪玩家。
- 其余五招继续用旧动作驱动，经新骨架的标准 IK/骨骼控制兼容。它们没有被制作成五份新 Montage，也没有被宣称达到冲锋样本的目标质量。

## 马步态适配的修正

最初直接适配后的蹄骨轨迹最低约在地下 12 cm，该版本没有被视作完成。旧 CC0 马的 IK 蹄骨并不是腿链后代，不能直接用作连续 UE 重定向链。

在 `HorseIKSource/ConnectedSource.blend` 中制作独立的连续源骨架副本，并逐帧保持原世界空间动作；最大位置差异小于 0.001 cm。随后创建 `HorseRetargetConnected/IK_SampleHorseSource`、`IK_SampleHorseTarget`、`RTG_SampleHorse`，使用原生四肢求解器、FK 链和蹄底地面约束生成三份候选序列。原始骨架与动作未覆盖。

最新检查中的蹄骨最低点约为地面上 2–6 cm，抬蹄轨迹仍存在。这是骨骼点，不等于蹄面已经完全贴地，也不证明没有滑步。新版步态已接入，仍须在正常速度下观察关节折叠、蹄底接触和制动。

## 验证与仍未完成的工作

战斗实现版本的完整后台回归为 **27/27**：样本 15、默认旧六招 10、守井者 2。证据与当时源码/模块/资产 hash 在 `Docs/Verification/MountedChargeSample/CurrentBuild/verification.json`。之后仅更新录制检查流程和盾牌装饰面朝向；最新二进制另跑 **5/5** 针对性回归（冲锋命中/闪避、跃盾命中、窗口前取消、重试），见 `PostExportBuild/verification.json`。不要把前一版本 27 项写成最新二进制全量复测。两轮都校验原始文件未变，保留旧测试与断言。

仍未完成：

1. A/B 用户动态验收；盾牌侧面遮挡明显，比例不能由旧判定尺寸替代美术判断。骑士腿甲、握持与马蹄接触还需细看。
2. 马匹低速与制动时的滑步、关节运动和重量感仍未达到可宣布对标大树守卫的证据标准。
3. C 普通输入跑位、闪避、反打与重试的完整实战验收。已有失败尝试录像，不能替代成功交付。
4. 新骑士死亡后的离鞍/倒地表现尚未适配；清理窗口和停止动作有回归，视觉上可能仍保持骑乘姿势。
5. 其他五招的新骨架兼容姿势仍需视觉回归，尤其跃盾持盾；后台命中通过不等于贴地表演通过。Niagara、正式音频/UI 未在本轮进一步完善。

## 启动入口

- 当前样本：`Scripts/launch_mounted_charge_sample.command`。普通 E 进入、Tab 锁定、空格跳跃、Shift 短按闪避/长按冲刺、左右键攻击、R 重试。数字 3 为明确的单招检查，F5 恢复自然 AI；单招检查不能冒充 C。
- A 环绕：`Scripts/launch_mounted_asset_review.command -MountedReviewOrbit`。自动检查镜头、正常速度、AI 暂停。
- 原六招：`Scripts/launch_mounted_boss.command`，默认不进入新样本分支。
- 原守井者：`Scripts/launch_station_gate.command`。

## 回退

即时回到原六招使用原入口，不需要覆盖或删除新资产。基线提交保持为 `a8c455c65a3c19812d14f64b65ff217a87caeac0`；需要完整旧源码版本时，在新的独立 worktree 检出该提交并按 README 构建，保留当前工作目录，不对当前目录执行 reset/clean。

`Saved/MountedChargeStandard/Baseline` 保存初始 git 状态、已有 diff、Meshy 索引和 28 个原始导出文件的 hash；它不是完整项目备份。原始文件、新派生资产与失败候选分别保留。当前改动未合并或推送，也没有购买、重新生成资产或扩展世界/剧情/背包系统。
