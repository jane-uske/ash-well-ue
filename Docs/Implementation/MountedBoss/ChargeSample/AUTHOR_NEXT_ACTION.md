# 第二个动作的制作接口（当前未迁移第二招）

当前实际样本资产：/Game/AshWell/Combat/MountedChargeSample/ReferenceProduction 下的骑士/马匹 ChargeSweep AnimSequence、两个 Montage 和 C_ChargeForwardDistance；登记在 DA_MountedSampleActions。主干仍保留原六招。

1. 以独立人马骨架制作两条等长序列，保持单一角色根位移。Blender的原生IK只烘焙接触姿态，游戏坡地由UE节点处理。SourceAssets/MountedReferenceProduction/Animation/HorseContactAuthoring.blend可重开修改落蹄目标，原始源动画不覆盖。
2. 参考 charge-timing.json 登记准备、Launch、Strike、Pass、ContactEnd、Brake、Recover、End及Commit时间。位移采样使用厘米与秒，必须单调，不能让AnimBP和Actor同时移动根。
3. 使用 AshWellMountedSampleTools.build_reference_montage 创建两个原生Montage；骑士Montage包含阶段Notify和武器NotifyState。build_distance_curve创建可在UE编辑的CurveFloat。原生AnimBP的MountedFullBody Slot播放动作，结束与中断清理均沿用现有规则。
4. 登记Montages与AuthoredActions；当前Boss规则适配仅将charge时序读自配置。制作第二招时需给该招接入配置时序并复核判定方式，不能仅填登记表便称已完成。
5. 先验证两条Montage进度、可见接触/判定、位移、恢复/中断/死亡/重试，再录制正常速度A/B候选。未经动态验收不迁移第二招。C始终使用自然AI、正式输入和完整血量。

当前A/B候选未获动态验收，本文件是可接续接口说明，不是推广批准。


## 2026-09-12 骑士比例派生步骤

当前骑士运行缩放为1.60，原冲锋源握柄轨迹按1.35制作。重导基础动画后必须先运行 `adapt_mounted_rider_proportions.py`（Blender），再在UE编辑器执行 `import_mounted_rider_proportions.py`。它用Blender原生两骨IK及Copy Rotation生成独立派生FBX，保持放大后的手臂长度与原世界握柄/刃向，重导既有冲锋AnimSequence；原生Montage、Notify与马匹序列保持。可编辑约束源位于`SourceAssets/MountedReferenceProduction/ProportionRevision/RiderGripConstraints.blend`。不要以扩大Sweep半径代替动画适配。任何再次改变骑士缩放都要更新这份适配并复测平地/坡地命中与闪避。这不是第二招制作授权。
