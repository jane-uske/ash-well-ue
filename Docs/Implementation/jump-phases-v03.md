# 主角跳跃分段修正 — 2026-09-10

用户实机反馈：跳跃时双腿在空中反复蹬动。此前把完整 Meshy JumpRun 片段从约 2.1 秒压到 0.85 秒，并从起跳一直播放到结束，跑步步态被带进短腾空过程；这是素材选择和播放驱动的问题。

本次改用项目已有的 Quaternius Universal Animation Library Standard（CC0）。取 Jump_Start、Jump_Loop、Jump_Land 的适用姿势，重定向到厘米骨架，另存 `/Game/AshWell/Combat/JumpPolish/`，不覆盖原始 Meshy 文件。

- 起跳：约 0.13 秒，只完成一次收腿。
- 空中：上升和最高点保持收腿，下落时按垂直速度逐步伸腿，不按时间反复循环跑步或重新起跳。
- 落地：由 CharacterMovement 实际碰地触发约 0.27 秒的缓冲；移动、攻击、再次跳跃仍可衔接，不新增操作锁定。
- 空格跳跃、Shift 短按闪避/长按冲刺保持原方案。

构建脚本 `Scripts/prepare_hero_jump.py`，导入脚本 `Scripts/import_hero_jump.py`。源姿势检查、导出清单在 `SourceAssets/JumpPolish/`。验证以 `Saved/JumpPolish/` 的最终实机结果为准，源文件导出不等于视觉验收。

## 可用动作库

- [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)：已有本地 Standard 版；适合基础动作和快速接入，当前跳跃修正实际使用此库。授权副本在 `SourceAssets/AnimationTrial/License.txt`。
- [Epic Game Animation Sample](https://dev.epicgames.com/documentation/unreal-engine/game-animation-sample-project-in-unreal-engine)：官方动捕与移动系统示例，适合参考更写实的走跑、起停、转向、跳跃及其衔接，也支持迁移动作和系统到自己的项目。尚未整体迁入本项目。
- [Adobe Mixamo](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)：Adobe ID 可免费使用，角色与动作可用于个人和商业项目；适合快速挑选、预览和重定向人形动作。本次没有另行下载 Mixamo 素材。

制作原则：先审查原动作的运动意图、幅度和衔接，再重定向、接入游戏速度及落地条件；不以名称含 Jump 或 Run 作为直接上线依据。

测试关注：分段不能循环重启；起跳、腾空、落地三阶段都要观察到；落地时序以碰地事件时间记录，不能把碰地前整帧耗时算入落地缓冲。

最终验证：`jump_phases`、`hero_jump`、`hero_sprint` 实机用例通过。起跳/腾空/落地阶段均被观察到，空中采样不循环、无回退；四阶段截图和记录见 `Docs/Verification/JumpPolish/`。本次新增 Meshy 消耗为 0。
