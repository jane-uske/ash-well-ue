# 主角动作与布料接入 v02 — 2026-09-10

承接旅人长剑 v01；地图与剧本暂停修改。本轮以实际 UE 角色为交付对象。

## 操作

- WASD 常速跑；按住 Ctrl 慢走。
- 空格跳跃；Shift 短按并松开触发翻滚，持续按住 0.20 秒进入冲刺，松开冲刺只停跑。
- 跳跃采用 CharacterMovement 重力、碰撞与落地，单次起跳，不提供空中重复跳或翻滚。
- 左键横斩、右键重击；Tab 锁定、E 交互、R 重试。

## 制作记录

Meshy 取得 Idle、Run、Jump、Roll Dodge、Sword Slash、Charged Slash、Combat Walk 共 7 个动作候选，每个 3 积分，实测余额 2355 → 2334。此前已有的 walking.glb 继续可用。

新建 `SourceAssets/HeroComplete/` 与 `/Game/AshWell/Combat/HeroComplete/`。从原旅人模型派生，厘米单位，骨架缩放 1；把历史上的 Y 镜像烘入模型与骨架，避免实时布料使用负缩放。材质恢复常规 PBR 与法线贴图。

走跑、跳跃与翻滚取 Meshy 候选；持剑戒备、横斩和重击保留已校验的长剑握持及伤害时序，Meshy 攻击候选也保存在新目录，未仅凭名称就替换。没有新造一套面孔，仍基于已确认的旅人外观。

披风使用 Chaos Cloth：肩领固定、下摆活动，躯干与双腿胶囊碰撞，低强度风。需要实际模拟输出和运动画面共同验证，组件存在不等于布料验收。

## 复现与回退

- `Scripts/prepare_hero_complete.py`：后台 Blender 构建单位与镜像正确的角色及原动作。
- `Scripts/retarget_hero_meshy.py`：转换保存的 Meshy 动作，无网络付费调用。
- `Scripts/import_hero_complete.py`：导入独立资产，创建材质、碰撞及布料。
- `Scripts/test_battle_runtime.py`：包含 `hero_jump` 与走跑、挥剑和翻滚实际运行用例。
- `Scripts/launch_station_gate.command`：大门前运行；加 `-HeroBaseline` 对照上一版角色。
- 任务、下载与成本记录：`Saved/HeroComplete/motion-tasks.json`、`balance-before.txt`、`balance-after-motions.txt`。

实测 9 项运行用例全部通过；跳跃最高离地 73.2 cm，固定人物姿势的风动测试有 5016 个可动布料顶点，单帧下摆最大位移约 1.06 cm，渲染映射与求解器输出均存在。截图和 5 秒风动片段见 `Docs/Verification/HeroComplete/`。

验证结果以本轮最后一次 `Saved/HeroComplete/runtime-tests.log` 和实际截图为准。既有模型尚无独立手指骨骼，脸部不是影视级面部绑定。本轮不打包。

## 已确认的冲刺补充

用户确认使用 Shift 短按闪避/长按冲刺；空格跳跃、Ctrl 慢走保留。判定使用真实时间，避免命中慢动作改变长短按手感。冲刺速度 360 cm/s，普通跑 280 cm/s，慢走 140 cm/s。锁定时仍可朝移动方向冲刺；战斗中移动冲刺每秒消耗 12 点体力，耗尽后需松开再按，探索时不额外消耗。松开长按不触发翻滚。

追加 `hero_sprint` 实机用例通过：点按只滚一次、长按达到冲刺速度、冲刺接跳跃、长按松开无误滚、锁定冲刺、体力耗尽后不自动反复起跑。追加跳跃及闪避重砸回归也通过，证据见 `Saved/HeroComplete/sprint-tests.log`。

后续跳跃修正见 [跳跃分段 v03](jump-phases-v03.md)。
