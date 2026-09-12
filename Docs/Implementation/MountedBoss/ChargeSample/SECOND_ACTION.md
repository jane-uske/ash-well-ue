# 用同一流程制作第二个动作

当前只注册冲锋；以下是复用方式，不代表第二招已经迁移或验收。先完成当前样本动态验收，再推广。

1. 使用同一骑士骨架制作有内容的 AnimSequence，并在 UE Montage 编辑器建立 Montage。使用 `MountedFullBody` Slot，保留同一鞍座和脚蹬约束，无须重建 AnimBP 或合并人马骨架。
2. Montage 总时长、准备/有效/恢复分界需与该招的现有 `AttackTuning` 一致；保留承诺方向和反打窗口。在需要的时间添加 `Mounted action phase` Notify 和 `Mounted weapon window` Notify State。`BuildChargeMontage` 是当前冲锋的专用构建脚本，不应把它的固定时间点原样用于其他招式。
3. 在 `/Game/AshWell/Combat/MountedChargeSample/DA_MountedSampleActions` 的 Montages 中添加对应键和 Montage。可用键为 `sweep`、`overhead`、`charge`、`body_check`、`rear`、`leap_shield`。当前只有 `charge`；增加一个键后，该招自动使用 Montage 时钟、窗口通知和标准姿势，未登记的招式继续原兼容驱动。
4. 先单招正常速度检查，再验证对应命中/闪避、取消、死亡和恢复，最后普通输入自然 AI 交锋。不要只验证资产存在或编译结果。

已经共用的部分：独立人马骨架、材质、挂点、AnimBP Slot、脚蹬 IK、Notify 类型、每招一次命中、刚性武器弧线扫掠、清理和重试。马匹其他专用动作仍需要对应序列或标准动画图设计，不能用登记一个空 Montage 冒充完成。

当前后台回归入口：

```sh
python3 Scripts/test_mounted_runtime.py --sample hit_charge dodge_charge sample_cleanup sample_pre_cancel retry input
```

`sample_cleanup` 在开启窗口后取消并在第二次窗口内死亡；`sample_pre_cancel` 在窗口开启前取消，检查淡出期间没有新的武器窗口。两者是测试驱动输入，不是 C 的普通输入录像。
